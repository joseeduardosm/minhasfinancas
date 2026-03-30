"""Testes de recorrencia e validacao financeira."""

from datetime import date
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase

from .models import Transacao
from .services import gerar_dados_mensais


class TransacaoModelTests(TestCase):
    """Valida regras de modelo e agregacao mensal."""

    def setUp(self):
        """Cria usuario base para os testes."""
        self.user = get_user_model().objects.create_user("tester", password="SenhaForte123!")

    def test_nao_permite_valor_negativo_ou_zero(self):
        """Valor deve ser sempre maior que zero."""
        transacao = Transacao(
            usuario=self.user,
            tipo=Transacao.Tipo.RECEITA,
            status=Transacao.Status.EXECUTADO,
            nome="Invalida",
            valor=Decimal("0"),
            data_base=date(2026, 3, 1),
            data_fim_recorrencia=date(2026, 3, 31),
            recorrencia=Transacao.Recorrencia.MENSAL,
        )
        with self.assertRaises(ValidationError):
            transacao.full_clean()

    def test_agrega_series_com_recorrencias(self):
        """Gera recorrencias e soma corretamente receitas e despesas do mes."""
        Transacao.objects.create(
            usuario=self.user,
            tipo=Transacao.Tipo.RECEITA,
            status=Transacao.Status.EXECUTADO,
            nome="Salario",
            valor=Decimal("1000.00"),
            data_base=date(2026, 3, 5),
            data_fim_recorrencia=date(2026, 12, 31),
            recorrencia=Transacao.Recorrencia.MENSAL,
        )
        Transacao.objects.create(
            usuario=self.user,
            tipo=Transacao.Tipo.DESPESA,
            status=Transacao.Status.PLANEJADO,
            nome="Cafe",
            valor=Decimal("10.00"),
            data_base=date(2026, 3, 1),
            data_fim_recorrencia=date(2026, 3, 31),
            recorrencia=Transacao.Recorrencia.DIARIA,
        )

        dados = gerar_dados_mensais(self.user, 2026, 3)

        self.assertEqual(dados["series"]["receitas"][4], 1000.0)
        self.assertEqual(dados["series"]["despesas"][0], 10.0)
        self.assertEqual(len(dados["eventos_por_dia"]["2026-03-01"]), 1)
        self.assertTrue(dados["saldo"]["planejado"] < 0)
        self.assertTrue(dados["saldo"]["executado"] > 0)
