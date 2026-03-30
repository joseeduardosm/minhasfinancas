"""Configuração do app accounts."""

from django.apps import AppConfig


class AccountsConfig(AppConfig):
    """Classe de configuração do app de autenticação."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "accounts"
