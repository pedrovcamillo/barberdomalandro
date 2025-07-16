from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.contrib import messages
from django.utils import timezone
from datetime import datetime, date, timedelta 
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
import json
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.db import transaction 


from core.models import Empresa
from funcionarios.models import Funcionario
from servicos.models import Servico
from clientes.models import Cliente
from .models import Agendamento, FilaEspera
from .services import DisponibilidadeService, AgendamentoService, FilaEsperaService
from core.whatsapp import enviar_whatsapp
from django.http import JsonResponse
from django.contrib import messages


def home(request ):
    """View principal do sistema"""
    empresas = Empresa.objects.filter(ativo=True)
    context = {
        "empresas": empresas,
        "titulo": "Sistema de Agendamentos"
    }
    return render(request, "agendamentos/home.html", context)


def empresa_detail(request, empresa_id):
    """Página de detalhes da empresa com serviços e funcionários"""
    empresa = get_object_or_404(Empresa, id=empresa_id, ativo=True)
    servicos = empresa.servicos.filter(ativo=True)
    funcionarios = empresa.funcionarios.filter(ativo=True)
    
    context = {
        "empresa": empresa,
        "servicos": servicos,
        "funcionarios": funcionarios,
        "titulo": f"Agendamento - {empresa.nome}"
    }
    return render(request, "agendamentos/empresa_detail.html", context)


def verificar_disponibilidade(request, empresa_id):
    """API para verificar horários disponíveis"""
    if request.method != "POST":
        return JsonResponse({"error": "Método não permitido"}, status=405)
    
    try:
        data = json.loads(request.body)
        funcionario_id = data.get("funcionario_id")
        servico_id = data.get("servico_id")
        data_str = data.get("data")
        
        # Validar dados
        if not all([funcionario_id, servico_id, data_str]):
            return JsonResponse({"error": "Dados incompletos"}, status=400)
        
        empresa = get_object_or_404(Empresa, id=empresa_id, ativo=True)
        funcionario = get_object_or_404(Funcionario, id=funcionario_id, empresa=empresa)
        servico = get_object_or_404(Servico, id=servico_id, empresa=empresa)
        
        # Converter string de data para objeto date
        data_agendamento = datetime.strptime(data_str, "%Y-%m-%d").date()
        
        # Verificar disponibilidade
        disponibilidade_service = DisponibilidadeService(empresa)
        horarios_disponiveis = disponibilidade_service.get_horarios_disponiveis(
            funcionario, servico, data_agendamento
        )
        
        # Converter para formato JSON
        horarios_json = [
            {
                "datetime": horario.isoformat(),
                "display": horario.strftime("%H:%M")
            }
            for horario in horarios_disponiveis
        ]
        
        return JsonResponse({
            "success": True,
            "horarios": horarios_json,
            "funcionario": funcionario.nome,
            "servico": servico.nome,
            "data": data_agendamento.strftime("%d/%m/%Y")
        })
        
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


def criar_agendamento(request, empresa_id):
    """View para criar um novo agendamento"""
    if request.method != "POST":
        return JsonResponse({"error": "Método não permitido"}, status=405)
    
    try:
        data = json.loads(request.body)
        
        # Extrair dados do request
        cliente_nome = data.get("cliente_nome")
        cliente_email = data.get("cliente_email")
        cliente_telefone = data.get("cliente_telefone")
        funcionario_id = data.get("funcionario_id")
        servico_id = data.get("servico_id")
        data_hora_str = data.get("data_hora")
        
        # Validar dados obrigatórios
        if not all([cliente_nome, cliente_email, funcionario_id, servico_id, data_hora_str]):
            return JsonResponse({"error": "Dados obrigatórios não fornecidos"}, status=400)
        
        # Obter objetos do banco
        empresa = get_object_or_404(Empresa, id=empresa_id, ativo=True)
        funcionario = get_object_or_404(Funcionario, id=funcionario_id, empresa=empresa)
        servico = get_object_or_404(Servico, id=servico_id, empresa=empresa)
        
        # Converter string para datetime
        data_hora_inicio = datetime.fromisoformat(data_hora_str.replace("Z", "+00:00"))
        if timezone.is_naive(data_hora_inicio):
            data_hora_inicio = timezone.make_aware(data_hora_inicio)
        
        # Buscar ou criar cliente
        cliente, created = Cliente.objects.get_or_create(
            email=cliente_email,
            defaults={
                "nome": cliente_nome,
                "telefone": cliente_telefone or ""
            }
        )
        
        # Se o cliente já existe, atualizar dados se necessário
        if not created:
            if cliente.nome != cliente_nome:
                cliente.nome = cliente_nome
            if cliente_telefone and cliente.telefone != cliente_telefone:
                cliente.telefone = cliente_telefone
            cliente.save()
        
        # Criar agendamento
        agendamento_service = AgendamentoService(empresa)
        sucesso, mensagem, agendamento = agendamento_service.criar_agendamento(
            cliente, funcionario, servico, data_hora_inicio
        )
        
        if sucesso:
            return JsonResponse({
                "success": True,
                "message": mensagem,
                "agendamento_id": agendamento.id,
                "data_hora": agendamento.data_hora_inicio.strftime("%d/%m/%Y às %H:%M")
            })
        else:
            return JsonResponse({"error": mensagem}, status=400)
            
    except Exception as e:
        return JsonResponse({"error": f"Erro interno: {str(e)}"}, status=500)


