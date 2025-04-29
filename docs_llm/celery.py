import os

from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "docs_llm.settings")

app = Celery("docs_llm")

app.config_from_object("django.conf:settings", namespace="CELERY")

app.autodiscover_tasks()
