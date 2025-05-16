from django.db import models
from langchain_mistralai import MistralAIEmbeddings
from pgvector.django import VectorField

from core.models import FinancialStatement


class LlmModel:
    class MistralAI:
        embedding_model = MistralAIEmbeddings
        model_name = "mistral-embed"
        embedding_length = 1024


CURRENT_MODEL = LlmModel.MistralAI


class FinancialStatementAnalysis(models.Model):
    financial_statement = models.OneToOneField(
        FinancialStatement,
        on_delete=models.CASCADE,
        related_name="financial_statement_analysis",
    )
    analysis_text = models.TextField(
        help_text="The generated analysis text that was embedded.",
        blank=True,
        null=True,
    )
    embedding = VectorField(
        max_length=CURRENT_MODEL.embedding_length,
        null=True,
        blank=True,
        help_text="Vector representation of the analysis text.",
    )
    last_modified = models.DateField(auto_now=True, null=True, blank=True)
