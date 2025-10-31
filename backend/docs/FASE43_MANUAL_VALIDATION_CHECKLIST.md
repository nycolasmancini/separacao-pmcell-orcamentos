# FASE 43f - Manual Validation Checklist

**Objetivo**: Validar manualmente os três problemas reportados pelo usuário e confirmar que todas as soluções implementadas funcionam corretamente em produção.

**Data de Criação**: 2025-10-31
**Status**: ⏳ AGUARDANDO VALIDAÇÃO MANUAL

---

## 📋 Problemas Reportados (User Request)

### ✅ Issue #1 - Items appear in purchase panel (JÁ FUNCIONAVA)
**Status Inicial**: WORKING ✅
**Ação Necessária**: Nenhuma (já estava funcionando)

### ❌ Issue #2 - Items don't disappear from purchase panel when separated
**Status Inicial**: NOT WORKING ❌
**Solução Implementada**: Fase 43a & 43b
**Ação Necessária**: VALIDAR manualmente

### ❌ Issue #3 - Badge doesn't update from "Aguardando Compra" to "Já Comprado"
**Status Inicial**: NOT WORKING ❌
**Solução Implementada**: Fase 43c & 43d
**Ação Necessária**: VALIDAR manualmente

---

## 🧪 TESTE 1: Validar Issue #2 - Item Desaparece do Painel ao Separar

### Pré-requisitos
- [ ] Servidor Django rodando em `http://localhost:8000`
- [ ] Banco de dados com pedido contendo itens não separados
- [ ] Usuário SEPARADOR criado e logado

### Passos de Validação

1. **Setup Inicial**
   - [ ] Abrir **Tab 1**: `http://localhost:8000/painel-compras/`
   - [ ] Abrir **Tab 2**: `http://localhost:8000/dashboard/` (escolher um pedido)
   - [ ] No **Tab 2**, marcar pelo menos 1 item para compra (botão "🛒 Enviar para Compra")
   - [ ] Verificar que item apareceu no **Tab 1** (Painel de Compras)

2. **Testar Separação → Remove do Painel**
   - [ ] No **Tab 2** (Dashboard), marcar o mesmo item como **SEPARADO** (checkbox verde)
   - [ ] **VALIDAR Tab 1**: Item deve **DESAPARECER** do Painel de Compras em tempo real
   - [ ] **VALIDAR**: Fade-out animation deve ocorrer
   - [ ] **VALIDAR**: Nenhum reload da página deve acontecer
   - [ ] **VALIDAR Console Tab 1**: Deve logar `[WebSocket] Item separado recebido - item_id: X, em_compra: false`

3. **Testar Substituição → Remove do Painel**
   - [ ] Marcar outro item para compra no **Tab 2**
   - [ ] Marcar o mesmo item como **SUBSTITUÍDO** (botão "Substituir")
   - [ ] **VALIDAR Tab 1**: Item deve **DESAPARECER** do Painel de Compras em tempo real
   - [ ] **VALIDAR**: Fade-out animation deve ocorrer

4. **Testar Múltiplos Itens Sequenciais**
   - [ ] Marcar 3 itens para compra no **Tab 2**
   - [ ] Separar os 3 itens sequencialmente
   - [ ] **VALIDAR Tab 1**: Cada item deve desaparecer em tempo real conforme é separado
   - [ ] **VALIDAR**: Nenhum item duplicado deve aparecer

5. **Testar Round-Trip**
   - [ ] Marcar item para compra → aparece no Painel
   - [ ] Separar item → desaparece do Painel
   - [ ] Desmarcar separação → não deve reaparecer (correto: item sem em_compra)
   - [ ] Marcar para compra novamente → deve reaparecer no Painel

### ✅ Critério de Sucesso
- [ ] Todos os itens marcados como separados **desaparecem do painel em tempo real**
- [ ] Todos os itens marcados como substituídos **desaparecem do painel em tempo real**
- [ ] Nenhum reload manual é necessário
- [ ] Animação fade-out funciona corretamente
- [ ] Console logs confirmam recebimento do evento WebSocket

---

## 🧪 TESTE 2: Validar Issue #3 - Badge Atualiza "Aguardando Compra" → "Já Comprado"

### Pré-requisitos
- [ ] Servidor Django rodando em `http://localhost:8000`
- [ ] Banco de dados com pedido contendo itens em compra
- [ ] Usuário COMPRADORA criado e logado

### Passos de Validação

