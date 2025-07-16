from django.db import models
from django.contrib.auth.models import User
from core.models import Empresa


class Funcionario(models.Model):
    """
    Modelo para representar funcionários (barbeiros, manicures, etc.).
    """
    user = models.OneToOneField(
        User, 
        on_delete=models.CASCADE, 
        blank=True, 
        null=True,
        related_name='funcionario',
        verbose_name="Usuário",
        help_text="Conta de usuário para login do funcionário"
    )
    
    empresa = models.ForeignKey(
        Empresa, 
        on_delete=models.CASCADE, 
        related_name='funcionarios',
        verbose_name="Empresa"
    )
    nome = models.CharField(max_length=200, verbose_name="Nome")
    email = models.EmailField(verbose_name="E-mail")
    telefone = models.CharField(max_length=20, verbose_name="Telefone")
    cargo = models.CharField(
        max_length=100, 
        verbose_name="Cargo",
        help_text="Ex: Barbeiro, Manicure, Esteticista"
    )
    especialidade = models.CharField(
        max_length=200, 
        blank=True, 
        verbose_name="Especialidade",
        help_text="Especialidades específicas do funcionário"
    )
    ativo = models.BooleanField(default=True, verbose_name="Ativo")
    data_contratacao = models.DateField(verbose_name="Data de Contratação")
    data_criacao = models.DateTimeField(auto_now_add=True, verbose_name="Data de Criação")
    data_atualizacao = models.DateTimeField(auto_now=True, verbose_name="Última Atualização")

    class Meta:
        verbose_name = "Funcionário"
        verbose_name_plural = "Funcionários"
        ordering = ['nome']

    def __str__(self):
        return f"{self.nome} ({self.cargo})"

    def get_agendamentos_hoje(self):
        """Retorna agendamentos do funcionário para hoje"""
        from datetime import date
        from agendamentos.models import Agendamento
        return Agendamento.objects.filter(
            funcionario=self,
            data_hora_inicio__date=date.today(),
            status__in=['confirmado', 'em_andamento']
        ).order_by('data_hora_inicio')

    def get_agendamentos_periodo(self, data_inicio, data_fim):
        """Retorna agendamentos do funcionário para um período"""
        from agendamentos.models import Agendamento
        return Agendamento.objects.filter(
            funcionario=self,
            data_hora_inicio__date__range=[data_inicio, data_fim],
            status__in=['confirmado', 'em_andamento']
        ).order_by('data_hora_inicio')


class DisponibilidadeFuncionario(models.Model):
    """
    Modelo para gerenciar a disponibilidade de horários dos funcionários.
    Pode ser usado para definir horários de trabalho, almoço, folgas, etc.
    """
    TIPO_CHOICES = [
        ('trabalho', 'Trabalho'),
        ('almoco', 'Almoço'),
        ('pausa', 'Pausa'),
        ('folga', 'Folga'),
        ('outro', 'Outro'),
    ]

    funcionario = models.ForeignKey(
        Funcionario, 
        on_delete=models.CASCADE, 
        related_name='disponibilidades',
        verbose_name="Funcionário"
    )
    data = models.DateField(verbose_name="Data")
    horario_inicio = models.TimeField(verbose_name="Horário de Início")
    horario_fim = models.TimeField(verbose_name="Horário de Fim")
    tipo = models.CharField(
        max_length=20, 
        choices=TIPO_CHOICES, 
        default='trabalho',
        verbose_name="Tipo"
    )
    observacao = models.TextField(
        blank=True, 
        verbose_name="Observação",
        help_text="Detalhes adicionais sobre este período"
    )
    data_criacao = models.DateTimeField(auto_now_add=True, verbose_name="Data de Criação")

    class Meta:
        verbose_name = "Disponibilidade do Funcionário"
        verbose_name_plural = "Disponibilidades dos Funcionários"
        ordering = ['data','horario_inicio']
        unique_together = ['funcionario', 'data', 'horario_inicio', 'horario_fim']

    def __str__(self):
        return f"{self.funcionario.nome} - {self.data} ({self.horario_inicio}-{self.horario_fim}) - {self.get_tipo_display()}"

    def clean(self):
        """Validação personalizada"""
        from django.core.exceptions import ValidationError
        
        if self.horario_inicio >= self.horario_fim:
            raise ValidationError("Horário de início deve ser anterior ao horário de fim.")

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)
