import os

from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "fin_vantage.settings")

app = Celery("fin_vantage")

app.config_from_object("django.conf:settings", namespace="CELERY")

app.autodiscover_tasks()