import datetime
import logging
from decimal import Decimal

import requests
from celery import shared_task
from dateutil.relativedelta import relativedelta
from django.conf import settings
from django.db import transaction
from django.db.models import Q
from tenacity import (
    after_log,
    before_log,
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from core.models import Company, CompanyDataTracker, Currency, FinancialStatement
from ingestion.models import ApiUsage
from ingestion.queues import Queues


@shared_task
def sync_companies():
    logger = logging.getLogger("sync_companies")

    logger.info("Starting sync_companies task ...")

    today = datetime.date.today()
    today_api_usage, created = ApiUsage.objects.get_or_create(date=today)

    if not created and today_api_usage.limit_reached:
        logger.info("API limit reached for today. Skipping sync.")
        return

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type(requests.exceptions.RequestException),
        before=before_log(logger, logging.DEBUG),
        after=after_log(logger, logging.DEBUG),
    )
    def get_companies_list():
        response = requests.get(
            f"{settings.FINANCIAL_DATA_API_URL}/v3/stock/list",
            params={"apikey": settings.FINANCIAL_DATA_API_KEY},
        )
        response.raise_for_status()
        return response

    try:
        companies_list = get_companies_list().json()
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 429:
            logger.info("API limit reached. Marking today's usage as limit reached.")
            today_api_usage.limit_reached = True
            today_api_usage.save()
            return
    except Exception as e:
        logger.error(f"Error fetching companies list: {e}. Stopping ...")
        return

    companies = [
        Company(name=company.get("name"), symbol=company.get("symbol"))
        for company in companies_list
        if company.get("exchangeShortName", "") in settings.STOCK_EXCHANGES
    ]

    count_before = Company.objects.count()

    with transaction.atomic():
        Company.objects.bulk_create(companies, batch_size=1000, ignore_conflicts=True)

        companies_without_tracking = Company.objects.filter(
            symbol__in=[company.symbol for company in companies],
            data_tracker__isnull=True,
        ).values_list("id", flat=True)

        CompanyDataTracker.objects.bulk_create(
            [
                CompanyDataTracker(company_id=company_id)
                for company_id in companies_without_tracking
            ],
            batch_size=1000,
        )

    count_after = Company.objects.count()

    if count_after > count_before:
        logger.info(f"Inserted {count_after - count_before} new companies.")
    else:
        logger.info("No new companies were inserted.")


@shared_task
def fetch_financial_report(companies):
    logger = logging.getLogger("fetch_financial_report")
    currencies = {currency.code: currency for currency in Currency.objects.all()}

    logger.info("Starting sync_financial_statements task ...")

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type(requests.exceptions.RequestException),
        before=before_log(logger, logging.DEBUG),
        after=after_log(logger, logging.DEBUG),
    )
    def get_financial_statements_for_company(symbol: str):
        response = requests.get(
            f"{settings.FINANCIAL_DATA_API_URL}/v3/income-statement/{symbol}",
            params={"period": "annual", "apikey": settings.FINANCIAL_DATA_API_KEY},
        )
        response.raise_for_status()
        return response

    financial_statements = []
    for company_id, symbol in companies:
        # fetch statement
        company_statements = get_financial_statements_for_company(symbol).json()
        for statement_data in company_statements:
            currency = currencies.get(statement_data.get("reportedCurrency"))
            statement_date = statement_data.get("date")
            if not currency:
                logger.warning(
                    f"Statement with date {statement_date} for symbol {symbol} was omitted. It lacks a mentioned currency."
                )
                continue

            financial_statements.append(
                FinancialStatement(
                    company_id=company_id,
                    date_reported=statement_date,
                    calendar_year=int(statement_data.get("calendarYear")),
                    period=statement_data.get("period"),
                    currency=currency,
                    revenue=Decimal(str(statement_data.get("revenue"))),
                    net_income=Decimal(str(statement_data.get("netIncome"))),
                    gross_profit=Decimal(str(statement_data.get("grossProfit"))),
                    operating_income=Decimal(
                        str(statement_data.get("operatingIncome"))
                    ),
                    income_before_tax=Decimal(
                        str(statement_data.get("incomeBeforeTax"))
                    ),
                    operating_expenses=Decimal(
                        str(statement_data.get("operatingExpenses"))
                    ),
                    research_and_development_expenses=Decimal(
                        str(statement_data.get("researchAndDevelopmentExpenses", 0))
                    ),
                )
            )

    today = datetime.datetime.now().date()
    with transaction.atomic():
        FinancialStatement.objects.bulk_create(financial_statements, batch_size=1000)
        CompanyDataTracker.objects.filter(
            company_id__in=[company_id for company_id, _ in companies]
        ).update(last_financial_report_fetch=today)

    logger.info(
        f"Successfully inserted {len(financial_statements)} financial statements."
    )


@shared_task
def sync_financial_statements():
    logger = logging.getLogger("sync_financial_statements")

    logger.info("Starting sync_financial_statements task ...")

    today = datetime.date.today()
    today_api_usage, created = ApiUsage.objects.get_or_create(date=today)

    if not created and today_api_usage.limit_reached:
        logger.info("API limit reached for today. Skipping sync.")
        return

    # fetch the data for all the companies that have never had their financial statement fetched
    # or for those that have it fetched 1 year ago
    one_year_ago = datetime.date.today() - relativedelta(years=1)
    companies_to_fetch = list(
        CompanyDataTracker.objects.filter(
            Q(last_financial_report_fetch__isnull=True)
            | Q(last_financial_report_fetch__lt=one_year_ago)
        )
        .select_related("company")
        .values_list("company_id", "company__symbol")
    )

    chunk_size = 20
    chunks = [
        companies_to_fetch[index : index + chunk_size]
        for index in range(0, len(companies_to_fetch), chunk_size)
    ]

    QUEUE = Queues.FETCH_FINANCIAL_REPORT

    for chunk in chunks:
        fetch_financial_report.apply_async(
            args=[chunk],
            queue=QUEUE,
        )
        logger.info(f"Queued {len(chunk)} companies to {QUEUE}.")
