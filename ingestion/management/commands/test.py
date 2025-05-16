import datetime

from dateutil.relativedelta import relativedelta
from django.core.management.base import BaseCommand
from django.db.models import Q

from core.models import Company, FinancialStatement


class Command(BaseCommand):
    help = "Sync financial statements for all companies"

    def handle(self, *args, **options):
        # embeddings = MistralAIEmbeddings(
        #     model="mistral-embed",
        # )

        # text = "LangChain is the framework for building context-aware reasoning applications"

        # vectorstore = InMemoryVectorStore.from_texts(
        #     texts=["Hello world", "The world is flat", "The world is great"],
        #     embedding=embeddings,
        # )
        # database.save(vectorstore.embeddings) # just an example

        # retriever = vectorstore.as_retriever()

        # retrieved_documents = retriever.invoke("How is the world?")

        # # vectorstore.add_texts(["Hello world"])
        # fetch_financial_report([(140059, "VHCOX")])

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

        sentences = []
        for company_id, financial_statements in statements_by_company.items():
            sentences.append(
                {
                    "company_id": company_id,
                    "sentences": [
                        generate_sentence(statement)
                        for statement in financial_statements
                    ],
                }
            )

        chunk_size = 20
        chunks = [
            sentences[index : index + chunk_size]
            for index in range(0, len(sentences), chunk_size)
        ]

        QUEUE = Queues.FETCH_FINANCIAL_REPORT

        for chunk in chunks:
            fetch_financial_report.apply_async(
                args=[chunk],
                queue=QUEUE,
            )
            logger.info(f"Queued {len(chunk)} companies to {QUEUE}.")
