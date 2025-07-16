from django.db import models
from django.contrib.auth.models import User


class Cliente(models.Model):
    """
    Modelo para representar clientes do sistema.
    Pode ser integrado com o sistema de autenticação do Django.
    """
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        related_name='cliente',
        verbose_name="Usuário",
        help_text="Usuário do sistema (opcional para clientes não cadastrados)"
    )
    nome = models.CharField(max_length=200, verbose_name="Nome")
    email = models.EmailField(unique=True, verbose_name="E-mail")
    telefone = models.CharField(max_length=20, verbose_name="Telefone")
    data_nascimento = models.DateField(
        blank=True,
        null=True,
        verbose_name="Data de Nascimento"
    )
    endereco = models.TextField(
        blank=True,
        verbose_name="Endereço"
    )
    observacoes = models.TextField(
        blank=True,
        verbose_name="Observações",
        help_text="Observações sobre o cliente (preferências, alergias, etc.)"
    )
    ativo = models.BooleanField(default=True, verbose_name="Ativo")
    data_criacao = models.DateTimeField(auto_now_add=True, verbose_name="Data de Criação")
    data_atualizacao = models.DateTimeField(auto_now=True, verbose_name="Última Atualização")

    class Meta:
        verbose_name = "Cliente"
        verbose_name_plural = "Clientes"
        ordering = ["nome"]

    def __str__(self):
        return f"{self.nome} ({self.email})"

    def get_nome_display(self):
        """Retorna o nome do cliente ou do usuário associado"""
        if self.user and self.user.first_name:
            return f"{self.user.first_name} {self.user.last_name}".strip()
        return self.nome

    def get_agendamentos_ativos(self):
        """Retorna agendamentos ativos do cliente"""
        from agendamentos.models import Agendamento
        return Agendamento.objects.filter(
            cliente=self,
            status__in=["confirmado", "pendente"]
        ).order_by("data_hora_inicio")

    def get_historico_agendamentos(self):
        """Retorna histórico completo de agendamentos do cliente"""
        from agendamentos.models import Agendamento
        return Agendamento.objects.filter(cliente=self).order_by("-data_hora_inicio")