def adicionar_fila_espera(request, empresa_id):
    """View para adicionar cliente à fila de espera"""
    if request.method != "POST":
        return JsonResponse({"error": "Método não permitido"}, status=405)
    
    try:
        data = json.loads(request.body)
        
        # Extrair dados
        cliente_nome = data.get("cliente_nome")
        cliente_email = data.get("cliente_email")
        cliente_telefone = data.get("cliente_telefone")
        servico_id = data.get("servico_id")
        funcionario_id = data.get("funcionario_id")  # Opcional
        data_desejada_str = data.get("data_desejada")
        horario_desejado_str = data.get("horario_desejado")  # Opcional
        flexivel_data = data.get("flexivel_data", True)
        flexivel_horario = data.get("flexivel_horario", True)
        observacoes = data.get("observacoes", "")
        
        # Validar dados obrigatórios
        if not all([cliente_nome, cliente_email, data_desejada_str]):
            return JsonResponse({"error": "Dados obrigatórios não fornecidos"}, status=400)
        
        # Obter objetos
        empresa = get_object_or_404(Empresa, id=empresa_id, ativo=True)
        servico = None
        funcionario_preferido = None
        
        if servico_id:
            servico = get_object_or_404(Servico, id=servico_id, empresa=empresa)
        
        if funcionario_id:
            funcionario_preferido = get_object_or_404(Funcionario, id=funcionario_id, empresa=empresa)
        
        # Converter data
        data_desejada = datetime.strptime(data_desejada_str, "%Y-%m-%d").date()
        
        # Converter horário se fornecido
        horario_desejado = None
        if horario_desejado_str:
            horario_desejado = datetime.strptime(horario_desejado_str, "%H:%M").time()
        
        # Buscar ou criar cliente
        cliente, created = Cliente.objects.get_or_create(
            email=cliente_email,
            defaults={
                "nome": cliente_nome,
                "telefone": cliente_telefone or ""
            }
        )
        
        # Adicionar à fila de espera
        fila_service = FilaEsperaService(empresa)
        sucesso, mensagem, fila_entry = fila_service.adicionar_a_fila(
            cliente=cliente,
            data_desejada=data_desejada,
            servico=servico,
            funcionario_preferido=funcionario_preferido,
            horario_desejado=horario_desejado,
            flexivel_data=flexivel_data,
            flexivel_horario=flexivel_horario,
            observacoes=observacoes
        )
        
        if sucesso:
            return JsonResponse({
                "success": True,
                "message": mensagem,
                "fila_id": fila_entry.id
            })
        else:
            return JsonResponse({"error": mensagem}, status=400)
            
    except Exception as e:
        return JsonResponse({"error": f"Erro interno: {str(e)}"}, status=500)


