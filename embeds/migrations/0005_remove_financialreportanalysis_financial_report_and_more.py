# Generated by Django 5.2.1 on 2025-05-16 14:59

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0009_enable_pgvector"),
        ("embeds", "0004_alter_financialreportanalysis_financial_report"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="financialreportanalysis",
            name="financial_report",
        ),
        migrations.AddField(
            model_name="financialreportanalysis",
            name="financial_statement",
            field=models.OneToOneField(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="financial_statement_analysis",
                to="core.financialstatement",
            ),
        ),
    ]
