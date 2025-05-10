import datetime
import logging

import requests
from celery import shared_task
from django.conf import settings
from tenacity import (
    after_log,
    before_log,
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from core.models import Company
from ingestion.models import ApiUsage

logger = logging.getLogger("sync_companies")


@shared_task
def sync_companies():
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
    Company.objects.bulk_create(companies, batch_size=1000, ignore_conflicts=True)
    count_after = Company.objects.count()

    if count_after > count_before:
        logger.info(f"Inserted {count_after - count_before} new companies.")
    else:
        logger.info("No new companies were inserted.")
