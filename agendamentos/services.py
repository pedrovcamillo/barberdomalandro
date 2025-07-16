from datetime import datetime, timedelta, time, date
from typing import List, Tuple, Optional
from django.utils import timezone
from django.db.models import Q
from core.models import Empresa, ParametrosEmpresa
from funcionarios.models import Funcionario, DisponibilidadeFuncionario
from servicos.models import Servico, FuncionarioServico
from clientes.models import Cliente
from .models import Agendamento, FilaEspera
from core.whatsapp import enviar_whatsapp


class DisponibilidadeService:
    """
    Serviço responsável por gerenciar a disponibilidade de horários para agendamentos.
    """
    
    def __init__(self, empresa: Empresa):
        self.empresa = empresa
        self.parametros = empresa.parametros
    
    def get_horarios_disponiveis(
        self, 
        funcionario: Funcionario, 
        servico: Servico, 
        data: date
    ) -> List[datetime]:
        """
        Retorna uma lista de horários disponíveis para um funcionário em uma data específica.
        
        Args:
            funcionario: O funcionário para verificar disponibilidade
            servico: O serviço a ser agendado
            data: A data para verificar disponibilidade
            
        Returns:
            Lista de objetos datetime representando os horários disponíveis
        """
        # Verificar se a data não é no passado
        if data < timezone.now().date():
            return []
        
        # Verificar se o funcionário oferece o serviço
        if not self._funcionario_oferece_servico(funcionario, servico):
            return []
        
        # Obter duração do serviço para este funcionário
        duracao_servico = self._get_duracao_servico(funcionario, servico)
        
        # Obter períodos de trabalho do funcionário para a data
        periodos_trabalho = self._get_periodos_trabalho(funcionario, data)
        
        # Obter períodos ocupados (agendamentos + bloqueios)
        periodos_ocupados = self._get_periodos_ocupados(funcionario, data)
        
        # Gerar slots disponíveis
        slots_disponiveis = self._gerar_slots_disponiveis(
            periodos_trabalho, 
            periodos_ocupados, 
            duracao_servico, 
            data
        )
        
        return slots_disponiveis
    
    def _funcionario_oferece_servico(self, funcionario: Funcionario, servico: Servico) -> bool:
        """Verifica se o funcionário oferece o serviço especificado."""
        return FuncionarioServico.objects.filter(
            funcionario=funcionario, 
            servico=servico
        ).exists()
    
    def _get_duracao_servico(self, funcionario: Funcionario, servico: Servico) -> int:
        """Obtém a duração do serviço para o funcionário específico."""
        try:
            func_servico = FuncionarioServico.objects.get(
                funcionario=funcionario, 
                servico=servico
            )
            return func_servico.get_duracao_final()
        except FuncionarioServico.DoesNotExist:
            return servico.duracao
    
    def _get_periodos_trabalho(self, funcionario: Funcionario, data: date) -> List[Tuple[time, time]]:
        """
        Obtém os períodos de trabalho do funcionário para uma data específica.
        
        Returns:
            Lista de tuplas (horario_inicio, horario_fim) dos períodos de trabalho
        """
        # Verificar se há disponibilidade específica para a data
        disponibilidades_trabalho = DisponibilidadeFuncionario.objects.filter(
            funcionario=funcionario,
            data=data,
            tipo="trabalho"
        ).order_by("horario_inicio")
        
        if disponibilidades_trabalho.exists():
            # Usar horários específicos definidos para a data
            return [
                (disp.horario_inicio, disp.horario_fim) 
                for disp in disponibilidades_trabalho
            ]
        else:
            # Usar horários padrão da empresa
            return self._get_horarios_padrao_empresa(data)
    
    def _get_horarios_padrao_empresa(self, data: date) -> List[Tuple[time, time]]:
        """Obtém os horários padrão de funcionamento da empresa para uma data."""
        # Verificar se a empresa funciona no dia da semana
        dias_semana = {
            0: "seg", 1: "ter", 2: "qua", 3: "qui", 
            4: "sex", 5: "sab", 6: "dom"
        }
        
        dia_semana = dias_semana[data.weekday()]
        dias_funcionamento = self.parametros.get_dias_funcionamento_list()
        
        if dia_semana in dias_funcionamento:
            return [(self.parametros.horario_abertura, self.parametros.horario_fechamento)]
        else:
            return []  # Empresa não funciona neste dia
    
    def _get_periodos_ocupados(self, funcionario: Funcionario, data: date) -> List[Tuple[time, time]]:
        """
        Obtém todos os períodos ocupados do funcionário para uma data específica.
        Inclui agendamentos confirmados e bloqueios de disponibilidade.
        
        Returns:
            Lista de tuplas (horario_inicio, horario_fim) dos períodos ocupados
        """
        periodos_ocupados = []
        
        # Agendamentos confirmados
        agendamentos = Agendamento.objects.filter(
            funcionario=funcionario,
            data_hora_inicio__date=data,
            status__in=["confirmado", "em_andamento"]
        )
        
        for agendamento in agendamentos:
            periodos_ocupados.append((
                agendamento.data_hora_inicio.time(),
                agendamento.data_hora_fim.time()
            ))
        
        # Bloqueios de disponibilidade (almoço, pausa, etc.)
        bloqueios = DisponibilidadeFuncionario.objects.filter(
            funcionario=funcionario,
            data=data,
            tipo__in=["almoco", "pausa", "outro"]
        )
        
        for bloqueio in bloqueios:
            periodos_ocupados.append((
                bloqueio.horario_inicio,
                bloqueio.horario_fim
            ))
        
        # Verificar se há folga para o dia inteiro
        folga_dia_inteiro = DisponibilidadeFuncionario.objects.filter(
            funcionario=funcionario,
            data=data,
            tipo="folga"
        ).exists()
        
        if folga_dia_inteiro:
            # Se há folga, o dia inteiro está ocupado
            periodos_ocupados.append((time(0, 0), time(23, 59)))
        
        return periodos_ocupados
    
    def _gerar_slots_disponiveis(
        self, 
        periodos_trabalho: List[Tuple[time, time]], 
        periodos_ocupados: List[Tuple[time, time]], 
        duracao_servico: int, 
        data: date
    ) -> List[datetime]:
        """
        Gera os slots de horários disponíveis com base nos períodos de trabalho e ocupados.
        
        Args:
            periodos_trabalho: Lista de períodos de trabalho
            periodos_ocupados: Lista de períodos ocupados
            duracao_servico: Duração do serviço em minutos
            data: Data para gerar os slots
            
        Returns:
            Lista de horários disponíveis como objetos datetime
        """
        slots_disponiveis = []
        intervalo = self.parametros.intervalo_agendamento
        
        for inicio_trabalho, fim_trabalho in periodos_trabalho:
            # Converter para datetime para facilitar cálculos
            inicio_dt = datetime.combine(data, inicio_trabalho)
            fim_dt = datetime.combine(data, fim_trabalho)
            
            # Gerar slots dentro do período de trabalho
            slot_atual = inicio_dt
            
            while slot_atual + timedelta(minutes=duracao_servico) <= fim_dt:
                slot_fim = slot_atual + timedelta(minutes=duracao_servico)
                
                # Verificar se o slot não conflita com períodos ocupados
                if not self._slot_conflita_com_ocupados(
                    slot_atual.time(), 
                    slot_fim.time(), 
                    periodos_ocupados
                ):
                    # Verificar antecedência mínima
                    if self._slot_respeita_antecedencia(slot_atual):
                        slots_disponiveis.append(
                            timezone.make_aware(slot_atual)
                        )
                
                # Avançar para o próximo slot
                slot_atual += timedelta(minutes=intervalo)
        
        return slots_disponiveis
    
    def _slot_conflita_com_ocupados(
        self, 
        slot_inicio: time, 
        slot_fim: time, 
        periodos_ocupados: List[Tuple[time, time]]
    ) -> bool:
        """Verifica se um slot conflita com algum período ocupado."""
        for ocupado_inicio, ocupado_fim in periodos_ocupados:
            # Verificar sobreposição de horários
            if (slot_inicio < ocupado_fim and slot_fim > ocupado_inicio):
                return True
        return False
    
    def _slot_respeita_antecedencia(self, slot_datetime: datetime) -> bool:
        """Verifica se o slot respeita a antecedência mínima para agendamentos."""
        agora = timezone.now()
        antecedencia_minima = timedelta(minutes=self.parametros.antecedencia_minima)
        
        return timezone.make_aware(slot_datetime) >= agora + antecedencia_minima


