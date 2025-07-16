from django.db import models


class Empresa(models.Model):
    """
    Modelo para representar a empresa (barbearia ou outro negócio).
    Base para a modularidade do sistema.
    """
    nome = models.CharField(max_length=200, verbose_name="Nome da Empresa")
    cnpj = models.CharField(max_length=18, unique=True, verbose_name="CNPJ")
    email = models.EmailField(verbose_name="E-mail")
    telefone = models.CharField(max_length=20, verbose_name="Telefone")
    endereco = models.TextField(verbose_name="Endereço")
    logo = models.ImageField(upload_to='logos/', blank=True, null=True, verbose_name="Logo")
    ativo = models.BooleanField(default=True, verbose_name="Ativo")
    data_criacao = models.DateTimeField(auto_now_add=True, verbose_name="Data de Criação")
    data_atualizacao = models.DateTimeField(auto_now=True, verbose_name="Última Atualização")

    class Meta:
        verbose_name = "Empresa"
        verbose_name_plural = "Empresas"
        ordering = ['nome']

    def __str__(self):
        return self.nome


class ParametrosEmpresa(models.Model):
    """
    Parâmetros gerais de configuração para cada empresa.
    Permite personalização por empresa para escalabilidade.
    """
    empresa = models.OneToOneField(
        Empresa, 
        on_delete=models.CASCADE, 
        related_name='parametros',
        verbose_name="Empresa"
    )
    horario_abertura = models.TimeField(verbose_name="Horário de Abertura")
    horario_fechamento = models.TimeField(verbose_name="Horário de Fechamento")
    intervalo_agendamento = models.PositiveIntegerField(
        default=30, 
        verbose_name="Intervalo de Agendamento (minutos)",
        help_text="Duração mínima dos slots de agendamento em minutos"
    )
    dias_funcionamento = models.CharField(
        max_length=50,
        verbose_name="Dias de Funcionamento",
        help_text="Dias da semana separados por vírgula (ex: seg,ter,qua,qui,sex)"
    )
    antecedencia_minima = models.PositiveIntegerField(
        default=60,
        verbose_name="Antecedência Mínima (minutos)",
        help_text="Tempo mínimo de antecedência para agendamentos"
    )
    antecedencia_cancelamento = models.PositiveIntegerField(
        default=120,
        verbose_name="Antecedência para Cancelamento (minutos)",
        help_text="Tempo mínimo de antecedência para cancelar agendamentos"
    )

    class Meta:
        verbose_name = "Parâmetros da Empresa"
        verbose_name_plural = "Parâmetros das Empresas"

    def __str__(self):
        return f"Parâmetros - {self.empresa.nome}"

    def get_dias_funcionamento_list(self):
        """Retorna lista dos dias de funcionamento"""
        return [dia.strip() for dia in self.dias_funcionamento.split(',') if dia.strip()]
