# urls.py
from django.urls import path

from . import views

urlpatterns = [
    path("ask/", views.financial_query, name="financial_query"),
]
