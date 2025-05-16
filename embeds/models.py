from django.db import models
from pgvector.django import VectorField

from core.models import FinancialStatement


class LlmModel:
    class MistralAI:
        embedding_model = "mistral-ai/mistral-7b-v0.1"
        embedding_length = 1024


CURRENT_MODEL = LlmModel.MistralAI


class FinancialReportAnalysis(models.Model):
    financial_report = models.ForeignKey(
        FinancialStatement,
        on_delete=models.CASCADE,
        related_name="financial_report_analysis",
    )
    embedding = VectorField(
        max_length=CURRENT_MODEL.embedding_length,
        null=True,
        blank=True,
        db_index=True,
        help_text="Vector representation of the analysis text.",
    )
