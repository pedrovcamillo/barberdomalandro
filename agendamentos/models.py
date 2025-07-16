from django.db import models
from django.utils import timezone
from datetime import timedelta
from core.models import Empresa
from funcionarios.models import Funcionario
from servicos.models import Servico
from clientes.models import Cliente


class Agendamento(models.Model):
    """
    Modelo para representar agendamentos de serviços.
    Inclui chaves estrangeiras diretas para facilitar consultas.
    """
    STATUS_CHOICES = [
        ("pendente", "Pendente"),
        ("confirmado", "Confirmado"),
        ("em_andamento", "Em Andamento"),
        ("concluido", "Concluído"),
        ("cancelado", "Cancelado"),
        ("nao_compareceu", "Não Compareceu"),
    ]

    # Chaves estrangeiras diretas para facilitar consultas
    empresa = models.ForeignKey(
        Empresa, 
        on_delete=models.CASCADE, 
        related_name="agendamentos",
        verbose_name="Empresa"
    )
    cliente = models.ForeignKey(
        Cliente, 
        on_delete=models.CASCADE, 
        related_name="agendamentos",
        verbose_name="Cliente"
    )
    funcionario = models.ForeignKey(
        Funcionario, 
        on_delete=models.CASCADE, 
        related_name="agendamentos",
        verbose_name="Funcionário"
    )
    servico = models.ForeignKey(
        Servico, 
        on_delete=models.CASCADE, 
        related_name="agendamentos",
        verbose_name="Serviço"
    )
    
    # Dados do agendamento
    data_hora_inicio = models.DateTimeField(verbose_name="Data e Hora de Início")
    data_hora_fim = models.DateTimeField(verbose_name="Data e Hora de Fim")
    status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES, 
        default="pendente",
        verbose_name="Status"
    )
    preco_cobrado = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        verbose_name="Preço Cobrado",
        help_text="Preço efetivamente cobrado pelo serviço"
    )
    observacoes = models.TextField(
        blank=True, 
        verbose_name="Observações",
        help_text="Observações sobre o agendamento"
    )
    
    # Metadados
    data_criacao = models.DateTimeField(auto_now_add=True, verbose_name="Data de Criação")
    data_atualizacao = models.DateTimeField(auto_now=True, verbose_name="Última Atualização")
    cancelado_por = models.CharField(
        max_length=100, 
        blank=True, 
        verbose_name="Cancelado Por",
        help_text="Quem cancelou o agendamento (cliente, funcionário, sistema)"
    )
    motivo_cancelamento = models.TextField(
        blank=True, 
        verbose_name="Motivo do Cancelamento"
    )

    class Meta:
        verbose_name = "Agendamento"
        verbose_name_plural = "Agendamentos"
        ordering = ["-data_hora_inicio"]

    def __str__(self):
        return f"{self.cliente.nome} - {self.servico.nome} - {self.data_hora_inicio.strftime("%d/%m/%Y %H:%M")}"

    def clean(self):
        """Validações personalizadas"""
        from django.core.exceptions import ValidationError
        
        if self.data_hora_inicio >= self.data_hora_fim:
            raise ValidationError("Data/hora de início deve ser anterior à data/hora de fim.")
        
        if self.data_hora_inicio < timezone.now():
            raise ValidationError("Não é possível agendar para uma data/hora no passado.")

    def save(self, *args, **kwargs):
        # Calcular data_hora_fim se não foi fornecida
        if not self.data_hora_fim and self.servico:
            from servicos.models import FuncionarioServico
            try:
                func_servico = FuncionarioServico.objects.get(
                    funcionario=self.funcionario, 
                    servico=self.servico
                )
                duracao = func_servico.get_duracao_final()
            except FuncionarioServico.DoesNotExist:
                duracao = self.servico.duracao
            
            self.data_hora_fim = self.data_hora_inicio + timedelta(minutes=duracao)
        
        # Definir preço cobrado se não foi fornecido
        if not self.preco_cobrado and self.servico:
            from servicos.models import FuncionarioServico
            try:
                func_servico = FuncionarioServico.objects.get(
                    funcionario=self.funcionario, 
                    servico=self.servico
                )
                self.preco_cobrado = func_servico.get_preco_final()
            except FuncionarioServico.DoesNotExist:
                self.preco_cobrado = self.servico.preco
        
        self.clean()
        super().save(*args, **kwargs)

    def pode_ser_cancelado(self):
        """Verifica se o agendamento pode ser cancelado"""
        if self.status in ["cancelado", "concluido", "nao_compareceu"]:
            return False
        
        # Verificar antecedência mínima para cancelamento
        antecedencia = self.empresa.parametros.antecedencia_cancelamento
        limite_cancelamento = self.data_hora_inicio - timedelta(minutes=antecedencia)
        
        return timezone.now() <= limite_cancelamento

    def get_duracao_total(self):
        """Retorna a duração total do agendamento"""
        return self.data_hora_fim - self.data_hora_inicio