def meus_agendamentos(request):
    """View para listar agendamentos de um cliente (por email)"""
    email = request.GET.get("email")
    if not email:
        return render(request, "agendamentos/meus_agendamentos.html", {
            "titulo": "Meus Agendamentos",
            "agendamentos": [],
            "email": ""
        })
    
    try:
        cliente = Cliente.objects.get(email=email)
        agendamentos = cliente.get_agendamentos_ativos()
        
        context = {
            "titulo": "Meus Agendamentos",
            "agendamentos": agendamentos,
            "cliente": cliente,
            "email": email
        }
        return render(request, "agendamentos/meus_agendamentos.html", context)
        
    except Cliente.DoesNotExist:
        context = {
            "titulo": "Meus Agendamentos",
            "agendamentos": [],
            "email": email,
            "erro": "Nenhum agendamento encontrado para este e-mail."
        }
        return render(request, "agendamentos/meus_agendamentos.html", context)

@login_required
def agenda_barbeiro(request, ano=None, mes=None, dia=None):
    """
    View para a agenda do barbeiro logado.
    Exibe os agendamentos para a semana da data selecionada ou do dia atual.
    """
    try:
        funcionario = request.user.funcionario
    except Funcionario.DoesNotExist:
        messages.error(request, "Você não está associado a um funcionário.")
        return redirect("agendamentos:home")

    # Determinar a data base para a semana
    if ano and mes and dia:
        try:
            data_base = date(int(ano), int(mes), int(dia))
        except ValueError:
            messages.error(request, "Data inválida.")
            data_base = timezone.localdate()
    else:
        data_base = timezone.localdate()

    # Encontrar o início da semana (domingo)
    # weekday() retorna 0 para segunda, 6 para domingo
    # Para começar a semana no domingo, ajustamos:
    # Se for domingo (6), subtrai 0 dias
    # Se for segunda (0), subtrai 1 dia
    # ...
    # Se for sábado (5), subtrai 6 dias
    inicio_semana = data_base - timedelta(days=(data_base.weekday() + 1) % 7)
    
    # Ajuste para começar a semana na segunda-feira (se preferir)
    # inicio_semana = data_base - timedelta(days=data_base.weekday())

    fim_semana = inicio_semana + timedelta(days=6)

    agendamentos_semana = funcionario.get_agendamentos_periodo(
        inicio_semana, fim_semana
    )

    # Organizar agendamentos por dia da semana
    agenda_semanal = { (inicio_semana + timedelta(days=i)): [] for i in range(7) }
    for agendamento in agendamentos_semana:
        agenda_semanal[agendamento.data_hora_inicio.date()].append(agendamento)
    
    # Preparar datas para navegação
    semana_anterior = data_base - timedelta(weeks=1)
    proxima_semana = data_base + timedelta(weeks=1)

    context = {
        "titulo": f"Agenda Semanal de {funcionario.nome}",
        "funcionario": funcionario,
        "agenda_semanal": agenda_semanal,
        "inicio_semana": inicio_semana,
        "fim_semana": fim_semana,
        "semana_anterior": semana_anterior,
        "proxima_semana": proxima_semana,
    }
    return render(request, "agendamentos/agenda_barbeiro.html", context)

@login_required
@require_http_methods(["POST"])
def cancelar_agendamento(request, agendamento_id):
    """
    Permite ao barbeiro cancelar um agendamento.
    Envia notificação via WhatsApp ao cliente após o cancelamento.
    """
    try:
        funcionario = request.user.funcionario
    except Funcionario.DoesNotExist:
        return JsonResponse({"success": False, "error": "Funcionário não encontrado."})

    try:
        agendamento = Agendamento.objects.get(id=agendamento_id, funcionario=funcionario)
        agendamento.status = "cancelado"
        agendamento.save()

        # Enviar notificação via WhatsApp ao cliente
        mensagem = (
            f"Olá {agendamento.cliente.nome}, seu horário com {agendamento.funcionario.nome} "
            f"no dia {agendamento.data_hora_inicio.strftime('%d/%m/%Y')} às "
            f"{agendamento.data_hora_inicio.strftime('%H:%M')} foi cancelado."
        )
        numero_cliente = f"whatsapp:+55{''.join(filter(str.isdigit, agendamento.cliente.telefone))}"
        enviar_whatsapp(mensagem, numero_cliente)

        messages.success(request, "Agendamento cancelado com sucesso!")
        return JsonResponse({"success": True, "message": "Agendamento cancelado com sucesso!"})

    except Agendamento.DoesNotExist:
        return JsonResponse({
            "success": False,
            "error": "Agendamento não encontrado ou você não tem permissão para cancelá-lo."
        })
    except Exception as e:
        return JsonResponse({
            "success": False,
            "error": f"Erro ao cancelar agendamento: {str(e)}"
        })


