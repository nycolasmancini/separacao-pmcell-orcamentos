/**
 * upload_feedback.js
 * Fase 16: Sistema de feedback visual para upload de orçamentos
 *
 * Funcionalidades:
 * - Loading spinner durante processamento
 * - Progress bar para upload
 * - Validação em tempo real com feedback visual
 * - Animações de erro/sucesso
 * - Tooltips explicativos
 */

(function() {
    'use strict';

    // ============================================
    // CONFIGURAÇÕES
    // ============================================

    const CONFIG = {
        // Tamanho mínimo para exibir progress bar (1MB)
        MIN_FILE_SIZE_FOR_PROGRESS: 1024 * 1024,

        // Duração das animações (ms)
        ANIMATION_DURATION: 300,

        // Timeout para tooltips automáticos (ms)
        TOOLTIP_AUTO_HIDE: 3000,

        // Logísticas que requerem CAIXA
        LOGISTICS_REQUIRE_BOX: ['CORREIOS', 'MELHOR_ENVIO', 'ONIBUS']
    };

    // ============================================
    // ELEMENTOS DO DOM
    // ============================================

    let elements = {};

    function initializeElements() {
        elements = {
            form: document.getElementById('uploadForm'),
            fileInput: document.querySelector('input[type="file"]'),
            logisticaSelect: document.getElementById('id_logistica'),
            embalagemRadios: document.querySelectorAll('input[name="embalagem"]'),
            submitButton: document.querySelector('button[type="submit"]'),

            // Containers de feedback (serão criados dinamicamente)
            loadingOverlay: null,
            progressContainer: null,
            progressBar: null,
            progressText: null
        };
    }

    // ============================================
    // LOADING OVERLAY
    // ============================================

    function createLoadingOverlay() {
        const overlay = document.createElement('div');
        overlay.className = 'loading-overlay';
        overlay.innerHTML = `
            <div class="bg-white rounded-lg shadow-2xl p-8 flex flex-col items-center space-y-4 scale-in">
                <div class="relative">
                    <div class="w-16 h-16 border-4 border-blue-200 border-t-blue-600 rounded-full spinner"></div>
                </div>
                <div class="text-center">
                    <p class="text-lg font-semibold text-gray-800">Processando PDF<span class="loading-dots"></span></p>
                    <p class="text-sm text-gray-600 mt-2">Extraindo informações do orçamento</p>
                </div>
            </div>
        `;
        document.body.appendChild(overlay);
        elements.loadingOverlay = overlay;
        return overlay;
    }

    function showLoadingOverlay() {
        if (!elements.loadingOverlay) {
            createLoadingOverlay();
        }
        elements.loadingOverlay.style.display = 'flex';
    }

    function hideLoadingOverlay() {
        if (elements.loadingOverlay) {
            elements.loadingOverlay.classList.add('fade-out');
            setTimeout(() => {
                if (elements.loadingOverlay && elements.loadingOverlay.parentNode) {
                    elements.loadingOverlay.parentNode.removeChild(elements.loadingOverlay);
                }
                elements.loadingOverlay = null;
            }, CONFIG.ANIMATION_DURATION);
        }
    }

    // ============================================
    // PROGRESS BAR
    // ============================================

    function createProgressBar() {
        const container = document.createElement('div');
        container.className = 'fixed bottom-8 right-8 bg-white rounded-lg shadow-2xl p-6 w-96 scale-in z-50';
        container.innerHTML = `
            <div class="space-y-3">
                <div class="flex items-center justify-between">
                    <span class="text-sm font-semibold text-gray-800">Fazendo upload...</span>
                    <span class="text-sm font-bold text-blue-600" id="progressPercentage">0%</span>
                </div>
                <div class="w-full bg-gray-200 rounded-full h-3 overflow-hidden">
                    <div class="h-full bg-gradient-to-r from-blue-500 to-blue-600 rounded-full transition-smooth progress-bar-fill"
                         id="progressBarFill"
                         style="width: 0%">
                        <div class="h-full progress-shimmer"></div>
                    </div>
                </div>
                <p class="text-xs text-gray-600" id="progressDescription">Preparando envio...</p>
            </div>
        `;
        document.body.appendChild(container);

        elements.progressContainer = container;
        elements.progressBar = container.querySelector('#progressBarFill');
        elements.progressText = container.querySelector('#progressPercentage');

        return container;
    }

    function updateProgress(percentage, description) {
        if (!elements.progressContainer) {
            createProgressBar();
        }

        const clampedPercentage = Math.min(Math.max(percentage, 0), 100);

        if (elements.progressBar) {
            elements.progressBar.style.width = `${clampedPercentage}%`;
        }

        if (elements.progressText) {
            elements.progressText.textContent = `${Math.round(clampedPercentage)}%`;
        }

        if (description) {
            const descElement = elements.progressContainer.querySelector('#progressDescription');
            if (descElement) {
                descElement.textContent = description;
            }
        }
    }

    function hideProgressBar() {
        if (elements.progressContainer) {
            elements.progressContainer.classList.add('slide-up');
            setTimeout(() => {
                if (elements.progressContainer && elements.progressContainer.parentNode) {
                    elements.progressContainer.parentNode.removeChild(elements.progressContainer);
                }
                elements.progressContainer = null;
                elements.progressBar = null;
                elements.progressText = null;
            }, CONFIG.ANIMATION_DURATION);
        }
    }

    // ============================================
    // VALIDAÇÃO EM TEMPO REAL
    // ============================================

    function updateEmbalagemValidation() {
        const logistica = elements.logisticaSelect ? elements.logisticaSelect.value : '';
        const requiresBox = CONFIG.LOGISTICS_REQUIRE_BOX.includes(logistica);

        elements.embalagemRadios.forEach(radio => {
            const isSacola = radio.value === 'SACOLA';
            const container = radio.closest('div');

            if (isSacola && requiresBox) {
                // Desabilitar SACOLA
                radio.disabled = true;
                container.classList.add('disabled-state');

                // Se estava selecionada, selecionar CAIXA
                if (radio.checked) {
                    const caixaRadio = Array.from(elements.embalagemRadios)
                        .find(r => r.value === 'CAIXA');
                    if (caixaRadio) {
                        caixaRadio.checked = true;
                        // Animação de atenção
                        caixaRadio.closest('div').classList.add('bounce');
                        setTimeout(() => {
                            caixaRadio.closest('div').classList.remove('bounce');
                        }, 600);
                    }
                }

                // Adicionar tooltip explicativo
                addTooltip(container, 'Este tipo de logística aceita apenas CAIXA');
            } else {
                // Habilitar opção
                radio.disabled = false;
                container.classList.remove('disabled-state');
                removeTooltip(container);
            }
        });
    }

    function addTooltip(element, message) {
        // Remover tooltip existente
        removeTooltip(element);

        const tooltip = document.createElement('div');
        tooltip.className = 'tooltip absolute -top-12 left-0 bg-gray-800 text-white text-xs rounded px-3 py-2 whitespace-nowrap z-10';
        tooltip.textContent = message;
        tooltip.setAttribute('data-tooltip', 'true');

        element.style.position = 'relative';
        element.appendChild(tooltip);

        // Auto-remover após timeout
        setTimeout(() => {
            removeTooltip(element);
        }, CONFIG.TOOLTIP_AUTO_HIDE);
    }

    function removeTooltip(element) {
        const existingTooltip = element.querySelector('[data-tooltip="true"]');
        if (existingTooltip) {
            existingTooltip.classList.add('fade-out');
            setTimeout(() => {
                if (existingTooltip.parentNode) {
                    existingTooltip.parentNode.removeChild(existingTooltip);
                }
            }, CONFIG.ANIMATION_DURATION);
        }
    }

    // ============================================
    // VALIDAÇÃO DE ARQUIVO
    // ============================================

    function validateFile(file) {
        const errors = [];

        // Validar extensão
        if (!file.name.toLowerCase().endsWith('.pdf')) {
            errors.push('O arquivo deve ser um PDF (.pdf)');
        }

        // Validar tamanho (10MB)
        const maxSize = 10 * 1024 * 1024;
        if (file.size > maxSize) {
            errors.push('O arquivo é muito grande. Tamanho máximo: 10MB');
        }

        // Validar tipo MIME
        if (file.type && file.type !== 'application/pdf') {
            errors.push('O arquivo deve ser um PDF válido');
        }

        return errors;
    }

    function showFileValidationErrors(errors) {
        const fileInputContainer = elements.fileInput.closest('div');

        // Remover erros anteriores
        const existingErrors = fileInputContainer.querySelectorAll('[data-file-error]');
        existingErrors.forEach(el => el.remove());

        // Adicionar novos erros com animação
        errors.forEach(error => {
            const errorDiv = document.createElement('div');
            errorDiv.className = 'mt-2 p-3 bg-red-50 border border-red-200 rounded-lg flex items-start space-x-2 slide-down';
            errorDiv.setAttribute('data-file-error', 'true');
            errorDiv.innerHTML = `
                <svg class="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                </svg>
                <span class="text-sm text-red-800">${error}</span>
            `;
            fileInputContainer.appendChild(errorDiv);
        });

        // Shake animation no input
        elements.fileInput.classList.add('shake');
        setTimeout(() => {
            elements.fileInput.classList.remove('shake');
        }, 500);
    }

    function showFileSuccess(fileName) {
        const fileInputContainer = elements.fileInput.closest('div');

        // Remover erros anteriores
        const existingErrors = fileInputContainer.querySelectorAll('[data-file-error]');
        existingErrors.forEach(el => el.remove());

        // Adicionar mensagem de sucesso
        const successDiv = document.createElement('div');
        successDiv.className = 'mt-2 p-3 bg-green-50 border border-green-200 rounded-lg flex items-start space-x-2 slide-down';
        successDiv.setAttribute('data-file-error', 'true');
        successDiv.innerHTML = `
            <svg class="w-5 h-5 text-green-600 flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"></path>
            </svg>
            <div class="flex-1">
                <span class="text-sm font-semibold text-green-800">Arquivo selecionado:</span>
                <span class="text-sm text-green-700 ml-1">${fileName}</span>
            </div>
        `;
        fileInputContainer.appendChild(successDiv);
    }

    // ============================================
    // MANIPULAÇÃO DE FORMULÁRIO
    // ============================================

    function handleFileChange(event) {
        const file = event.target.files[0];

        if (!file) {
            return;
        }

        // Validar arquivo
        const errors = validateFile(file);

        if (errors.length > 0) {
            showFileValidationErrors(errors);
            // Limpar input
            event.target.value = '';
        } else {
            showFileSuccess(file.name);
        }
    }

    function handleFormSubmit(event) {
        const file = elements.fileInput.files[0];

        if (!file) {
            return;
        }

        // Desabilitar botão de submit
        if (elements.submitButton) {
            elements.submitButton.disabled = true;
            elements.submitButton.classList.add('disabled-state');

            // Adicionar spinner ao botão
            const originalText = elements.submitButton.innerHTML;
            elements.submitButton.innerHTML = `
                <svg class="w-5 h-5 mr-2 spinner" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                    <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                Processando...
            `;

            // Restaurar botão se voltar (erro de validação)
            setTimeout(() => {
                if (elements.submitButton && elements.submitButton.disabled) {
                    elements.submitButton.disabled = false;
                    elements.submitButton.classList.remove('disabled-state');
                    elements.submitButton.innerHTML = originalText;
                }
            }, 30000); // 30 segundos timeout
        }

        // Mostrar progress bar se arquivo for grande
        if (file.size > CONFIG.MIN_FILE_SIZE_FOR_PROGRESS) {
            updateProgress(0, 'Preparando envio...');

            // Simular progresso (Django não suporta progress nativo facilmente)
            let progress = 0;
            const interval = setInterval(() => {
                progress += Math.random() * 15;
                if (progress >= 90) {
                    progress = 90;
                    clearInterval(interval);
                    updateProgress(progress, 'Processando no servidor...');
                } else {
                    updateProgress(progress, 'Enviando arquivo...');
                }
            }, 300);
        }

        // Mostrar loading overlay após um delay
        setTimeout(() => {
            showLoadingOverlay();
        }, 500);
    }

    // ============================================
    // MENSAGENS DE FEEDBACK
    // ============================================

    function enhanceMessages() {
        // Adicionar ícones e animações às mensagens do Django
        const messages = document.querySelectorAll('.messages > div, [class*="bg-"][class*="50"]');

        messages.forEach(msg => {
            if (!msg.querySelector('svg')) {
                msg.classList.add('slide-down');

                let icon = '';
                if (msg.classList.contains('bg-green-50') || msg.textContent.toLowerCase().includes('sucesso')) {
                    icon = `
                        <svg class="w-5 h-5 text-green-600 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                        </svg>
                    `;
                } else if (msg.classList.contains('bg-red-50') || msg.textContent.toLowerCase().includes('erro')) {
                    icon = `
                        <svg class="w-5 h-5 text-red-600 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                        </svg>
                    `;
                } else if (msg.classList.contains('bg-blue-50')) {
                    icon = `
                        <svg class="w-5 h-5 text-blue-600 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                        </svg>
                    `;
                }

                if (icon) {
                    const content = msg.innerHTML;
                    msg.innerHTML = `<div class="flex items-start space-x-2">${icon}<div class="flex-1">${content}</div></div>`;
                }
            }
        });
    }

    // ============================================
    // INICIALIZAÇÃO
    // ============================================

    function init() {
        console.log('[Upload Feedback] Inicializando sistema de feedback visual...');

        initializeElements();

        // Event listeners
        if (elements.fileInput) {
            elements.fileInput.addEventListener('change', handleFileChange);
        }

        if (elements.logisticaSelect) {
            elements.logisticaSelect.addEventListener('change', updateEmbalagemValidation);
            // Executar na inicialização
            updateEmbalagemValidation();
        }

        if (elements.form) {
            elements.form.addEventListener('submit', handleFormSubmit);
        }

        // Melhorar mensagens existentes
        enhanceMessages();

        console.log('[Upload Feedback] Sistema inicializado com sucesso!');
    }

    // Inicializar quando DOM estiver pronto
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }

    // Expor funções globalmente (para debugging)
    window.UploadFeedback = {
        showLoadingOverlay,
        hideLoadingOverlay,
        updateProgress,
        hideProgressBar
    };

})();