class AgendamentoService:
    """
    Serviço responsável por criar e gerenciar agendamentos.
    """

    def __init__(self, empresa: Empresa):
        self.empresa = empresa
        self.disponibilidade_service = DisponibilidadeService(empresa)

    def criar_agendamento(
        self,
        cliente: Cliente,
        funcionario: Funcionario,
        servico: Servico,
        data_hora_inicio: datetime
    ) -> Tuple[bool, str, Optional[Agendamento]]:
        """
        Cria um novo agendamento.

        Args:
            cliente: Cliente que está agendando
            funcionario: Funcionário que prestará o serviço
            servico: Serviço a ser prestado
            data_hora_inicio: Data e hora de início do agendamento

        Returns:
            Tupla (sucesso, mensagem, agendamento_criado)
        """
        # Obter duração do serviço para este funcionário e calcular data_hora_fim
        duracao = self.disponibilidade_service._get_duracao_servico(funcionario, servico)
        data_hora_fim = data_hora_inicio + timedelta(minutes=duracao)

        # Verificar se o horário está disponível (verificação inicial)
        horarios_disponiveis = self.disponibilidade_service.get_horarios_disponiveis(
            funcionario, servico, data_hora_inicio.date()
        )

        if data_hora_inicio not in horarios_disponiveis:
            return False, "Horário não disponível para agendamento ou já ocupado.", None

        # VERIFICAÇÃO DE CONFLITO FINAL (MAIS ROBUSTA)
        conflitos_existentes = Agendamento.objects.filter(
            funcionario=funcionario,
            data_hora_inicio__lt=data_hora_fim,
            data_hora_fim__gt=data_hora_inicio,
            status__in=["confirmado", "em_andamento"]
        ).exists()

        if conflitos_existentes:
            return False, "O horário selecionado foi recentemente ocupado. Por favor, escolha outro.", None

        try:
            # Obter preço do serviço
            try:
                func_servico = FuncionarioServico.objects.get(
                    funcionario=funcionario, servico=servico
                )
                preco = func_servico.get_preco_final()
            except FuncionarioServico.DoesNotExist:
                preco = servico.preco

            # Criar o agendamento
            agendamento = Agendamento.objects.create(
                empresa=self.empresa,
                cliente=cliente,
                funcionario=funcionario,
                servico=servico,
                data_hora_inicio=data_hora_inicio,
                data_hora_fim=data_hora_fim,
                preco_cobrado=preco,
                status="confirmado"
            )

            # Enviar notificação via WhatsApp
            mensagem = (
                f"Olá {cliente.nome}, seu horário com {funcionario.nome} foi confirmado "
                f"para o dia {data_hora_inicio.strftime('%d/%m/%Y')} às {data_hora_inicio.strftime('%H:%M')}."
            )
            numero_cliente = f"whatsapp:+55{''.join(filter(str.isdigit, cliente.telefone))}"
            enviar_whatsapp(mensagem, numero_cliente)

            return True, "Agendamento criado com sucesso!", agendamento

        except Exception as e:
            return False, f"Erro ao criar agendamento: {str(e)}", None

