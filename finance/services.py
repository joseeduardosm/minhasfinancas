"""Servicos de agregacao mensal para dashboard e calendario financeiro."""

from __future__ import annotations

from calendar import monthrange
from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal

from .models import Transacao


@dataclass(frozen=True)
class MesReferencia:
    """Representa a faixa de datas de um mes especifico."""

    year: int
    month: int
    inicio: date
    fim: date
    dias_no_mes: int


def resolver_mes_referencia(year: int, month: int) -> MesReferencia:
    """Normaliza ano/mes e retorna o intervalo completo do mes."""
    year = max(1900, min(2100, int(year)))
    month = max(1, min(12, int(month)))
    dias_no_mes = monthrange(year, month)[1]
    inicio = date(year, month, 1)
    fim = date(year, month, dias_no_mes)
    return MesReferencia(year=year, month=month, inicio=inicio, fim=fim, dias_no_mes=dias_no_mes)


def mes_anterior(year: int, month: int) -> tuple[int, int]:
    """Retorna o par ano/mes imediatamente anterior."""
    if month == 1:
        return year - 1, 12
    return year, month - 1


def mes_posterior(year: int, month: int) -> tuple[int, int]:
    """Retorna o par ano/mes imediatamente seguinte."""
    if month == 12:
        return year + 1, 1
    return year, month + 1


def _add_months(base: date, months: int) -> date:
    """Avanca datas por meses preservando o dia quando possivel."""
    month_index = base.month - 1 + months
    new_year = base.year + month_index // 12
    new_month = month_index % 12 + 1
    new_day = min(base.day, monthrange(new_year, new_month)[1])
    return date(new_year, new_month, new_day)


def _iterar_ocorrencias(transacao: Transacao, inicio: date, fim: date):
    """Gera ocorrencias da transacao dentro da faixa mensal informada."""
    fim_recorrencia = transacao.data_fim_recorrencia or fim
    fim_consulta = min(fim, fim_recorrencia)
    atual = transacao.data_base
    if atual > fim_consulta:
        return

    recorrencia = transacao.recorrencia

    if recorrencia == Transacao.Recorrencia.DIARIA:
        passo = timedelta(days=1)
        while atual < inicio:
            atual += passo
        while atual <= fim_consulta:
            yield atual
            atual += passo
        return

    if recorrencia == Transacao.Recorrencia.SEMANAL:
        passo = timedelta(days=7)
        while atual < inicio:
            atual += passo
        while atual <= fim_consulta:
            yield atual
            atual += passo
        return

    if recorrencia == Transacao.Recorrencia.QUINZENAL:
        passo = timedelta(days=14)
        while atual < inicio:
            atual += passo
        while atual <= fim_consulta:
            yield atual
            atual += passo
        return

    meses_por_passo = {
        Transacao.Recorrencia.MENSAL: 1,
        Transacao.Recorrencia.TRIMESTRAL: 3,
        Transacao.Recorrencia.SEMESTRAL: 6,
        Transacao.Recorrencia.ANUAL: 12,
    }[recorrencia]

    while atual < inicio:
        atual = _add_months(atual, meses_por_passo)

    while atual <= fim_consulta:
        yield atual
        atual = _add_months(atual, meses_por_passo)


def _formatar_brl(valor: Decimal) -> str:
    """Formata valor decimal no padrao monetario BRL."""
    sinal = "-" if valor < 0 else ""
    bruto = f"{abs(valor):,.2f}"
    # Troca separadores para formato brasileiro.
    return f"{sinal}R$ {bruto}".replace(",", "X").replace(".", ",").replace("X", ".")


def _valor_assinado(transacao: Transacao) -> Decimal:
    """Converte valor para sinal financeiro, por tipo de transacao."""
    if transacao.tipo == Transacao.Tipo.RECEITA:
        return transacao.valor
    return -transacao.valor


