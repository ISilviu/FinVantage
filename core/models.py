from django.db import models


class Company(models.Model):
    name = models.CharField(max_length=255)
    symbol = models.CharField(max_length=10, unique=True)
    cik = models.CharField(max_length=10, unique=True, blank=True, null=True)

    image = models.URLField(blank=True, null=True)

    sector = models.CharField(max_length=100, blank=True, null=True)
    industry = models.CharField(max_length=100, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    ipo_date = models.DateField(blank=True, null=True)


class Currency(models.Model):
    code = models.CharField(max_length=3, unique=True)
    name = models.CharField(max_length=50)
    symbol = models.CharField(max_length=10)


class FinancialStatement(models.Model):
    company = models.ForeignKey(
        Company, on_delete=models.CASCADE, related_name="financial_statements"
    )

    date_reported = models.DateField()
    calendar_year = models.IntegerField()
    period = models.CharField(
        max_length=10, db_comment='For example: "Q1", "Q2", "Q3", "Q4", "FY"'
    )

    currency = models.ForeignKey(Currency, on_delete=models.CASCADE)

    revenue = models.DecimalField(max_digits=20, decimal_places=2)
    net_income = models.DecimalField(max_digits=20, decimal_places=2)
    gross_profit = models.DecimalField(max_digits=20, decimal_places=2)
    operating_income = models.DecimalField(max_digits=20, decimal_places=2)
    income_before_tax = models.DecimalField(max_digits=20, decimal_places=2)
    operating_expenses = models.DecimalField(max_digits=20, decimal_places=2)
    cash_and_equivalents = models.DecimalField(max_digits=20, decimal_places=2)
    research_and_development_expenses = models.DecimalField(
        max_digits=20, decimal_places=2
    )

    class Meta:
        unique_together = (
            "company",
            "date_reported",
            "calendar_year",
            "period",
            "currency",
        )
