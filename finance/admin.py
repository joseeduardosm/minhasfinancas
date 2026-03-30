"""Configuracoes administrativas do modulo financeiro."""

from django.contrib import admin

from .models import Transacao, TransacaoExcecao


@admin.register(Transacao)
class TransacaoAdmin(admin.ModelAdmin):
    """Admin para cadastro de receitas e despesas financeiras."""

    list_display = (
        "nome",
        "usuario",
        "tipo",
        "status",
        "valor",
        "data_base",
        "data_fim_recorrencia",
        "recorrencia",
        "ativo",
    )
    list_filter = ("usuario", "tipo", "status", "recorrencia", "ativo", "data_base")
    search_fields = ("nome", "usuario__username")
    ordering = ("data_base", "tipo", "nome")


@admin.register(TransacaoExcecao)
class TransacaoExcecaoAdmin(admin.ModelAdmin):
    """Admin de dias excluidos de recorrencias financeiras."""

    list_display = ("transacao", "data", "created_at")
    list_filter = ("data",)
    search_fields = ("transacao__nome", "transacao__usuario__username")
    ordering = ("-data",)