1. **Setup Inicial**
   - [ ] Login como **COMPRADORA** (tipo=COMPRADORA)
   - [ ] Abrir **Tab 1**: `http://localhost:8000/dashboard/` (detalhe de um pedido)
   - [ ] Abrir **Tab 2**: `http://localhost:8000/painel-compras/`
   - [ ] No **Tab 1**, marcar pelo menos 1 item para compra
   - [ ] **VALIDAR Tab 1**: Badge laranja **"⏳ Aguardando Compra"** deve aparecer no item

2. **Testar Marcar como Realizado → Badge Atualiza**
   - [ ] No **Tab 2** (Painel de Compras), marcar checkbox **"Pedido Realizado"** para o item
   - [ ] **VALIDAR Tab 1**: Badge deve mudar de laranja para azul **"✓ Já comprado"** em tempo real
   - [ ] **VALIDAR**: Nenhum reload da página deve acontecer
   - [ ] **VALIDAR Console Tab 1**: Deve logar `[WebSocket] Item pedido realizado: item_id: X, pedido_realizado: true`
   - [ ] **VALIDAR Console Tab 1**: Deve logar `[WebSocket] Badge atualizado para item X - pedido_realizado: true`

3. **Testar Desmarcar Realizado → Badge Reverte**
   - [ ] No **Tab 2**, **DESMARCAR** checkbox "Pedido Realizado"
   - [ ] **VALIDAR Tab 1**: Badge deve voltar para laranja **"⏳ Aguardando Compra"** em tempo real
   - [ ] **VALIDAR**: Toggle behavior funciona corretamente
   - [ ] **VALIDAR Console Tab 1**: Deve logar `pedido_realizado: false`

4. **Testar Multi-Tab Synchronization**
   - [ ] Abrir **Tab 3**: `http://localhost:8000/dashboard/` (mesmo pedido)
   - [ ] No **Tab 2**, marcar item como realizado
   - [ ] **VALIDAR Tab 1 e Tab 3**: Badges devem atualizar **SIMULTANEAMENTE** em ambas as tabs
   - [ ] **VALIDAR**: WebSocket sincroniza todas as tabs abertas

5. **Testar Múltiplos Itens**
   - [ ] Marcar 3 itens para compra no **Tab 1**
   - [ ] No **Tab 2**, marcar 2 itens como realizados
   - [ ] **VALIDAR Tab 1**: Apenas os 2 itens marcados devem ter badge azul
   - [ ] **VALIDAR**: O terceiro item deve manter badge laranja

6. **Testar Badge CSS Classes**
   - [ ] Inspecionar badge azul no DevTools
   - [ ] **VALIDAR**: Classe CSS: `bg-blue-100 text-blue-800`
   - [ ] **VALIDAR**: Texto: "Já comprado"
   - [ ] **VALIDAR**: Ícone: Checkmark SVG
   - [ ] Inspecionar badge laranja no DevTools
   - [ ] **VALIDAR**: Classe CSS: `bg-orange-100 text-orange-800`
   - [ ] **VALIDAR**: Texto: "Aguardando Compra"
   - [ ] **VALIDAR**: Ícone: Clock SVG

### ✅ Critério de Sucesso
- [ ] Badge atualiza de laranja para azul **em tempo real** ao marcar como realizado
- [ ] Badge reverte de azul para laranja **em tempo real** ao desmarcar
- [ ] Toggle behavior funciona perfeitamente
- [ ] Multi-tab synchronization funciona (todas as tabs atualizam simultaneamente)
- [ ] Console logs confirmam recebimento do evento WebSocket
- [ ] CSS classes e ícones SVG corretos são aplicados

---

## 🧪 TESTE 3: Integração Completa (End-to-End Flow)

### Cenário: Fluxo Completo de Compra

1. **Fase 1: Marcar para Compra**
   - [ ] Dashboard → Marcar item para compra
   - [ ] **VALIDAR**: Badge laranja aparece localmente SEM reload
   - [ ] **VALIDAR**: Painel de Compras mostra item (após reload automático)

2. **Fase 2: Compradora Marca Realizado**
   - [ ] Painel de Compras → Marcar "Pedido Realizado"
   - [ ] **VALIDAR**: Badge no Dashboard atualiza para azul em tempo real
   - [ ] **VALIDAR**: Painel de Compras mantém item visível

