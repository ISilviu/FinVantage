# Generated by Django 5.2.1 on 2025-05-09 15:39

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0004_financialstatement'),
    ]

    operations = [
        migrations.AlterField(
            model_name='company',
            name='cik',
            field=models.CharField(blank=True, max_length=10, null=True, unique=True),
        ),
        migrations.AlterField(
            model_name='financialstatement',
            name='company',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='financial_statements', to='core.company'),
        ),
        migrations.AlterUniqueTogether(
            name='financialstatement',
            unique_together={('company', 'date_reported', 'calendar_year', 'period', 'currency')},
        ),
    ]
