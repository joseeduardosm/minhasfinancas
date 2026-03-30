"""Configuração do app welcome."""

from django.apps import AppConfig


class WelcomeConfig(AppConfig):
    """Classe de configuração do app pós-login."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "welcome"
