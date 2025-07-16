from django.db import models
from core.models import Empresa
from funcionarios.models import Funcionario


class Servico(models.Model):
    """
    Modelo para representar serviços oferecidos pela empresa.
    """
    empresa = models.ForeignKey(
        Empresa, 
        on_delete=models.CASCADE, 
        related_name='servicos',
        verbose_name="Empresa"
    )
    nome = models.CharField(max_length=200, verbose_name="Nome do Serviço")
    descricao = models.TextField(
        blank=True, 
        verbose_name="Descrição",
        help_text="Descrição detalhada do serviço"
    )
    duracao = models.PositiveIntegerField(
        verbose_name="Duração (minutos)",
        help_text="Duração média do serviço em minutos"
    )
    preco = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        verbose_name="Preço",
        help_text="Preço base do serviço"
    )
    ativo = models.BooleanField(default=True, verbose_name="Ativo")
    funcionarios = models.ManyToManyField(
        Funcionario,
        through='FuncionarioServico',
        related_name='servicos',
        verbose_name="Funcionários"
    )
    data_criacao = models.DateTimeField(auto_now_add=True, verbose_name="Data de Criação")
    data_atualizacao = models.DateTimeField(auto_now=True, verbose_name="Última Atualização")

    class Meta:
        verbose_name = "Serviço"
        verbose_name_plural = "Serviços"
        ordering = ['nome']
        unique_together = ['empresa', 'nome']  # Nome único por empresa

    def __str__(self):
        return f"{self.nome} - {self.empresa.nome}"

    def get_funcionarios_disponiveis(self):
        """Retorna funcionários ativos que oferecem este serviço"""
        return self.funcionarios.filter(ativo=True)


class FuncionarioServico(models.Model):
    """
    Tabela intermediária para relacionamento Many-to-Many entre Funcionario e Servico.
    Permite adicionar atributos específicos da relação.
    """
    funcionario = models.ForeignKey(
        Funcionario, 
        on_delete=models.CASCADE,
        verbose_name="Funcionário"
    )
    servico = models.ForeignKey(
        Servico, 
        on_delete=models.CASCADE,
        verbose_name="Serviço"
    )
    preco_especifico = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        blank=True, 
        null=True,
        verbose_name="Preço Específico",
        help_text="Preço específico deste funcionário para este serviço (opcional)"
    )
    duracao_especifica = models.PositiveIntegerField(
        blank=True, 
        null=True,
        verbose_name="Duração Específica (minutos)",
        help_text="Duração específica deste funcionário para este serviço (opcional)"
    )
    data_associacao = models.DateTimeField(auto_now_add=True, verbose_name="Data de Associação")

    class Meta:
        verbose_name = "Funcionário-Serviço"
        verbose_name_plural = "Funcionários-Serviços"
        unique_together = ['funcionario', 'servico']

    def __str__(self):
        return f"{self.funcionario.nome} - {self.servico.nome}"

    def get_preco_final(self):
        """Retorna o preço específico ou o preço base do serviço"""
        return self.preco_especifico if self.preco_especifico else self.servico.preco

    def get_duracao_final(self):
        """Retorna a duração específica ou a duração base do serviço"""
        return self.duracao_especifica if self.duracao_especifica else self.servico.duracao
