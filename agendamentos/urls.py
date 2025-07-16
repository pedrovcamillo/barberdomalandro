from django.urls import path
from . import views

app_name = "agendamentos"

urlpatterns = [
    # URLs para clientes
    path("", views.home, name="home"),
    path("empresa/<int:empresa_id>/", views.empresa_detail, name="empresa_detail"),
    path("empresa/<int:empresa_id>/verificar_disponibilidade/", views.verificar_disponibilidade, name="verificar_disponibilidade"),
    path("empresa/<int:empresa_id>/criar_agendamento/", views.criar_agendamento, name="criar_agendamento"),
    path("empresa/<int:empresa_id>/adicionar_fila_espera/", views.adicionar_fila_espera, name="adicionar_fila_espera"),
    path("meus_agendamentos/", views.meus_agendamentos, name="meus_agendamentos"),

    # URLs para funcionários (barbeiros)
    path("barbeiro/agenda/", views.agenda_barbeiro, name="agenda_barbeiro"),
    path("barbeiro/agenda/<int:ano>/<int:mes>/<int:dia>/", views.agenda_barbeiro, name="agenda_barbeiro_data"),
    path("barbeiro/agendar_para_cliente/", views.agendar_para_cliente, name="agendar_para_cliente"),
    path("barbeiro/cancelar_agendamento/<int:agendamento_id>/", views.cancelar_agendamento, name="cancelar_agendamento"), 

    # URLs de autenticação
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
]
