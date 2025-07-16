from django.contrib import admin
from .models import Agendamento, FilaEspera

@admin.register(Agendamento)
class AgendamentoAdmin(admin.ModelAdmin):
    list_display = ["cliente", "funcionario", "servico", "data_hora_inicio", "status", "empresa"]
    list_filter = ["status", "empresa", "funcionario", "servico", "data_hora_inicio"]
    search_fields = ["cliente__nome", "funcionario__nome", "servico__nome"]
    raw_id_fields = ["empresa", "cliente", "funcionario", "servico"]
    date_hierarchy = "data_hora_inicio"

@admin.register(FilaEspera)
class FilaEsperaAdmin(admin.ModelAdmin):
    list_display = ["cliente", "empresa", "servico", "data_desejada", "notificado", "ativo"]
    list_filter = ["empresa", "servico", "notificado", "ativo", "data_desejada"]
    search_fields = ["cliente__nome", "servico__nome"]
    raw_id_fields = ["empresa", "cliente", "servico", "funcionario_preferido"]
