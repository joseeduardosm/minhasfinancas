"""Configuracao do app financeiro."""

from django.apps import AppConfig


class FinanceConfig(AppConfig):
    """Classe de configuracao do modulo financeiro."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "finance"
