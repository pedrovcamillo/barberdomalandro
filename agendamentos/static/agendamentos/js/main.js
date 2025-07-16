document.addEventListener('DOMContentLoaded', function() {
    console.log('Sistema de Agendamentos carregado!');

    // Variáveis globais para armazenar dados selecionados
    let selectedSlot = null;
    let selectedServico = null;
    let selectedFuncionario = null;
    let selectedData = null;

    // Elementos do DOM
    const servicoSelect = document.getElementById('servicoSelect');
    const funcionarioSelect = document.getElementById('funcionarioSelect');
    const dataSelect = document.getElementById('dataSelect');
    const verificarBtn = document.getElementById('verificarDisponibilidadeBtn');
    const horariosDiv = document.getElementById('horariosDisponiveis');
    const slotsContainer = document.getElementById('slotsContainer');
    const confirmarBtn = document.getElementById('confirmarAgendamentoBtn');
    const filaBtn = document.getElementById('entrarFilaEsperaBtn');

    // Configurar data mínima (hoje)
    if (dataSelect) {
        const hoje = new Date();
        const dataMinima = hoje.toISOString().split('T')[0];
        dataSelect.min = dataMinima;
    }

    // Event listeners
    if (verificarBtn) {
        verificarBtn.addEventListener('click', verificarDisponibilidade);
    }

    if (confirmarBtn) {
        confirmarBtn.addEventListener('click', abrirModalConfirmacao);
    }

    if (filaBtn) {
        filaBtn.addEventListener('click', abrirModalFilaEspera);
    }

    // Botão de finalizar agendamento no modal
    const finalizarAgendamentoBtn = document.getElementById('finalizarAgendamentoBtn');
    if (finalizarAgendamentoBtn) {
        finalizarAgendamentoBtn.addEventListener('click', finalizarAgendamento);
    }

    // Botão de finalizar fila de espera no modal
    const finalizarFilaEsperaBtn = document.getElementById('finalizarFilaEsperaBtn');
    if (finalizarFilaEsperaBtn) {
        finalizarFilaEsperaBtn.addEventListener('click', finalizarFilaEspera);
    }

    function verificarDisponibilidade() {
        const servicoId = servicoSelect.value;
        const funcionarioId = funcionarioSelect.value;
        const data = dataSelect.value;

        // Validar seleções
        if (!servicoId || !funcionarioId || !data) {
            alert('Por favor, selecione o serviço, profissional e data.');
            return;
        }

        // Armazenar seleções
        selectedServico = servicoSelect.options[servicoSelect.selectedIndex];
        selectedFuncionario = funcionarioSelect.options[funcionarioSelect.selectedIndex];
        selectedData = data;

        // Mostrar loading
        verificarBtn.disabled = true;
        verificarBtn.textContent = 'Verificando...';

        // Fazer requisição para verificar disponibilidade
        fetch(`/empresa/${empresaId}/verificar_disponibilidade/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify({
                funcionario_id: funcionarioId,
                servico_id: servicoId,
                data: data
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                mostrarHorarios(data.horarios);
                document.getElementById('selectedFuncionario').textContent = data.funcionario;
                document.getElementById('selectedServico').textContent = data.servico;
                document.getElementById('selectedData').textContent = data.data;
            } else {
                alert('Erro: ' + data.error);
            }
        })
        .catch(error => {
            console.error('Erro:', error);
            alert('Erro ao verificar disponibilidade. Tente novamente.');
        })
        .finally(() => {
            verificarBtn.disabled = false;
            verificarBtn.textContent = 'Verificar Disponibilidade';
        });
    }

    function mostrarHorarios(horarios) {
        slotsContainer.innerHTML = '';
        
        if (horarios.length === 0) {
            slotsContainer.innerHTML = '<div class="alert alert-warning">Nenhum horário disponível para esta data.</div>';
            filaBtn.style.display = 'block';
            confirmarBtn.style.display = 'none';
        } else {
            horarios.forEach(horario => {
                const slotElement = document.createElement('a');
                slotElement.href = '#';
                slotElement.className = 'list-group-item list-group-item-action';
                slotElement.textContent = horario.display;
                slotElement.dataset.datetime = horario.datetime;
                
                slotElement.addEventListener('click', function(e) {
                    e.preventDefault();
                    selecionarSlot(this);
                });
                
                slotsContainer.appendChild(slotElement);
            });
            filaBtn.style.display = 'none';
            confirmarBtn.style.display = 'none';
        }
        
        horariosDiv.style.display = 'block';
        selectedSlot = null;
    }

    function selecionarSlot(slotElement) {
        // Remover seleção anterior
        document.querySelectorAll('#slotsContainer .list-group-item').forEach(item => {
            item.classList.remove('active');
        });
        
        // Selecionar novo slot
        slotElement.classList.add('active');
        selectedSlot = slotElement;
        confirmarBtn.style.display = 'block';
    }

    function abrirModalConfirmacao() {
        if (!selectedSlot) {
            alert('Por favor, selecione um horário.');
            return;
        }

        // Preencher dados no modal
        document.getElementById('modalServico').textContent = selectedServico.textContent;
        document.getElementById('modalFuncionario').textContent = selectedFuncionario.textContent;
        
        const dataHora = new Date(selectedSlot.dataset.datetime);
        document.getElementById('modalDataHora').textContent = dataHora.toLocaleString('pt-BR');
        
        const preco = selectedServico.dataset.preco;
        document.getElementById('modalPreco').textContent = parseFloat(preco).toFixed(2);

        // Abrir modal
        $('#confirmarAgendamentoModal').modal('show');
    }

    function abrirModalFilaEspera() {
        $('#filaEsperaModal').modal('show');
    }

    function finalizarAgendamento() {
        const nome = document.getElementById('clienteNome').value;
        const email = document.getElementById('clienteEmail').value;
        const telefone = document.getElementById('clienteTelefone').value;

        if (!nome || !email) {
            alert('Por favor, preencha nome e e-mail.');
            return;
        }

        // Desabilitar botão
        const btn = document.getElementById('finalizarAgendamentoBtn');
        btn.disabled = true;
        btn.textContent = 'Agendando...';

        // Fazer requisição
        fetch(`/empresa/${empresaId}/criar_agendamento/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify({
                cliente_nome: nome,
                cliente_email: email,
                cliente_telefone: telefone,
                funcionario_id: funcionarioSelect.value,
                servico_id: servicoSelect.value,
                data_hora: selectedSlot.dataset.datetime
            })
        })
        .then(response => response.json())
        .then(data => {
             if (data.success) {
                alert("Agendamento realizado com sucesso para " + data.data_hora + "!");
                $("#confirmarAgendamentoModal").modal("hide");
                
                verificarDisponibilidade(); 
                limparFormulario();

            } else {
                alert("Erro: " + data.error);
            }
        })
        .catch(error => {
            console.error('Erro:', error);
            alert('Erro ao criar agendamento. Tente novamente.');
        })
        .finally(() => {
            btn.disabled = false;
            btn.textContent = 'Agendar';
        });
    }

    function finalizarFilaEspera() {
        const nome = document.getElementById('filaClienteNome').value;
        const email = document.getElementById('filaClienteEmail').value;
        const telefone = document.getElementById('filaClienteTelefone').value;
        const observacoes = document.getElementById('filaObservacoes').value;
        const flexivelData = document.getElementById('flexivelData').checked;
        const flexivelHorario = document.getElementById('flexivelHorario').checked;

        if (!nome || !email) {
            alert('Por favor, preencha nome e e-mail.');
            return;
        }

        // Desabilitar botão
        const btn = document.getElementById('finalizarFilaEsperaBtn');
        btn.disabled = true;
        btn.textContent = 'Adicionando...';

        // Fazer requisição
        fetch(`/empresa/${empresaId}/adicionar_fila_espera/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify({
                cliente_nome: nome,
                cliente_email: email,
                cliente_telefone: telefone,
                servico_id: servicoSelect.value,
                funcionario_id: funcionarioSelect.value,
                data_desejada: selectedData,
                observacoes: observacoes,
                flexivel_data: flexivelData,
                flexivel_horario: flexivelHorario
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                alert('Você foi adicionado à fila de espera! Entraremos em contato quando houver disponibilidade.');
                $('#filaEsperaModal').modal('hide');
                limparFormulario();
            } else {
                alert('Erro: ' + data.error);
            }
        })
        .catch(error => {
            console.error('Erro:', error);
            alert('Erro ao adicionar à fila de espera. Tente novamente.');
        })
        .finally(() => {
            btn.disabled = false;
            btn.textContent = 'Entrar na Fila';
        });
    }

    function limparFormulario() {
        // Limpar seleções
        servicoSelect.value = '';
        funcionarioSelect.value = '';
        dataSelect.value = '';
        
        // Esconder horários
        horariosDiv.style.display = 'none';
        
        // Limpar campos dos modais
        document.getElementById('clienteNome').value = '';
        document.getElementById('clienteEmail').value = '';
        document.getElementById('clienteTelefone').value = '';
        document.getElementById('filaClienteNome').value = '';
        document.getElementById('filaClienteEmail').value = '';
        document.getElementById('filaClienteTelefone').value = '';
        document.getElementById('filaObservacoes').value = '';
        
        // Reset variáveis
        selectedSlot = null;
        selectedServico = null;
        selectedFuncionario = null;
        selectedData = null;
    }

    // Função para obter CSRF token
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }
});
