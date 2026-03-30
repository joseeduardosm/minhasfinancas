"""Rotas do app welcome."""

from django.urls import path

from .views import (
    api_mes,
    calendario,
    editar_transacao,
    executar_transacao,
    excluir_transacao,
    home,
    listar_eventos_tipo,
    lancar_transacao,
)

app_name = "welcome"

urlpatterns = [
    # Dashboard mensal com grafico e resumo financeiro.
    path("", home, name="home"),
    # Calendario mensal de receitas e despesas.
    path("calendario/", calendario, name="calendar"),
    # API mensal para consumo de visualizacoes no frontend.
    path("api/mes/", api_mes, name="api_month"),
    # Listagem mensal por tipo com ordenacao e busca.
    path("eventos/<str:tipo_slug>/", listar_eventos_tipo, name="event_list"),
    # Endpoint de criacao de lancamentos via dashboard.
    path("lancamento/", lancar_transacao, name="create_entry"),
    # Acao rapida para marcar lancamento como executado.
    path("lancamento/<int:transacao_id>/executar/", executar_transacao, name="execute_entry"),
    # Tela de edicao de lancamento.
    path("lancamento/<int:transacao_id>/editar/", editar_transacao, name="edit_entry"),
    # Exclusao (inativacao) de lancamento.
    path("lancamento/<int:transacao_id>/excluir/", excluir_transacao, name="delete_entry"),
]