@login_required
@require_http_methods(["GET", "POST"] )
def agendar_para_cliente(request):
    """
    Permite ao barbeiro agendar um serviço para um cliente.
    """
    try:
        funcionario = request.user.funcionario
    except Funcionario.DoesNotExist:
        messages.error(request, "Você não está associado a um funcionário.")
        return redirect("agendamentos:home")

    empresa = funcionario.empresa
    servicos_funcionario = Servico.objects.filter(funcionarios=funcionario, ativo=True)

    if request.method == "POST":
        cliente_nome = request.POST.get("cliente_nome")
        cliente_email = request.POST.get("cliente_email")
        cliente_telefone = request.POST.get("cliente_telefone")
        servico_id = request.POST.get("servico")
        data_agendamento_str = request.POST.get("data_agendamento")
        horario_agendamento_str = request.POST.get("horario_agendamento")

        if not all([cliente_nome, cliente_email, cliente_telefone, servico_id, data_agendamento_str, horario_agendamento_str]):
            messages.error(request, "Todos os campos obrigatórios devem ser preenchidos.")
            # Renderiza o formulário novamente com os dados preenchidos
            context = {
                "titulo": "Agendar para Cliente",
                "funcionario": funcionario,
                "servicos": servicos_funcionario,
                "cliente_nome": cliente_nome,
                "cliente_email": cliente_email,
                "cliente_telefone": cliente_telefone,
                "servico_id_selecionado": servico_id,
                "data_agendamento_str": data_agendamento_str,
                "horario_agendamento_str": horario_agendamento_str,
            }
            return render(request, "agendamentos/agendar_para_cliente.html", context)

        try:
            servico = get_object_or_404(Servico, id=servico_id, empresa=empresa)
            
            # Buscar ou criar cliente
            cliente, created = Cliente.objects.get_or_create(
                email=cliente_email,
                defaults={
                    "nome": cliente_nome,
                    "telefone": cliente_telefone
                }
            )
            if not created:
                # Atualiza nome e telefone se o cliente já existe
                cliente.nome = cliente_nome
                cliente.telefone = cliente_telefone
                cliente.save()

            # Combinar data e hora
            data_agendamento = datetime.strptime(data_agendamento_str, "%Y-%m-%d")
            horario_agendamento = datetime.strptime(horario_agendamento_str, "%H:%M")
            data_hora_inicio = datetime.combine(data_agendamento.date(), horario_agendamento.time())
            data_hora_inicio = timezone.make_aware(data_hora_inicio) # Garante que é aware

            agendamento_service = AgendamentoService(empresa)
            success, msg, agendamento = agendamento_service.criar_agendamento(
                cliente=cliente,
                funcionario=funcionario,
                servico=servico,
                data_hora_inicio=data_hora_inicio
            )

            if success:
                messages.success(request, msg)
                return redirect("agendamentos:agenda_barbeiro")
            else:
                messages.error(request, msg)

        except ValueError:
            messages.error(request, "Formato de data/hora inválido.")
        except Exception as e:
            messages.error(request, f"Erro ao agendar: {str(e)}")

    context = {
        "titulo": "Agendar para Cliente",
        "funcionario": funcionario,
        "servicos": servicos_funcionario,
    }
    return render(request, "agendamentos/agendar_para_cliente.html", context)


# Views de autenticação (login/logout)

def login_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, "Login realizado com sucesso!")
            # Redirecionar para a agenda do barbeiro se for um funcionário
            if hasattr(user, "funcionario"):
                return redirect("agendamentos:agenda_barbeiro")
            else:
                # Redirecionar para a home para clientes ou outros usuários
                return redirect("agendamentos:home")
        else:
            messages.error(request, "Nome de usuário ou senha inválidos.")
    return render(request, "agendamentos/login.html", {"titulo": "Login"})


@login_required
def logout_view(request):
    logout(request)
    messages.info(request, "Você foi desconectado.")
    return redirect("agendamentos:home")