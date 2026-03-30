"""Rotas do app accounts."""

from django.urls import path

from .views import CustomLoginView, logout_view, signup_view

app_name = "accounts"

urlpatterns = [
    # Tela de login principal do sistema.
    path("login/", CustomLoginView.as_view(), name="login"),
    # Tela de cadastro de novo usuario local.
    path("signup/", signup_view, name="signup"),
    # Logout via GET para manter fluxo simples por link.
    path("logout/", logout_view, name="logout"),
]
