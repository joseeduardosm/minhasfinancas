"""Configuracoes globais do projeto Django."""

import os
import sys
from pathlib import Path

from dotenv import load_dotenv

# Caminho base do projeto.
BASE_DIR = Path(__file__).resolve().parent.parent

# Carrega variaveis do arquivo .env para facilitar configuracao por ambiente.
load_dotenv(BASE_DIR / ".env")

# Chave secreta lida do ambiente (com fallback apenas para desenvolvimento local).
SECRET_KEY = os.getenv(
    "DJANGO_SECRET_KEY",
    "django-insecure-dev-only-change-this-key-in-production",
)

# Ativa modo debug por padrao localmente.
DEBUG = os.getenv("DJANGO_DEBUG", "True").lower() == "true"

# Hosts permitidos para acessar a aplicacao.
ALLOWED_HOSTS = [
    host.strip()
    for host in os.getenv("DJANGO_ALLOWED_HOSTS", "127.0.0.1,localhost,testserver").split(",")
    if host.strip()
]

# Aplicacoes instaladas no projeto.
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "accounts",
    "finance",
    "welcome",
]

# Middlewares usados no ciclo de requisicao/resposta.
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    # WhiteNoise permite servir arquivos estaticos via Gunicorn.
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

# Configuracao de templates. Cada app usa seus proprios templates.
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

# Banco de dados MySQL para o projeto de financas pessoais.
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.mysql",
        "NAME": os.getenv("MYSQL_DATABASE", "minhasfinancas"),
        "USER": os.getenv("MYSQL_USER", "minhasfinancas_user"),
        "PASSWORD": os.getenv("MYSQL_PASSWORD", ""),
        "HOST": os.getenv("MYSQL_HOST", "127.0.0.1"),
        "PORT": os.getenv("MYSQL_PORT", "3306"),
        "OPTIONS": {
            "charset": "utf8mb4",
        },
    }
}

# Validadores padrao de senha do Django.
AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

# Idioma e fuso do projeto.
LANGUAGE_CODE = "pt-br"
TIME_ZONE = "America/Sao_Paulo"
USE_I18N = True
USE_TZ = True

# Configuracao de arquivos estaticos.
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
# Mantem os arquivos estaticos comprimidos e versionados.
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"},
}

# Em testes, usa storage simples para nao depender de manifesto coletado.
if "test" in sys.argv:
    STORAGES["staticfiles"] = {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"}

# Tipo de chave primaria padrao para novos modelos.
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Configuracoes de autenticacao local do sistema.
LOGIN_URL = "/accounts/login/"
LOGIN_REDIRECT_URL = "/welcome/"
LOGOUT_REDIRECT_URL = "/accounts/login/"
