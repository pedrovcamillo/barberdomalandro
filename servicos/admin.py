from django.contrib import admin
from .models import Servico, FuncionarioServico

@admin.register(Servico)
class ServicoAdmin(admin.ModelAdmin):
    list_display = ["nome", "empresa", "duracao", "preco", "ativo"]
    list_filter = ["empresa", "ativo"]
    search_fields = ["nome", "descricao"]
    raw_id_fields = ["empresa"]

@admin.register(FuncionarioServico)
class FuncionarioServicoAdmin(admin.ModelAdmin):
    list_display = ["funcionario", "servico", "preco_especifico", "duracao_especifica"]
    list_filter = ["funcionario", "servico"]
    raw_id_fields = ["funcionario", "servico"]
