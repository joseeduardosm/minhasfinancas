"""Modelos do dominio financeiro."""

from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models


class Transacao(models.Model):
    """Representa uma receita ou despesa do usuario, com opcao de recorrencia."""

    class Tipo(models.TextChoices):
        """Tipos possiveis de transacao."""

        RECEITA = "RECEITA", "Receita"
        DESPESA = "DESPESA", "Despesa"

    class Status(models.TextChoices):
        """Status de execucao financeira."""

        PLANEJADO = "PLANEJADO", "Planejado"
        EXECUTADO = "EXECUTADO", "Executado"

    class Recorrencia(models.TextChoices):
        """Periodicidade de repeticao da transacao."""

        DIARIA = "DIARIA", "Diaria"
        SEMANAL = "SEMANAL", "Semanal"
        QUINZENAL = "QUINZENAL", "Quinzenal"
        MENSAL = "MENSAL", "Mensal"
        TRIMESTRAL = "TRIMESTRAL", "Trimestral"
        SEMESTRAL = "SEMESTRAL", "Semestral"
        ANUAL = "ANUAL", "Anual"

    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="transacoes",
        verbose_name="Usuario",
    )
    tipo = models.CharField(max_length=10, choices=Tipo.choices, verbose_name="Tipo")
    status = models.CharField(max_length=10, choices=Status.choices, verbose_name="Status")
    nome = models.CharField(max_length=120, verbose_name="Nome")
    valor = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Valor")
    data_base = models.DateField(verbose_name="Data base")
    data_fim_recorrencia = models.DateField(
        null=True,
        blank=True,
        verbose_name="Data fim da recorrencia",
    )
    recorrencia = models.CharField(
        max_length=12,
        choices=Recorrencia.choices,
        default=Recorrencia.MENSAL,
        verbose_name="Recorrencia",
    )
    ativo = models.BooleanField(default=True, verbose_name="Ativo")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Criado em")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Atualizado em")

    class Meta:
        """Metadados do modelo de transacao."""

        ordering = ["data_base", "tipo", "nome"]
        verbose_name = "Transacao"
        verbose_name_plural = "Transacoes"

    def __str__(self):
        """Descricao amigavel para listagens administrativas."""
        return f"{self.nome} ({self.get_tipo_display()})"

    def clean(self):
        """Garante coerencia de valores monetarios."""
        super().clean()
        if self.valor is None or self.valor <= Decimal("0"):
            raise ValidationError({"valor": "O valor deve ser maior que zero."})
        if self.data_fim_recorrencia is None:
            raise ValidationError(
                {"data_fim_recorrencia": "Informe a data fim da recorrencia."}
            )
        if self.data_fim_recorrencia < self.data_base:
            raise ValidationError(
                {"data_fim_recorrencia": "A data fim deve ser maior ou igual a data base."}
            )


class TransacaoExcecao(models.Model):
    """Registra dias que devem ser ignorados para uma transacao recorrente."""

    transacao = models.ForeignKey(
        Transacao,
        on_delete=models.CASCADE,
        related_name="excecoes",
        verbose_name="Transacao",
    )
    data = models.DateField(verbose_name="Data excluida")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Criado em")

    class Meta:
        """Metadados de excecao de recorrencia."""

        unique_together = ("transacao", "data")
        ordering = ["data"]
        verbose_name = "Excecao de transacao"
        verbose_name_plural = "Excecoes de transacoes"

    def __str__(self):
        """Descricao amigavel para listagens administrativas."""
        return f"{self.transacao_id} - {self.data.isoformat()}"
