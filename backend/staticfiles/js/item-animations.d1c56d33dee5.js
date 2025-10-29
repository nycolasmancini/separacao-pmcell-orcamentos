/**
 * item-animations.js
 * Fase 37: Orquestração de animações fluidas para separação de itens
 *
 * Este módulo gerencia as animações de:
 * - Fade out quando item é separado/substituído
 * - Movimentação fluida dos itens restantes
 * - Fade in do item na seção de destino
 */

(function() {
    'use strict';

    // Constantes de configuração
    const ANIMATION_DURATION = 250; // ms - sincronizado com CSS --animation-speed-fast
    const ANIMATION_EASE = 'cubic-bezier(0.4, 0, 0.2, 1)';

    /**
     * Aplica fade out em um elemento e retorna Promise
     * @param {HTMLElement} element - Elemento para fazer fade out
     * @returns {Promise<void>}
     */
    function fadeOutAndRemove(element) {
        return new Promise((resolve) => {
            if (!element) {
                resolve();
                return;
            }

            // Adicionar classe de fade out
            element.classList.add('item-fade-out', 'item-removing');

            // Aguardar animação completar
            setTimeout(() => {
                resolve();
            }, ANIMATION_DURATION);
        });
    }

    /**
     * Insere elemento com animação de slide in
     * @param {HTMLElement} container - Container onde inserir
     * @param {string} html - HTML do novo elemento
     * @returns {Promise<HTMLElement>} - Elemento inserido
     */
    function insertWithAnimation(container, html) {
        return new Promise((resolve) => {
            if (!container || !html) {
                resolve(null);
                return;
            }

            // Criar elemento temporário para parsing
            const tempDiv = document.createElement('div');
            tempDiv.innerHTML = html.trim();
            const newElement = tempDiv.firstElementChild;

            if (!newElement) {
                resolve(null);
                return;
            }

            // Adicionar classes de animação
            newElement.classList.add('item-slide-in', 'item-appearing');

            // Inserir no container
            container.insertBefore(newElement, container.firstChild);

            // Remover classes após animação
            setTimeout(() => {
                newElement.classList.remove('item-slide-in', 'item-appearing');
                resolve(newElement);
            }, ANIMATION_DURATION);
        });
    }

    /**
     * Move item de uma seção para outra com animação fluida
     * @param {number} itemId - ID do item
     * @param {string} targetContainerId - ID do container de destino
     * @returns {Promise<void>}
     */
    async function moveItemWithAnimation(itemId, targetContainerId) {
        const itemElement = document.getElementById(`item-${itemId}`);
        const targetContainer = document.getElementById(targetContainerId);

        if (!itemElement || !targetContainer) {
            console.warn(`[Animations] Elemento ou container não encontrado: item-${itemId}, ${targetContainerId}`);
            return;
        }

        // 1. Fade out do item na posição atual
        await fadeOutAndRemove(itemElement);

        // 2. Remover do DOM
        itemElement.remove();

        // 3. Item será adicionado via HTMX/WebSocket com HTML atualizado
        // (não fazemos nada aqui, apenas removemos)
    }

    /**
     * Intercepta eventos HTMX para aplicar animações
     */
    function setupHTMXAnimations() {
        // Interceptar ANTES do swap para prevenir comportamento padrão quando desmarcar
        document.body.addEventListener('htmx:beforeSwap', async (event) => {
            const response = event.detail.xhr;
            const triggerHeader = response.getResponseHeader('HX-Trigger');

            // Se o trigger é 'itemDesmarcado', prevenir swap padrão e lidar manualmente
            if (triggerHeader === 'itemDesmarcado') {
                console.log('[Animations] Interceptando itemDesmarcado ANTES do swap');
                event.preventDefault(); // Impedir HTMX de fazer swap

                // Disparar evento customizado para processamento
                const itemId = response.getResponseHeader('X-Item-Id');
                document.body.dispatchEvent(new CustomEvent('itemDesmarcadoManual', {
                    detail: { itemId: itemId }
                }));
            }
        });

        // Escutar evento customizado 'itemSeparado' disparado pelo header HX-Trigger
        document.body.addEventListener('itemSeparado', async (event) => {
            console.log('[Animations] Evento itemSeparado recebido:', event);

            // O HTMX já fez o swap, mas o item ainda está no container antigo
            // Precisamos movê-lo para o container correto com animação

            // Aguardar um frame para garantir que o DOM foi atualizado
            await new Promise(resolve => requestAnimationFrame(resolve));

            // Buscar todos os items separados que estão no container errado
            const containerNaoSeparados = document.getElementById('container-nao-separados');

            if (containerNaoSeparados) {
                const itemsSeparados = containerNaoSeparados.querySelectorAll('.border-green-200');

                for (const item of itemsSeparados) {
                    if (item.id && item.id.startsWith('item-')) {
                        const itemId = item.id.replace('item-', '');
                        console.log(`[Animations] Movendo item-${itemId} para seção de separados`);

                        // 1. Aplicar fade out
                        await fadeOutAndRemove(item);

                        // 2. Clonar o HTML do item
                        const itemHTML = item.outerHTML;

                        // 3. Remover do container atual
                        item.remove();

                        // 4. Inserir na seção de separados com animação
                        const containerSeparados = document.getElementById('container-separados');

                        if (containerSeparados) {
                            const newItem = await insertWithAnimation(containerSeparados, itemHTML);

                            if (newItem) {
                                // Reprocessar HTMX
                                htmx.process(newItem);
                                console.log(`[Animations] Item ${itemId} movido com sucesso`);
                            }
                        } else {
                            console.warn('[Animations] Container de separados não encontrado, recarregando...');
                            setTimeout(() => location.reload(), ANIMATION_DURATION);
                        }
                    }
                }

                // Atualizar badges após mover todos os items
                updateBadges();
            }
        });

        // Escutar evento customizado 'itemDesmarcadoManual' (quando item volta para não separado)
        document.body.addEventListener('itemDesmarcadoManual', async (event) => {
            console.log('[Animations] Evento itemDesmarcadoManual recebido', event);

            // CORREÇÃO DE BUG (Fase 37): Em vez de clonar HTML (que causa problemas com
            // Alpine.js e HTMX), vamos buscar HTML FRESCO via GET e inserir no container correto.

            // 1. Extrair item_id do evento customizado
            const itemId = event.detail?.itemId;

            if (!itemId) {
                console.error('[Animations] item_id não encontrado no evento itemDesmarcadoManual');
                return;
            }

            console.log(`[Animations] Movendo item-${itemId} de volta para não-separados`);

            // 2. Localizar elemento no DOM
            const itemElement = document.getElementById(`item-${itemId}`);

            if (!itemElement) {
                console.warn(`[Animations] Item #item-${itemId} não encontrado no DOM`);
                return;
            }

            // 3. Aplicar fade out
            await fadeOutAndRemove(itemElement);

            // 4. Remover completamente do DOM
            itemElement.remove();

            // 5. Buscar HTML FRESCO via GET (endpoint dedicado)
            try {
                // Extrair pedido_id da URL atual ou do elemento
                const pedidoId = window.location.pathname.match(/\/pedidos\/(\d+)\//)?.[1];

                if (!pedidoId) {
                    console.error('[Animations] pedido_id não encontrado na URL');
                    return;
                }

                const url = `/pedidos/${pedidoId}/itens/${itemId}/html/`;
                console.log(`[Animations] Buscando HTML fresco: ${url}`);

                const response = await fetch(url, {
                    headers: { 'HX-Request': 'true' }
                });

                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}`);
                }

                const freshHTML = await response.text();

                // 6. FASE 38 FIX: Detectar container destino automaticamente baseado no HTML
                const containerDestinoId = detectarContainerDestino(freshHTML);
                const containerDestino = document.getElementById(containerDestinoId);

                if (!containerDestino) {
                    console.warn(`[Animations] Container ${containerDestinoId} não encontrado, recarregando...`);
                    setTimeout(() => location.reload(), ANIMATION_DURATION);
                    return;
                }

                console.log(`[Animations] Inserindo item ${itemId} em ${containerDestinoId}`);
                const newItem = await insertWithAnimation(containerDestino, freshHTML);

                if (newItem) {
                    // 7. Reprocessar HTMX e Alpine.js
                    htmx.process(newItem);
                    if (window.Alpine) {
                        window.Alpine.initTree(newItem);
                    }

                    console.log(`[Animations] Item ${itemId} movido de volta para não-separados com HTML fresco`);
                }

                // 8. Atualizar badges
                updateBadges();

            } catch (error) {
                console.error(`[Animations] Erro ao buscar HTML fresco do item ${itemId}:`, error);
                // Em caso de erro, recarregar página como fallback
                setTimeout(() => location.reload(), ANIMATION_DURATION);
            }
        });
    }

    /**
     * Detecta container destino baseado no HTML do item
     *
     * Fase 38: Correção de bug - Determinar automaticamente para qual
     * container o item deve ir baseado nas classes CSS do HTML retornado.
     *
     * @param {string} html - HTML do item retornado pela API
     * @returns {string} - ID do container destino ('container-separados' ou 'container-nao-separados')
     */
    function detectarContainerDestino(html) {
        // Parsear HTML para detectar classes CSS
        const temp = document.createElement('div');
        temp.innerHTML = html.trim();
        const itemElement = temp.firstElementChild;

        if (!itemElement) {
            console.warn('[Animations] HTML inválido, usando fallback container-nao-separados');
            return 'container-nao-separados';
        }

        // Item separado tem border-green-200 (_item_pedido.html linha 16)
        if (itemElement.classList.contains('border-green-200')) {
            console.log('[Animations] Item detectado como SEPARADO (border-green-200)');
            return 'container-separados';
        }
        // Item em compra tem border-orange-200 ou border-blue-200 (_item_pedido.html linha 91)
        else if (itemElement.classList.contains('border-orange-200') ||
                 itemElement.classList.contains('border-blue-200')) {
            console.log('[Animations] Item detectado como EM COMPRA (border-orange/blue)');
            return 'container-nao-separados'; // Itens em compra ficam em "não separados"
        }
        // Item aguardando tem border-gray-200 (_item_pedido.html linha 166)
        else if (itemElement.classList.contains('border-gray-200')) {
            console.log('[Animations] Item detectado como AGUARDANDO (border-gray-200)');
            return 'container-nao-separados';
        }
        else {
            console.warn('[Animations] Classes CSS não reconhecidas, usando fallback');
            return 'container-nao-separados';
        }
    }

    /**
     * Atualiza contadores de badges
     */
    function updateBadges() {
        const containerNaoSeparados = document.getElementById('container-nao-separados');
        const containerSeparados = document.getElementById('container-separados');
        const badgeNaoSeparados = document.getElementById('badge-nao-separados');
        const badgeSeparados = document.getElementById('badge-separados');

        if (containerNaoSeparados && badgeNaoSeparados) {
            const count = containerNaoSeparados.children.length;
            badgeNaoSeparados.textContent = `${count} itens`;
        }

        if (containerSeparados && badgeSeparados) {
            const count = containerSeparados.children.length;
            badgeSeparados.textContent = `${count} itens`;
        }
    }

    /**
     * Anima atualização de badge de contagem
     * @param {string} badgeId - ID do badge
     * @param {number} newCount - Novo valor
     */
    function animateBadgeUpdate(badgeId, newCount) {
        const badge = document.getElementById(badgeId);
        if (!badge) return;

        // Adicionar animação de pulse
        badge.classList.add('scale-in');
        badge.textContent = `${newCount} itens`;

        setTimeout(() => {
            badge.classList.remove('scale-in');
        }, 300);
    }

    /**
     * Inicializa o sistema de animações
     */
    function init() {
        console.log('[Animations] Sistema de animações inicializado');
        setupHTMXAnimations();

        // Expor funções globalmente para uso por WebSocket
        window.ItemAnimations = {
            fadeOutAndRemove,
            insertWithAnimation,
            moveItemWithAnimation,
            animateBadgeUpdate,
            ANIMATION_DURATION
        };
    }

    // Inicializar quando DOM estiver pronto
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