3. **Fase 3: Separador Marca como Separado**
   - [ ] Dashboard → Marcar item como separado
   - [ ] **VALIDAR**: Item desaparece do Painel de Compras em tempo real
   - [ ] **VALIDAR**: Badge desaparece do Dashboard (item separado não mostra badge)

### Cenário: Fluxo de Cancelamento

1. **Fase 1: Marcar para Compra**
   - [ ] Dashboard → Marcar item para compra
   - [ ] **VALIDAR**: Badge laranja aparece

2. **Fase 2: Separador Desmarca Compra**
   - [ ] Dashboard → Desmarcar compra (clicar novamente no botão)
   - [ ] **VALIDAR**: Item desaparece do Painel de Compras em tempo real
   - [ ] **VALIDAR**: Badge desaparece do Dashboard

### Cenário: Múltiplas Operações Sequenciais

1. **Operações Rápidas**
   - [ ] Marcar item para compra → Separar → Marcar novamente → Marcar realizado
   - [ ] **VALIDAR**: Cada operação sincroniza corretamente
   - [ ] **VALIDAR**: Nenhum estado inconsistente ocorre
   - [ ] **VALIDAR**: Nenhum item duplicado aparece

### ✅ Critério de Sucesso
- [ ] Fluxo completo funciona sem erros
- [ ] Todas as sincronizações em tempo real funcionam
- [ ] Nenhum estado inconsistente entre Dashboard e Painel de Compras
- [ ] Operações sequenciais não causam duplicação

---

## 🔍 TESTE 4: Edge Cases & Error Handling

### Teste 4.1: Item Inexistente
- [ ] Abrir console do browser
- [ ] Simular evento WebSocket com `item_id` que não existe na página
- [ ] **VALIDAR**: Console loga warning: "Badge não encontrado para item X"
- [ ] **VALIDAR**: Nenhum erro JavaScript ocorre

### Teste 4.2: Permissões
- [ ] Login como **SEPARADOR** (não COMPRADORA)
- [ ] Tentar acessar `/compras/itens/{item_id}/marcar-realizado/`
- [ ] **VALIDAR**: Erro 403 Forbidden ou redirecionamento
- [ ] **VALIDAR**: Logs backend mostram "usuário não autorizado"

### Teste 4.3: WebSocket Desconectado
- [ ] Abrir Dashboard em Tab 1
- [ ] Abrir DevTools Network → Desconectar WebSocket manualmente
- [ ] Em Tab 2, marcar item como realizado
- [ ] **VALIDAR Tab 1**: Badge não atualiza (WebSocket offline)
- [ ] Recarregar Tab 1
- [ ] **VALIDAR**: Badge aparece no estado correto após reload

### Teste 4.4: Race Conditions
- [ ] Marcar 5 itens para compra SIMULTANEAMENTE
- [ ] Separar os 5 itens SIMULTANEAMENTE
- [ ] **VALIDAR**: Painel de Compras remove todos corretamente
- [ ] **VALIDAR**: Nenhum item fica "preso" no painel

### ✅ Critério de Sucesso
- [ ] Erros são tratados graciosamente
- [ ] Console logs informativos aparecem
- [ ] Nenhum crash ou erro JavaScript não tratado
- [ ] Sistema recupera corretamente após reconexão WebSocket

---

## 📊 TESTE 5: Performance & Load Testing

### Teste 5.1: Múltiplos Itens (Stress Test)
- [ ] Criar pedido com 20+ itens
- [ ] Marcar todos para compra
- [ ] **VALIDAR**: Painel de Compras carrega em < 2 segundos
- [ ] Separar todos os itens sequencialmente
- [ ] **VALIDAR**: Cada remoção do painel é instantânea (< 500ms)

### Teste 5.2: Múltiplas Tabs (Concurrency)
- [ ] Abrir 5 tabs no mesmo pedido
- [ ] Em tab 1, marcar item como realizado
- [ ] **VALIDAR**: Todas as 5 tabs atualizam badge simultaneamente
- [ ] **VALIDAR**: Nenhuma tab fica dessincronizada

### Teste 5.3: Memory Leaks
- [ ] Abrir Dashboard, deixar aberto por 10 minutos
- [ ] Marcar/desmarcar itens repetidamente (50+ operações)
- [ ] Abrir DevTools → Memory → Take Heap Snapshot
- [ ] **VALIDAR**: Nenhum crescimento anormal de memória
- [ ] **VALIDAR**: Event listeners não duplicados