def gerar_dados_mensais(usuario, year: int, month: int) -> dict:
    """Monta payload mensal para grafico, saldo e calendario."""
    mes = resolver_mes_referencia(year, month)

    transacoes = (
        Transacao.objects.filter(
            usuario=usuario,
            ativo=True,
            data_base__lte=mes.fim,
        )
        .prefetch_related("excecoes")
        .order_by("data_base", "nome")
    )

    eventos = []
    receitas_por_dia = [Decimal("0") for _ in range(mes.dias_no_mes)]
    despesas_por_dia = [Decimal("0") for _ in range(mes.dias_no_mes)]
    saldo_planejado = Decimal("0")
    saldo_executado = Decimal("0")
    receitas_planejadas = Decimal("0")
    receitas_executadas = Decimal("0")
    despesas_planejadas = Decimal("0")
    despesas_executadas = Decimal("0")

    for transacao in transacoes:
        datas_excluidas = {excecao.data for excecao in transacao.excecoes.all()}
        for ocorrencia in _iterar_ocorrencias(transacao, mes.inicio, mes.fim):
            if ocorrencia in datas_excluidas:
                continue
            valor_assinado = _valor_assinado(transacao)
            indice = ocorrencia.day - 1
            if transacao.tipo == Transacao.Tipo.RECEITA:
                receitas_por_dia[indice] += transacao.valor
            else:
                despesas_por_dia[indice] += transacao.valor

            if transacao.status == Transacao.Status.PLANEJADO:
                saldo_planejado += valor_assinado
                if transacao.tipo == Transacao.Tipo.RECEITA:
                    receitas_planejadas += transacao.valor
                else:
                    despesas_planejadas += transacao.valor
            else:
                saldo_executado += valor_assinado
                if transacao.tipo == Transacao.Tipo.RECEITA:
                    receitas_executadas += transacao.valor
                else:
                    despesas_executadas += transacao.valor

            prefixo = "+" if transacao.tipo == Transacao.Tipo.RECEITA else "-"
            label_tooltip = f"({prefixo}) {transacao.nome} - {_formatar_brl(transacao.valor)}"

            eventos.append(
                {
                    "id": transacao.id,
                    "data": ocorrencia.isoformat(),
                    "nome": transacao.nome,
                    "valor": float(transacao.valor),
                    "tipo": transacao.tipo,
                    "status": transacao.status,
                    "is_recorrente": bool(
                        transacao.data_fim_recorrencia
                        and transacao.data_fim_recorrencia > transacao.data_base
                    ),
                    "label_tooltip": label_tooltip,
                }
            )

    etiquetas_dias = [f"{dia:02d}/{mes.month:02d}" for dia in range(1, mes.dias_no_mes + 1)]

    eventos_por_dia = {}
    for evento in eventos:
        eventos_por_dia.setdefault(evento["data"], []).append(evento)

    return {
        "year": mes.year,
        "month": mes.month,
        "dias_no_mes": mes.dias_no_mes,
        "labels": etiquetas_dias,
        "series": {
            "receitas": [float(valor) for valor in receitas_por_dia],
            "despesas": [float(valor) for valor in despesas_por_dia],
        },
        "saldo": {
            "planejado": float(saldo_planejado),
            "executado": float(saldo_executado),
            "planejado_brl": _formatar_brl(saldo_planejado),
            "executado_brl": _formatar_brl(saldo_executado),
        },
        "resumo_tipos": {
            "receitas": {
                "planejada": float(receitas_planejadas),
                "executada": float(receitas_executadas),
                "planejada_brl": _formatar_brl(receitas_planejadas),
                "executada_brl": _formatar_brl(receitas_executadas),
            },
            "despesas": {
                "planejada": float(despesas_planejadas),
                "executada": float(despesas_executadas),
                "planejada_brl": _formatar_brl(despesas_planejadas),
                "executada_brl": _formatar_brl(despesas_executadas),
            },
        },
        "eventos": eventos,
        "eventos_por_dia": eventos_por_dia,
    }
