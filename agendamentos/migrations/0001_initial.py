# Generated by Django 5.2.3 on 2025-06-14 19:32

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('clientes', '0001_initial'),
        ('core', '0001_initial'),
        ('funcionarios', '0001_initial'),
        ('servicos', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Agendamento',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('data_hora_inicio', models.DateTimeField(verbose_name='Data e Hora de Início')),
                ('data_hora_fim', models.DateTimeField(verbose_name='Data e Hora de Fim')),
                ('status', models.CharField(choices=[('pendente', 'Pendente'), ('confirmado', 'Confirmado'), ('em_andamento', 'Em Andamento'), ('concluido', 'Concluído'), ('cancelado', 'Cancelado'), ('nao_compareceu', 'Não Compareceu')], default='pendente', max_length=20, verbose_name='Status')),
                ('preco_cobrado', models.DecimalField(decimal_places=2, help_text='Preço efetivamente cobrado pelo serviço', max_digits=10, verbose_name='Preço Cobrado')),
                ('observacoes', models.TextField(blank=True, help_text='Observações sobre o agendamento', verbose_name='Observações')),
                ('data_criacao', models.DateTimeField(auto_now_add=True, verbose_name='Data de Criação')),
                ('data_atualizacao', models.DateTimeField(auto_now=True, verbose_name='Última Atualização')),
                ('cancelado_por', models.CharField(blank=True, help_text='Quem cancelou o agendamento (cliente, funcionário, sistema)', max_length=100, verbose_name='Cancelado Por')),
                ('motivo_cancelamento', models.TextField(blank=True, verbose_name='Motivo do Cancelamento')),
                ('cliente', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='agendamentos', to='clientes.cliente', verbose_name='Cliente')),
                ('empresa', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='agendamentos', to='core.empresa', verbose_name='Empresa')),
                ('funcionario', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='agendamentos', to='funcionarios.funcionario', verbose_name='Funcionário')),
                ('servico', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='agendamentos', to='servicos.servico', verbose_name='Serviço')),
            ],
            options={
                'verbose_name': 'Agendamento',
                'verbose_name_plural': 'Agendamentos',
                'ordering': ['-data_hora_inicio'],
            },
        ),
        migrations.CreateModel(
            name='FilaEspera',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('data_desejada', models.DateField(verbose_name='Data Desejada')),
                ('horario_desejado', models.TimeField(blank=True, help_text='Horário preferido (opcional)', null=True, verbose_name='Horário Desejado')),
                ('flexivel_data', models.BooleanField(default=True, help_text='Aceita outras datas próximas', verbose_name='Flexível com Data')),
                ('flexivel_horario', models.BooleanField(default=True, help_text='Aceita outros horários', verbose_name='Flexível com Horário')),
                ('prioridade', models.PositiveIntegerField(default=1, help_text='Menor número = maior prioridade', verbose_name='Prioridade')),
                ('data_solicitacao', models.DateTimeField(auto_now_add=True, verbose_name='Data da Solicitação')),
                ('notificado', models.BooleanField(default=False, verbose_name='Notificado')),
                ('data_notificacao', models.DateTimeField(blank=True, null=True, verbose_name='Data da Notificação')),
                ('ativo', models.BooleanField(default=True, verbose_name='Ativo')),
                ('observacoes', models.TextField(blank=True, verbose_name='Observações')),
                ('cliente', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='fila_espera', to='clientes.cliente', verbose_name='Cliente')),
                ('empresa', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='fila_espera', to='core.empresa', verbose_name='Empresa')),
                ('funcionario_preferido', models.ForeignKey(blank=True, help_text='Funcionário preferido (opcional)', null=True, on_delete=django.db.models.deletion.CASCADE, related_name='fila_espera', to='funcionarios.funcionario', verbose_name='Funcionário Preferido')),
                ('servico', models.ForeignKey(blank=True, help_text='Serviço desejado (opcional)', null=True, on_delete=django.db.models.deletion.CASCADE, related_name='fila_espera', to='servicos.servico', verbose_name='Serviço')),
            ],
            options={
                'verbose_name': 'Fila de Espera',
                'verbose_name_plural': 'Fila de Espera',
                'ordering': ['prioridade', 'data_solicitacao'],
            },
        ),
    ]
