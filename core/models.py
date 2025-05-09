from django.db import models


class Company(models.Model):
    name = models.CharField(max_length=255)
    symbol = models.CharField(max_length=10, unique=True)
    cik = models.CharField(max_length=10, unique=True)

    image = models.URLField(blank=True, null=True)

    sector = models.CharField(max_length=100, blank=True, null=True)
    industry = models.CharField(max_length=100, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    ipo_date = models.DateField(blank=True, null=True)
