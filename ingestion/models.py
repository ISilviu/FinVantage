from django.db import models


class ApiUsage(models.Model):
    date = models.DateField(unique=True)
    limit_reached = models.BooleanField(default=False)
