"""Testes do app welcome para dashboard, calendario e API mensal."""

from datetime import date
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from finance.models import Transacao


class WelcomeViewsTests(TestCase):
    """Valida acesso autenticado e payloads basicos do painel mensal."""

    def setUp(self):
        """Cria usuario e transacoes para os cenarios de teste."""
        self.user = get_user_model().objects.create_user("welcome_user", password="SenhaForte123!")
        Transacao.objects.create(
            usuario=self.user,
            tipo=Transacao.Tipo.RECEITA,
            status=Transacao.Status.EXECUTADO,
            nome="Salario",
            valor=Decimal("2000.00"),
            data_base=date(2026, 3, 5),
            data_fim_recorrencia=date(2026, 12, 31),
            recorrencia=Transacao.Recorrencia.MENSAL,
        )

    def test_dashboard_requer_login(self):
        """Sem autenticacao, dashboard deve redirecionar para login."""
        response = self.client.get(reverse("welcome:home"))
        self.assertEqual(response.status_code, 302)
        self.assertIn("/accounts/login/", response["Location"])

    def test_dashboard_autenticada_carrega(self):
        """Usuario autenticado acessa dashboard com sucesso."""
        self.client.login(username="welcome_user", password="SenhaForte123!")
        response = self.client.get(reverse("welcome:home"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Dashboard Financeira Mensal")
        self.assertContains(response, "/welcome/eventos/receita/")
        self.assertContains(response, "/welcome/eventos/despesa/")

    def test_api_mes_retorna_payload(self):
        """Endpoint mensal devolve dados esperados para frontend."""
        self.client.login(username="welcome_user", password="SenhaForte123!")
        response = self.client.get(reverse("welcome:api_month"), {"year": 2026, "month": 3})
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["year"], 2026)
        self.assertEqual(payload["month"], 3)
        self.assertIn("series", payload)
        self.assertIn("eventos", payload)
        self.assertIn("resumo_tipos", payload)
        self.assertIn("id", payload["eventos"][0])

    def test_listagem_eventos_por_tipo_com_busca(self):
        """Listagem mensal deve filtrar por tipo e aplicar busca em todo o queryset do mes."""
        self.client.login(username="welcome_user", password="SenhaForte123!")
        Transacao.objects.create(
            usuario=self.user,
            tipo=Transacao.Tipo.DESPESA,
            status=Transacao.Status.PLANEJADO,
            nome="Internet Fibra",
            valor=Decimal("149.90"),
            data_base=date(2026, 3, 10),
            data_fim_recorrencia=date(2026, 12, 31),
            recorrencia=Transacao.Recorrencia.MENSAL,
        )
        response = self.client.get(
            reverse("welcome:event_list", kwargs={"tipo_slug": "despesa"}),
            {"year": 2026, "month": 3, "q": "Internet", "sort": "nome", "dir": "asc"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Internet Fibra")
        self.assertNotContains(response, "Salario")

    def test_cria_lancamento_via_dashboard(self):
        """Clique em bloco lateral envia formulario e cria transacao do tipo correto."""
        self.client.login(username="welcome_user", password="SenhaForte123!")
        response = self.client.post(
            reverse("welcome:create_entry"),
            {
                "tipo": "DESPESA",
                "nome": "Internet",
                "valor": "120.00",
                "data_base": "2026-03-10",
                "data_fim_recorrencia": "2026-12-31",
                "status": "PLANEJADO",
                "recorrencia": "MENSAL",
                "year": "2026",
                "month": "3",
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response["Location"], "/welcome/?year=2026&month=3")
        self.assertTrue(
            Transacao.objects.filter(
                usuario=self.user, nome="Internet", tipo=Transacao.Tipo.DESPESA
            ).exists()
        )
        transacao = Transacao.objects.get(usuario=self.user, nome="Internet")
        self.assertEqual(transacao.data_fim_recorrencia, transacao.data_base)

    def test_redireciona_para_mes_do_lancamento_quando_data_diferente(self):
        """Ao salvar em outro mes, a dashboard deve abrir no mes da data base."""
        self.client.login(username="welcome_user", password="SenhaForte123!")
        response = self.client.post(
            reverse("welcome:create_entry"),
            {
                "tipo": "RECEITA",
                "nome": "Freelance",
                "valor": "350.00",
                "data_base": "2026-04-08",
                "data_fim_recorrencia": "2026-12-31",
                "status": "EXECUTADO",
                "recorrencia": "MENSAL",
                "year": "2026",
                "month": "3",
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response["Location"], "/welcome/?year=2026&month=4")

    def test_executar_transacao_via_acao_do_calendario(self):
        """Acao de executar deve atualizar status e voltar ao calendario."""
        self.client.login(username="welcome_user", password="SenhaForte123!")
        transacao = Transacao.objects.create(
            usuario=self.user,
            tipo=Transacao.Tipo.DESPESA,
            status=Transacao.Status.PLANEJADO,
            nome="Conta de Luz",
            valor=Decimal("180.00"),
            data_base=date(2026, 3, 12),
            data_fim_recorrencia=date(2026, 12, 31),
            recorrencia=Transacao.Recorrencia.MENSAL,
        )
        response = self.client.post(
            reverse("welcome:execute_entry", kwargs={"transacao_id": transacao.id}),
            {"year": "2026", "month": "3", "day": "12", "next": "/welcome/eventos/despesa/?year=2026&month=3"},
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response["Location"], "/welcome/eventos/despesa/?year=2026&month=3")
        transacao.refresh_from_db()
        self.assertEqual(transacao.status, Transacao.Status.EXECUTADO)

    def test_editar_transacao_atualiza_campos(self):
        """Tela de edicao deve persistir os novos dados do lancamento."""
        self.client.login(username="welcome_user", password="SenhaForte123!")
        transacao = Transacao.objects.create(
            usuario=self.user,
            tipo=Transacao.Tipo.RECEITA,
            status=Transacao.Status.PLANEJADO,
            nome="Bonus",
            valor=Decimal("500.00"),
            data_base=date(2026, 3, 20),
            data_fim_recorrencia=date(2026, 12, 31),
            recorrencia=Transacao.Recorrencia.MENSAL,
        )
        response = self.client.post(
            reverse("welcome:edit_entry", kwargs={"transacao_id": transacao.id}),
            {
                "tipo": "RECEITA",
                "nome": "Bonus Atualizado",
                "valor": "750.00",
                "data_base": "2026-03-22",
                "data_fim_recorrencia": "2026-12-31",
                "is_recorrente": "1",
                "status": "EXECUTADO",
                "recorrencia": "ANUAL",
                "year": "2026",
                "month": "3",
                "day": "22",
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response["Location"], "/welcome/calendario/?year=2026&month=3&day=22")
        transacao.refresh_from_db()
        self.assertEqual(transacao.nome, "Bonus Atualizado")
        self.assertEqual(transacao.status, Transacao.Status.EXECUTADO)
        self.assertEqual(transacao.recorrencia, Transacao.Recorrencia.ANUAL)

    def test_excluir_transacao_inativa_registro(self):
        """Botao excluir deve inativar transacao e retornar ao calendario."""
        self.client.login(username="welcome_user", password="SenhaForte123!")
        transacao = Transacao.objects.create(
            usuario=self.user,
            tipo=Transacao.Tipo.DESPESA,
            status=Transacao.Status.PLANEJADO,
            nome="Academia",
            valor=Decimal("95.00"),
            data_base=date(2026, 4, 7),
            data_fim_recorrencia=date(2026, 12, 31),
            recorrencia=Transacao.Recorrencia.MENSAL,
        )
        response = self.client.post(
            reverse("welcome:delete_entry", kwargs={"transacao_id": transacao.id}),
            {"year": "2026", "month": "4", "day": "7"},
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response["Location"], "/welcome/calendario/?year=2026&month=4&day=7")
        transacao.refresh_from_db()
        self.assertFalse(transacao.ativo)

    def test_tela_edicao_exibe_valor_compativel_com_input_number(self):
        """Campo valor deve vir preenchido com separador decimal de ponto."""
        self.client.login(username="welcome_user", password="SenhaForte123!")
        transacao = Transacao.objects.create(
            usuario=self.user,
            tipo=Transacao.Tipo.RECEITA,
            status=Transacao.Status.PLANEJADO,
            nome="Servico",
            valor=Decimal("1234.56"),
            data_base=date(2026, 4, 7),
            data_fim_recorrencia=date(2026, 12, 31),
            recorrencia=Transacao.Recorrencia.MENSAL,
        )
        response = self.client.get(
            reverse("welcome:edit_entry", kwargs={"transacao_id": transacao.id}),
            {"year": "2026", "month": "4", "day": "7"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'value="1234.56"')

    def test_excluir_recorrencia_apenas_ocorrencia(self):
        """Escopo 'one' remove apenas a ocorrencia escolhida da serie."""
        self.client.login(username="welcome_user", password="SenhaForte123!")
        transacao = Transacao.objects.create(
            usuario=self.user,
            tipo=Transacao.Tipo.DESPESA,
            status=Transacao.Status.PLANEJADO,
            nome="Transporte",
            valor=Decimal("50.00"),
            data_base=date(2026, 4, 1),
            data_fim_recorrencia=date(2026, 4, 30),
            recorrencia=Transacao.Recorrencia.DIARIA,
        )
        self.client.post(
            reverse("welcome:delete_entry", kwargs={"transacao_id": transacao.id}),
            {
                "year": "2026",
                "month": "4",
                "day": "10",
                "occurrence_date": "2026-04-10",
                "delete_scope": "one",
            },
        )
        payload = self.client.get(reverse("welcome:api_month"), {"year": 2026, "month": 4}).json()
        dias = [evento["data"] for evento in payload["eventos"] if evento["id"] == transacao.id]
        self.assertIn("2026-04-09", dias)
        self.assertNotIn("2026-04-10", dias)
        self.assertIn("2026-04-11", dias)

    def test_excluir_recorrencia_a_partir_da_ocorrencia(self):
        """Escopo 'from' encerra a recorrencia no dia anterior ao selecionado."""
        self.client.login(username="welcome_user", password="SenhaForte123!")
        transacao = Transacao.objects.create(
            usuario=self.user,
            tipo=Transacao.Tipo.DESPESA,
            status=Transacao.Status.PLANEJADO,
            nome="Assinatura",
            valor=Decimal("20.00"),
            data_base=date(2026, 4, 1),
            data_fim_recorrencia=date(2026, 4, 30),
            recorrencia=Transacao.Recorrencia.DIARIA,
        )
        self.client.post(
            reverse("welcome:delete_entry", kwargs={"transacao_id": transacao.id}),
            {
                "year": "2026",
                "month": "4",
                "day": "15",
                "occurrence_date": "2026-04-15",
                "delete_scope": "from",
            },
        )
        transacao.refresh_from_db()
        self.assertEqual(transacao.data_fim_recorrencia, date(2026, 4, 14))
