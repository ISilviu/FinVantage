import datetime
import logging

from celery import shared_task
from dateutil.relativedelta import relativedelta
from django.db.models import Q

from core.models import Company, FinancialStatement
from queues import Queues


@shared_task
def build_financial_embeddings(sentences):
    pass


@shared_task
def generate_financial_sentences():
    logger = logging.getLogger("generate_financial_sentences")

    logger.info("Starting generate_financial_sentences task ...")

    # fetch all the financial statements that don't have embeddings or have embeddings older than 1 year
    one_year_ago = datetime.date.today() - relativedelta(years=1)

    companies = (
        Company.objects.prefetch_related("financial_statements")
        .filter(
            Q(financial_statements__isnull=False)
            & (
                Q(financial_statements__financial_report_analysis__isnull=True)
                | Q(
                    financial_statements__financial_report_analysis__last_modified__lt=one_year_ago
                )
            )
        )
        .distinct()
    )

    statements_by_company = {
        company.id: list(company.financial_statements.order_by("-calendar_year"))
        for company in companies
    }

    def generate_sentence(statement: FinancialStatement) -> str:
        return " ".join(
            [
                f"The company {statement.company.name}, with the symbol {statement.company.symbol}, for the year {statement.calendar_year}, has a total revenue of {statement.revenue}.",
                f"The net income is {statement.net_income}, the gross profit is {statement.gross_profit}, and the operating income is {statement.operating_income}.",
                f"The income before tax is {statement.income_before_tax}, the operating expenses are {statement.operating_expenses}, and the research and development expenses are {statement.research_and_development_expenses}.",
                f"The financial statement was reported on {statement.date_reported} and the reported period is {statement.period}.",
            ]
        )

    sentences = [
        {
            "company_id": company_id,
            "sentences": [
                generate_sentence(statement) for statement in financial_statements
            ],
        }
        for company_id, financial_statements in statements_by_company.items()
    ]

    logger.info(f"Generated sentences for {len(sentences)} companies.")

    chunk_size = 20
    chunks = [
        sentences[index : index + chunk_size]
        for index in range(0, len(sentences), chunk_size)
    ]

    QUEUE = Queues.FINANCIAL_SENTENCES

    for chunk in chunks:
        build_financial_embeddings.apply_async(
            args=[chunk],
            queue=QUEUE,
        )
        logger.info(f"Queued {len(chunk)} companies to {QUEUE}.")
