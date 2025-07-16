from django.contrib import admin
from .models import Cliente

@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ["nome", "email", "telefone", "ativo", "data_criacao"]
    list_filter = ["ativo", "data_criacao"]
    search_fields = ["nome", "email", "telefone"]
    raw_id_fields = ["user"] 