class FilaEsperaService:
    """
    Serviço responsável por gerenciar a fila de espera.
    """
    
    def __init__(self, empresa: Empresa):
        self.empresa = empresa

    def adicionar_a_fila(
        self, 
        cliente: Cliente, 
        data_desejada: date, 
        servico: Optional[Servico] = None, 
        funcionario_preferido: Optional[Funcionario] = None,
        horario_desejado: Optional[time] = None,
        flexivel_data: bool = True,
        flexivel_horario: bool = True,
        observacoes: str = ""
    ) -> Tuple[bool, str, Optional[FilaEspera]]:
        """
        Adiciona um cliente à fila de espera.
        """
        try:
            fila_espera_entry = FilaEspera.objects.create(
                empresa=self.empresa,
                cliente=cliente,
                servico=servico,
                funcionario_preferido=funcionario_preferido,
                data_desejada=data_desejada,
                horario_desejado=horario_desejado,
                flexivel_data=flexivel_data,
                flexivel_horario=flexivel_horario,
                observacoes=observacoes
            )
            return True, "Adicionado à fila de espera com sucesso!", fila_espera_entry
        except Exception as e:
            return False, f"Erro ao adicionar à fila de espera: {str(e)}", None

    def verificar_e_notificar_fila(
        self, 
        funcionario: Funcionario, 
        data_hora_vaga: datetime,
        servico_vago: Optional[Servico] = None
    ):
        """
        Verifica a fila de espera por clientes que possam se encaixar em um horário vago
        e os notifica.
        """
        # Lógica para encontrar clientes na fila que se encaixam no horário
        # e enviar notificações (e-mail, SMS, etc.)
        # Esta é uma lógica complexa que pode envolver tarefas assíncronas (Celery)
        # Por enquanto, vamos apenas simular a notificação.

        # Exemplo simplificado: encontrar clientes que desejam o serviço e funcionário
        # e que são flexíveis com data/horário ou que a data/horário desejado se encaixa
        
        candidatos = FilaEspera.objects.filter(
            empresa=self.empresa,
            notificado=False, # Ainda não notificado
            ativo=True,
            data_desejada__lte=data_hora_vaga.date() # Data desejada é anterior ou igual à vaga
        ).order_by("prioridade", "data_solicitacao")

        if servico_vago:
            candidatos = candidatos.filter(Q(servico=servico_vago) | Q(servico__isnull=True))
        
        if funcionario:
            candidatos = candidatos.filter(Q(funcionario_preferido=funcionario) | Q(funcionario_preferido__isnull=True))

        for entry in candidatos:
            # Lógica mais complexa aqui para verificar se o slot realmente atende a preferência
            # Por exemplo, se o cliente não é flexível, o horário deve ser exatamente o desejado
            
            # Simulação de notificação
            print(f"Notificando cliente {entry.cliente.nome} sobre horário vago: {data_hora_vaga}")
            entry.marcar_como_notificado()
            # Aqui você integraria com um serviço de e-mail/SMS

    def remover_da_fila(self, fila_espera_entry: FilaEspera) -> bool:
        """
        Remove (desativa) uma entrada da fila de espera.
        """
        try:
            fila_espera_entry.desativar()
            return True
        except Exception:
            return False

