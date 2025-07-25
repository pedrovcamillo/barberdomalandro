# Generated by Django 5.2.3 on 2025-06-15 00:55

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('funcionarios', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='funcionario',
            unique_together=set(),
        ),
        migrations.AddField(
            model_name='funcionario',
            name='user',
            field=models.OneToOneField(blank=True, help_text='Conta de usuário para login do funcionário', null=True, on_delete=django.db.models.deletion.CASCADE, related_name='funcionario', to=settings.AUTH_USER_MODEL, verbose_name='Usuário'),
        ),
        migrations.AlterField(
            model_name='disponibilidadefuncionario',
            name='tipo',
            field=models.CharField(choices=[('trabalho', 'Trabalho'), ('almoco', 'Almoço'), ('pausa', 'Pausa'), ('folga', 'Folga'), ('outro', 'Outro')], default='trabalho', max_length=20, verbose_name='Tipo'),
        ),
    ]
