"""Arquivo principal de rotas do projeto."""

from django.contrib import admin
from django.urls import include, path

from accounts.views import home_redirect

urlpatterns = [
    # Rota raiz decide se vai para login ou boas-vindas.
    path("", home_redirect, name="home_redirect"),
    # Rotas administrativas do Django.
    path("admin/", admin.site.urls),
    # Rotas do modulo de contas (template e CSS proprios).
    path("accounts/", include(("accounts.urls", "accounts"), namespace="accounts")),
    # Rotas do modulo de boas-vindas (template e CSS proprios).
    path("welcome/", include("welcome.urls")),
]
