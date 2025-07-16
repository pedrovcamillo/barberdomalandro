from django.contrib import admin
from .models import Empresa, ParametrosEmpresa

@admin.register(Empresa)
class EmpresaAdmin(admin.ModelAdmin):
    list_display = ["nome", "cnpj", "telefone", "ativo", "data_criacao"]
    list_filter = ["ativo", "data_criacao"]
    search_fields = ["nome", "cnpj", "email"]

@admin.register(ParametrosEmpresa)
class ParametrosEmpresaAdmin(admin.ModelAdmin):
    list_display = ["empresa", "horario_abertura", "horario_fechamento", "intervalo_agendamento"]
