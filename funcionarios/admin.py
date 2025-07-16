from django.contrib import admin
from .models import Funcionario, DisponibilidadeFuncionario

@admin.register(Funcionario)
class FuncionarioAdmin(admin.ModelAdmin):
    list_display = ["nome", "empresa", "cargo", "email", "ativo"]
    list_filter = ["empresa", "cargo", "ativo"]
    search_fields = ["nome", "email", "telefone"]
    raw_id_fields = ["empresa"]

@admin.register(DisponibilidadeFuncionario)
class DisponibilidadeFuncionarioAdmin(admin.ModelAdmin):
    list_display = ["funcionario", "data", "horario_inicio", "horario_fim", "tipo"]
    list_filter = ["funcionario", "data", "tipo"]
    search_fields = ["funcionario__nome"]
    raw_id_fields = ["funcionario"]