class FilaEspera(models.Model):
    """
    Modelo para gerenciar fila de espera quando não há horários disponíveis.
    Melhorado com mais atributos de controle.
    """
    empresa = models.ForeignKey(
        Empresa, 
        on_delete=models.CASCADE, 
        related_name="fila_espera",
        verbose_name="Empresa"
    )
    cliente = models.ForeignKey(
        Cliente, 
        on_delete=models.CASCADE, 
        related_name="fila_espera",
        verbose_name="Cliente"
    )
    servico = models.ForeignKey(
        Servico, 
        on_delete=models.CASCADE, 
        blank=True, 
        null=True,
        related_name="fila_espera",
        verbose_name="Serviço",
        help_text="Serviço desejado (opcional)"
    )
    funcionario_preferido = models.ForeignKey(
        Funcionario, 
        on_delete=models.CASCADE, 
        blank=True, 
        null=True,
        related_name="fila_espera",
        verbose_name="Funcionário Preferido",
        help_text="Funcionário preferido (opcional)"
    )
    
    # Preferências de agendamento
    data_desejada = models.DateField(verbose_name="Data Desejada")
    horario_desejado = models.TimeField(
        blank=True, 
        null=True, 
        verbose_name="Horário Desejado",
        help_text="Horário preferido (opcional)"
    )
    flexivel_data = models.BooleanField(
        default=True, 
        verbose_name="Flexível com Data",
        help_text="Aceita outras datas próximas"
    )
    flexivel_horario = models.BooleanField(
        default=True, 
        verbose_name="Flexível com Horário",
        help_text="Aceita outros horários"
    )
    
    # Controle da fila
    prioridade = models.PositiveIntegerField(
        default=1, 
        verbose_name="Prioridade",
        help_text="Menor número = maior prioridade"
    )
    data_solicitacao = models.DateTimeField(auto_now_add=True, verbose_name="Data da Solicitação")
    notificado = models.BooleanField(default=False, verbose_name="Notificado")
    data_notificacao = models.DateTimeField(
        blank=True, 
        null=True, 
        verbose_name="Data da Notificação"
    )
    ativo = models.BooleanField(default=True, verbose_name="Ativo")
    observacoes = models.TextField(
        blank=True, 
        verbose_name="Observações"
    )

    class Meta:
        verbose_name = "Fila de Espera"
        verbose_name_plural = "Fila de Espera"
        ordering = ["prioridade", "data_solicitacao"]

    def __str__(self):
        servico_str = f" - {self.servico.nome}" if self.servico else ""
        return f"{self.cliente.nome}{servico_str} - {self.data_desejada}"

    def marcar_como_notificado(self):
        """Marca o cliente como notificado"""
        self.notificado = True
        self.data_notificacao = timezone.now()
        self.save(update_fields=["notificado", "data_notificacao"])

    def desativar(self):
        """Desativa a entrada da fila de espera"""
        self.ativo = False
        self.save(update_fields=["ativo"])