### ✅ Critério de Sucesso
- [ ] Sistema responsivo mesmo com muitos itens
- [ ] Sincronização multi-tab funciona com 5+ tabs
- [ ] Nenhum memory leak detectado

---

## 📝 TESTE 6: Backend Logic Validation

### Teste 6.1: Toggle Behavior (marcar_realizado)
- [ ] Via Django shell ou Admin, verificar `item.pedido_realizado = False`
- [ ] Chamar `item.marcar_realizado(usuario_compradora)`
- [ ] **VALIDAR**: `item.pedido_realizado == True`
- [ ] Chamar novamente `item.marcar_realizado(usuario_compradora)`
- [ ] **VALIDAR**: `item.pedido_realizado == False` (toggle working)

### Teste 6.2: WebSocket Event Emission
- [ ] Backend logs em `/tmp/django_*.log`
- [ ] Marcar item como realizado via UI
- [ ] **VALIDAR Logs**: Mensagem "[WebSocket] Evento 'item_pedido_realizado' emitido"
- [ ] **VALIDAR Logs**: `item_id` e `pedido_realizado` corretos no payload

### Teste 6.3: Database Consistency
- [ ] Marcar item como realizado via UI
- [ ] Verificar no banco: `SELECT pedido_realizado, realizado_por_id, realizado_em FROM core_itempedido WHERE id=X`
- [ ] **VALIDAR**: `pedido_realizado = 1`
- [ ] **VALIDAR**: `realizado_por_id` = ID da compradora
- [ ] **VALIDAR**: `realizado_em` = timestamp correto

### ✅ Critério de Sucesso
- [ ] Toggle behavior funciona no model
- [ ] WebSocket events são emitidos corretamente
- [ ] Dados persistem corretamente no banco

---

## ✅ CHECKLIST FINAL - Fase 43f

### Implementação Backend
- [x] **Fase 43a**: Backend tests para item_separado (7 testes)
- [x] **Fase 43b**: Frontend handler para purchase panel removal (8 testes E2E)
- [x] **Fase 43c**: Backend tests para pedido_realizado WebSocket (7 testes)
  - [x] Fix toggle behavior em `marcar_realizado()`
  - [x] WebSocket emission em `MarcarRealizadoView`
  - [x] Handler `item_pedido_realizado()` em `DashboardConsumer`
- [x] **Fase 43d**: Frontend handler para badge update (detalhe_pedido.html)
  - [x] Case `item_pedido_realizado` no switch statement
  - [x] Função `handleItemPedidoRealizado()` implementada
- [x] **Fase 43e**: Integration E2E tests (10 E2E + 3 backend)

### Validação Manual (Fase 43f)
- [ ] **TESTE 1**: Issue #2 - Item desaparece do painel ao separar
- [ ] **TESTE 2**: Issue #3 - Badge atualiza "Aguardando Compra" → "Já Comprado"
- [ ] **TESTE 3**: Integração completa end-to-end
- [ ] **TESTE 4**: Edge cases & error handling
- [ ] **TESTE 5**: Performance & load testing
- [ ] **TESTE 6**: Backend logic validation

### Documentação
- [x] Checklist de validação manual criado
- [ ] Resultados dos testes manuais documentados
- [ ] Screenshots/videos de testes bem-sucedidos (opcional)

---

## 🎯 Próximos Passos (Após Validação)

1. **Se TODOS os testes passarem**:
   - [ ] Marcar Fase 43f como completa
   - [ ] Criar commit final: `feat: Fase 43 - Fix purchase panel sync issues`
   - [ ] Atualizar plan.md com status da Fase 43
   - [ ] Reportar ao usuário: "Fase 43 concluída com sucesso"

2. **Se ALGUM teste falhar**:
   - [ ] Documentar exatamente qual teste falhou
   - [ ] Investigar root cause
   - [ ] Criar nova fase (Fase 43g?) para fix
   - [ ] Re-executar todos os testes após fix

---

## 📌 Notas Importantes

- **Apenas COMPRADORA** pode marcar itens como realizados (permissão backend)
- **WebSocket** deve estar conectado para sincronização em tempo real
- **Badge** só aparece em itens com `em_compra=True`
- **Fade-out animation** dura 300ms (definido em painel_compras.html)
- **Badge azul** aparece quando `pedido_realizado=True`
- **Badge laranja** aparece quando `em_compra=True` e `pedido_realizado=False`

---

**FIM DO CHECKLIST - Fase 43f**
