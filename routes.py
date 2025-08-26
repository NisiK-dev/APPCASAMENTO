<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Confirmar Presença - Kelly & Nísio</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/@fortawesome/fontawesome-free@6.4.0/css/all.min.css">
    <style>
        .fixed-background {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: linear-gradient(135deg, #ff9a9e 0%, #fecfef 50%, #fecfef 100%);
            z-index: -1;
        }
        
        .rsvp-container {
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            min-height: 100vh;
        }

        /* Estilos para seleção individual de convidados */
        .guest-selection-card {
            border: 2px solid #e9ecef;
            border-radius: 12px;
            padding: 20px;
            margin-bottom: 15px;
            transition: all 0.3s ease;
            cursor: pointer;
            background: white;
        }

        .guest-selection-card:hover {
            border-color: #007bff;
            box-shadow: 0 4px 12px rgba(0,123,255,0.15);
            transform: translateY(-2px);
        }

        .guest-info {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 15px;
        }

        .guest-name {
            font-size: 1.25rem;
            font-weight: 600;
            color: #2c3e50;
            margin: 0;
        }

        .status-badge {
            padding: 6px 12px;
            border-radius: 20px;
            font-size: 0.85rem;
            font-weight: 500;
        }

        .status-confirmed { background: #d4edda; color: #155724; }
        .status-pending { background: #fff3cd; color: #856404; }
        .status-declined { background: #f8d7da; color: #721c24; }

        .guest-details {
            color: #6c757d;
            font-size: 0.95rem;
            margin-bottom: 15px;
        }

        .select-guest-btn {
            background: linear-gradient(135deg, #007bff, #0056b3);
            border: none;
            color: white;
            padding: 10px 25px;
            border-radius: 25px;
            font-weight: 500;
            transition: all 0.3s ease;
        }

        .select-guest-btn:hover {
            background: linear-gradient(135deg, #0056b3, #004085);
            transform: scale(1.05);
        }

        /* Estilos existentes do RSVP mantidos */
        .rsvp-options-container {
            display: flex;
            gap: 15px;
            margin-bottom: 20px;
        }

        .rsvp-option {
            flex: 1;
            border: 2px solid #e9ecef;
            border-radius: 12px;
            padding: 20px;
            cursor: pointer;
            transition: all 0.3s ease;
            background: white;
        }

        .rsvp-option:hover {
            border-color: #007bff;
            box-shadow: 0 4px 12px rgba(0,123,255,0.15);
        }

        .rsvp-option.selected {
            border-color: #28a745;
            background: #f8fff9;
            box-shadow: 0 0 0 3px rgba(40,167,69,0.1);
        }

        .option-content {
            display: flex;
            align-items: center;
            gap: 15px;
        }

        .option-icon {
            width: 50px;
            height: 50px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.25rem;
            color: white;
        }

        .option-icon.success { background: #28a745; }
        .option-icon.danger { background: #dc3545; }

        .option-text h6 {
            margin: 0 0 5px 0;
            font-weight: 600;
            color: #2c3e50;
        }

        .option-text p {
            margin: 0;
            color: #6c757d;
            font-size: 0.9rem;
        }

        @media (max-width: 768px) {
            .rsvp-options-container {
                flex-direction: column;
            }
            
            .guest-info {
                flex-direction: column;
                align-items: flex-start;
                gap: 10px;
            }
        }
    </style>
</head>
<body>
    <div class="fixed-background"></div>

    <div class="rsvp-container">
        <div class="text-center mb-5">
            <h2>
                <i class="fas fa-calendar-check me-2"></i>
                Confirme sua Presença
            </h2>
            <p class="lead text-dark">
                Por favor, confirme se você poderá comparecer ao nosso casamento
            </p>
        </div>

        <!-- Step 1: Search Guest -->
        <div class="card mb-4" id="searchStep">
            <div class="card-header">
                <h5 class="mb-0">
                    <i class="fas fa-search me-2"></i>
                    Encontre seu nome na lista
                </h5>
            </div>
            <div class="card-body">
                <div class="mb-3">
                    <label for="guestSearch" class="form-label">Digite seu nome</label>
                    <input type="text" class="form-control form-control-lg" id="guestSearch" 
                           placeholder="Ex: João Silva" autocomplete="on" minlength="3">
                    <div class="form-text">Digite pelo menos 3 caracteres para buscar</div>
                </div>
            </div>
            
            <!-- Loading -->
            <div id="searchLoading" class="text-center p-4" style="display: none;">
                <i class="fas fa-spinner fa-spin fa-2x text-primary"></i>
                <p class="mt-2">Procurando...</p>
            </div>
            
            <!-- Individual Guest Selection -->
            <div id="guestSelectionResults" style="display: none;">
                <div class="card-header border-top">
                    <h6 class="mb-0 text-primary">
                        <i class="fas fa-users me-2"></i>
                        Selecione seu nome:
                    </h6>
                </div>
                <div class="card-body">
                    <div id="individualGuestsList"></div>
                </div>
            </div>
        </div>

        <!-- Step 2: Confirm Guests -->
        <div class="card" id="confirmStep" style="display: none;">
            <div class="card-header">
                <h5 class="mb-0">
                    <i class="fas fa-check-circle me-2"></i>
                    Confirme a presença
                </h5>
            </div>
            <div class="card-body">
                <div class="alert alert-info mb-4">
                    <i class="fas fa-info-circle me-2"></i>
                    <strong id="selectedGuestName"></strong>, confirme sua presença e a de sua família:
                </div>
                
                <form id="rsvpForm" method="POST" action="/confirm_rsvp">
                    <div id="selectedGuestsList"></div>

                    <div class="row mt-4">
                        <div class="col-md-6 mb-3">
                            <button type="button" class="btn btn-outline-secondary w-100" onclick="goBackToSearch()">
                                <i class="fas fa-arrow-left me-2"></i>
                                Voltar à Busca
                            </button>
                        </div>
                        <div class="col-md-6 mb-3">
                            <button type="button" class="btn btn-success btn-lg w-100" onclick="confirmRSVP()">
                                <i class="fas fa-check me-2"></i>
                                Enviar Resposta
                            </button>
                        </div>
                    </div>
                </form>
            </div>
        </div>

        <!-- Help Section -->
        <div class="text-center mt-5">
            <div class="alert alert-info">
                <i class="fas fa-info-circle me-2"></i>
                <p class="mb-0">
                    Se você não encontrar seu nome na lista, entre em contato conosco.
                    Você pode confirmar a presença de toda sua família de uma vez.
                </p>
            </div>
        </div>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    <script>
        var selectedGuests = [];
        var searchTimeout;

        // Função para debug
        function logDebug(message, data = null) {
            console.log(`[RSVP Debug] ${message}`, data || '');
        }

        document.getElementById('guestSearch').addEventListener('input', function () {
            var query = this.value.trim();
            clearTimeout(searchTimeout);

            logDebug(`Input detectado: "${query}"`);

            // Mínimo 3 caracteres
            if (query.length < 3) {
                document.getElementById('guestSelectionResults').style.display = 'none';
                logDebug('Query muito curta, ocultando resultados');
                return;
            }

            // Mostrar loading
            document.getElementById('searchLoading').style.display = 'block';
            document.getElementById('guestSelectionResults').style.display = 'none';
            logDebug('Mostrando loading...');

            // Debounce de 300ms
            searchTimeout = setTimeout(function () {
                logDebug(`Executando busca para: "${query}"`);
                
                var formData = new FormData();
                formData.append('name', query);

                fetch('/search_guest_individual', {
                    method: 'POST',
                    body: formData,
                    headers: {
                        'X-Requested-With': 'XMLHttpRequest'
                    }
                })
                .then(response => {
                    logDebug(`Response status: ${response.status}`);
                    
                    if (!response.ok) {
                        throw new Error(`Erro HTTP: ${response.status} - ${response.statusText}`);
                    }
                    return response.text(); // Primeiro como text para debug
                })
                .then(text => {
                    logDebug('Response text:', text);
                    
                    let data;
                    try {
                        data = JSON.parse(text);
                    } catch (e) {
                        throw new Error(`Erro ao parsear JSON: ${e.message}. Response: ${text}`);
                    }
                    
                    document.getElementById('searchLoading').style.display = 'none';
                    logDebug('Dados recebidos:', data);

                    if (data.success) {
                        if (data.guests && data.guests.length > 0) {
                            logDebug(`${data.guests.length} convidados encontrados`);
                            displayIndividualGuests(data.guests);
                        } else {
                            logDebug('Nenhum convidado encontrado');
                            displayNoResults(data.message || 'Nenhum convidado encontrado');
                        }
                    } else {
                        throw new Error(data.error || 'Erro desconhecido na busca');
                    }
                })
                .catch(error => {
                    logDebug('ERRO na busca:', error);
                    document.getElementById('searchLoading').style.display = 'none';
                    displaySearchError(error.message);
                });
            }, 300);
        });

        function displayIndividualGuests(guests) {
            logDebug('Exibindo convidados:', guests);
            
            var guestsList = document.getElementById('individualGuestsList');
            var html = '';

            if (guests.length === 1) {
                logDebug('Apenas 1 convidado encontrado, selecionando automaticamente');
                selectSpecificGuest(guests[0].id, null);
                return;
            }

            guests.forEach((guest, index) => {
                logDebug(`Processando convidado ${index + 1}:`, guest);
                
                var statusClass = 'status-pending';
                var statusText = 'Pendente';
                
                if (guest.rsvp_status === 'confirmado') {
                    statusClass = 'status-confirmed';
                    statusText = 'Confirmado';
                } else if (guest.rsvp_status === 'nao_confirmado') {
                    statusClass = 'status-declined';
                    statusText = 'Não Confirmado';
                }

                var groupInfo = guest.group_name ? 
                    `<div class="guest-details"><i class="fas fa-users me-1"></i>Grupo: ${guest.group_name}</div>` : 
                    '<div class="guest-details"><i class="fas fa-user me-1"></i>Convidado individual</div>';

                html += `
                    <div class="guest-selection-card">
                        <div class="guest-info">
                            <h5 class="guest-name">${guest.name}</h5>
                            <span class="status-badge ${statusClass}">${statusText}</span>
                        </div>
                        ${groupInfo}
                        <div class="text-center">
                            <button type="button" class="btn select-guest-btn" onclick="selectSpecificGuest(${guest.id}, this)">
                                <i class="fas fa-check me-2"></i>
                                Este sou eu
                            </button>
                        </div>
                    </div>
                `;
            });

            guestsList.innerHTML = html;
            document.getElementById('guestSelectionResults').style.display = 'block';
            logDebug('Lista de convidados exibida com sucesso');
        }

        // 🔧 FUNÇÃO CORRIGIDA - Agora recebe o botão como parâmetro
        function selectSpecificGuest(guestId, buttonElement) {
            logDebug(`Selecionando convidado ID: ${guestId}`);
            
            // 🎯 CORREÇÃO: Usar o botão passado como parâmetro
            var button = buttonElement;
            var originalText = button ? button.innerHTML : '';
            
            if (button) {
                button.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Carregando...';
                button.disabled = true;
            }

            fetch(`/get_guest_group/${guestId}`, {
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            })
            .then(response => {
                logDebug(`Response status para grupo: ${response.status}`);
                
                if (!response.ok) {
                    throw new Error(`Erro HTTP: ${response.status}`);
                }
                return response.text();
            })
            .then(text => {
                logDebug('Response do grupo:', text);
                
                let data;
                try {
                    data = JSON.parse(text);
                } catch (e) {
                    throw new Error(`Erro ao parsear JSON do grupo: ${e.message}`);
                }
                
                if (data.success && data.guests) {
                    logDebug('Dados do grupo recebidos:', data);
                    selectedGuests = data.guests;
                    document.getElementById('selectedGuestName').textContent = data.selected_guest_name;
                    showConfirmStep();
                } else {
                    throw new Error(data.error || 'Erro ao carregar grupo');
                }
            })
            .catch(error => {
                logDebug('ERRO ao carregar grupo:', error);
                alert('Erro ao carregar informações: ' + error.message);
                
                if (button) {
                    button.innerHTML = originalText;
                    button.disabled = false;
                }
            });
        }

        function displayNoResults(message = 'Nenhum convidado encontrado com este nome.') {
            logDebug('Exibindo "sem resultados":', message);
            
            document.getElementById('individualGuestsList').innerHTML = `
                <div class="alert alert-warning">
                    <i class="fas fa-exclamation-triangle me-2"></i>
                    ${message}
                    <br><small class="text-muted mt-2">
                        ✓ Verifique se digitou o nome corretamente<br>
                        ✓ Tente usar apenas o primeiro nome<br>
                        ✓ Verifique se você está na lista de convidados
                    </small>
                </div>
            `;
            document.getElementById('guestSelectionResults').style.display = 'block';
        }

        function displaySearchError(errorMessage) {
            logDebug('Exibindo erro:', errorMessage);
            
            document.getElementById('individualGuestsList').innerHTML = `
                <div class="alert alert-danger">
                    <i class="fas fa-exclamation-circle me-2"></i>
                    <strong>Erro na busca:</strong><br>
                    ${errorMessage}
                    <br><small class="text-muted mt-2">
                        Por favor, tente novamente. Se o problema persistir, entre em contato conosco.
                    </small>
                </div>
            `;
            document.getElementById('guestSelectionResults').style.display = 'block';
        }

        function showConfirmStep() {
            logDebug('Mostrando step de confirmação para:', selectedGuests);
            
            document.getElementById('searchStep').style.display = 'none';
            document.getElementById('confirmStep').style.display = 'block';

            var guestsList = document.getElementById('selectedGuestsList');
            var html = '<h6 class="mb-3">Confirme a presença para:</h6>';

            selectedGuests.forEach(guest => {
                var currentStatus = guest.rsvp_status;
                var badgeClass = '';
                var badgeText = '';

                if (currentStatus === 'confirmado') {
                    badgeClass = 'success';
                    badgeText = 'Confirmado';
                } else if (currentStatus === 'nao_confirmado') {
                    badgeClass = 'danger';
                    badgeText = 'Não Confirmado';
                } else {
                    badgeClass = 'warning';
                    badgeText = 'Pendente';
                }

                html += `
                    <div class="guest-card mb-4 p-4 border rounded-3 shadow-sm">
                        <div class="d-flex justify-content-between align-items-center mb-3">
                            <h5 class="mb-0 fw-bold text-dark">${guest.name}</h5>
                            <span class="badge bg-${badgeClass} fs-6 px-3 py-2">${badgeText}</span>
                        </div>
                        <div class="rsvp-options-container">
                            <div class="rsvp-option ${currentStatus === 'confirmado' ? 'selected' : ''}" 
                                 data-value="confirmado" data-guest="${guest.id}">
                                <input type="radio" name="rsvp_${guest.id}" id="confirm_${guest.id}" 
                                       value="confirmado" style="display: none;" ${currentStatus === 'confirmado' ? 'checked' : ''}>
                                <div class="option-content">
                                    <div class="option-icon success"><i class="fas fa-check"></i></div>
                                    <div class="option-text">
                                        <h6 class="option-title">Confirmo Presença</h6>
                                        <p class="option-subtitle">Estarei presente no casamento</p>
                                    </div>
                                </div>
                            </div>
                            <div class="rsvp-option ${currentStatus === 'nao_confirmado' ? 'selected' : ''}" 
                                 data-value="nao_confirmado" data-guest="${guest.id}">
                                <input type="radio" name="rsvp_${guest.id}" id="decline_${guest.id}" 
                                       value="nao_confirmado" style="display: none;" ${currentStatus === 'nao_confirmado' ? 'checked' : ''}>
                                <div class="option-content">
                                    <div class="option-icon danger"><i class="fas fa-times"></i></div>
                                    <div class="option-text">
                                        <h6 class="option-title">Não Poderei Comparecer</h6>
                                        <p class="option-subtitle">Infelizmente não conseguirei ir</p>
                                    </div>
                                </div>
                            </div>
                        </div>
                        <input type="hidden" name="guest_ids" value="${guest.id}">
                    </div>
                `;
            });

            guestsList.innerHTML = html;
            
            // Add click handlers for RSVP options
            document.querySelectorAll('.rsvp-option').forEach(option => {
                option.addEventListener('click', function() {
                    var guestId = this.dataset.guest;
                    var value = this.dataset.value;
                    var radioInput = document.getElementById((value === 'confirmado' ? 'confirm_' : 'decline_') + guestId);
                    
                    // Remove selected class from all options for this guest
                    document.querySelectorAll('.rsvp-option[data-guest="' + guestId + '"]').forEach(opt => {
                        opt.classList.remove('selected');
                    });
                    
                    // Add selected class to clicked option
                    this.classList.add('selected');
                    
                    // Check the radio input
                    radioInput.checked = true;
                });
            });
        }

        function goBackToSearch() {
            logDebug('Voltando para busca');
            document.getElementById('confirmStep').style.display = 'none';
            document.getElementById('searchStep').style.display = 'block';
            document.getElementById('guestSelectionResults').style.display = 'none';
            document.getElementById('guestSearch').value = '';
            selectedGuests = [];
        }

        function confirmRSVP() {
            var hasSelection = false;

            selectedGuests.forEach(guest => {
                var radios = document.querySelectorAll(`input[name="rsvp_${guest.id}"]`);
                radios.forEach(radio => {
                    if (radio.checked) {
                        hasSelection = true;
                    }
                });
            });

            if (!hasSelection) {
                alert('Por favor, confirme a presença para pelo menos um convidado.');
                return;
            }

            var button = document.querySelector('button[onclick="confirmRSVP()"]');
            if (button) {
                button.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Salvando...';
                button.disabled = true;
            }

            logDebug('Enviando confirmações...');
            document.getElementById('rsvpForm').submit();
        }

        document.getElementById('guestSearch').addEventListener('keypress', function (e) {
            if (e.key === 'Enter') {
                e.preventDefault();
            }
        });

        // Debug inicial
        logDebug('Script RSVP carregado com sucesso');
    </script>
</body>
</html>
