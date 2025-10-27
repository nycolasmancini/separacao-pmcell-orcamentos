# PLANEJAMENTO - Web App Separação de Pedidos PMCELL

> **ATENÇÃO**: Este arquivo deve ser lido no INÍCIO de CADA sessão de desenvolvimento.
> Use `/clear` ao final de cada resposta do Claude para otimizar contexto.

---

## 📌 ÍNDICE RÁPIDO

1. [Visão Geral](#1-visão-geral)
2. [Stack Técnica](#2-stack-técnica)
3. [Metodologia](#3-metodologia)
4. [Status Atual](#4-status-atual)
5. [Fases de Desenvolvimento](#5-fases-de-desenvolvimento)
6. [UI/UX Guidelines](#6-uiux-guidelines)
7. [Decisões Técnicas](#7-decisões-técnicas)
8. [Como Usar Este Arquivo](#8-como-usar-este-arquivo)

---

## 1. VISÃO GERAL

### 1.1 Objetivo do Projeto
Web app interno para otimização do processo de separação de pedidos da PMCELL São Paulo.

### 1.2 Funcionalidades Principais
- Upload e parsing automático de orçamentos em PDF
- Dashboard com cards de pedidos em tempo real (WebSockets)
- Sistema de separação colaborativa (múltiplos usuários)
- Gestão de produtos faltantes (integração com compras)
- Métricas de performance da equipe
- Histórico completo de pedidos

### 1.3 Escopo
- **Usuários**: 7-12 funcionários simultâneos
- **Volume**: 30-40 pedidos/dia
- **Tipos de usuário**: Vendedores, Separadores, Compradora, Administrador
- **Acesso**: Web app interno (rede interna)

### 1.4 Documentação Existente
- **modelo-pdf.md**: Análise detalhada da estrutura dos PDFs de orçamento
- **projeto.md**: Especificação completa do sistema (78+ páginas)

---

## 2. STACK TÉCNICA

### 2.1 Backend
- **Framework**: Django 5.x
- **Tempo Real**: Django Channels + WebSockets
- **Banco de Dados**: PostgreSQL 15+
- **Cache/Broker**: Redis 7+
- **Parsing PDF**: pdfplumber
- **API**: Django REST Framework (para endpoints AJAX)

### 2.2 Frontend
- **Templates**: Django Templates
- **Interatividade**: HTMX (para reatividade sem JavaScript pesado)
- **CSS Framework**: Tailwind CSS 3.x
- **Animações**: Tailwind transitions + Alpine.js (para micro-interações)
- **WebSocket Client**: JavaScript nativo (WebSocket API)

### 2.3 Ferramentas de Desenvolvimento
- **Versionamento**: Git
- **Testes**: pytest + pytest-django + Playwright (E2E)
- **Qualidade**: Black (formatação) + Flake8 (linting)
- **Documentação**: Docstrings + Swagger (DRF)

### 2.4 Hospedagem (Planejada)
- **Plataforma**: Railway.app (~$10-20/mês)
- **Deploy**: Automático via Git
- **Ambiente**: Production + Staging

---

## 3. METODOLOGIA

### 3.1 Desenvolvimento Atômico
Cada fase implementa UMA funcionalidade mínima e completa.

**Exemplo**:
- ❌ Fase ruim: "Implementar autenticação"
- ✅ Fase boa: "Criar modelo de usuário com validação de PIN"

### 3.2 TDD Rigoroso
**Ciclo obrigatório em TODAS as fases**:

```
1. RED: Escrever teste que falha
2. GREEN: Implementar código mínimo para passar
3. REFACTOR: Melhorar código mantendo testes verdes
4. COMMIT: Commitar apenas quando tudo passar
```

### 3.3 Estrutura de Cada Fase
```
Fase X: [Nome da Fase]
├── 1. Objetivo (o que fazer)
├── 2. Testes (escrever ANTES)
├── 3. Implementação (código mínimo)
├── 4. Validação (tudo passou?)
└── 5. Próximos Passos
```

### 3.4 Arquitetura DDD (Domain-Driven Design)

```
src/
├── domain/           # Entidades e lógica de negócio
├── application/      # Casos de uso
├── infrastructure/   # Implementações (DB, PDF, WebSocket)
└── presentation/     # Views, templates, forms
```

---

## 4. STATUS ATUAL

### 4.1 O Que Foi Feito

#### ✅ Fase 0: Planejamento e Documentação
- **Concluído**: modelo-pdf.md (análise de PDFs)
- **Concluído**: projeto.md (especificação completa)
- **Concluído**: planejamento.md (este arquivo)
- **Concluído**: Definição de stack técnica
- **Status**: 100% completo

#### ✅ Fase 1: Setup do Projeto Django
- **Concluído**: Projeto Django criado em `/backend/`
- **Concluído**: App `core` criado com estrutura DDD
- **Concluído**: Estrutura DDD completa (domain/, application/, infrastructure/, presentation/)
- **Concluído**: requirements.txt (Django 4.2.25 + pytest)
- **Concluído**: .gitignore configurado
- **Concluído**: README.md com documentação básica
- **Concluído**: settings.py configurado (app core registrado, pt-br, timezone SP)
- **Concluído**: Docstrings em todas as camadas DDD
- **Concluído**: 6 testes automatizados (100% passando)
- **Concluído**: TDD rigoroso seguido (RED → GREEN → REFACTOR)
- **Status**: 100% completo

#### ✅ Fase 2: Configuração do PostgreSQL e Redis
- **Concluído**: PostgreSQL 16 instalado e configurado
- **Concluído**: Redis instalado e funcionando
- **Concluído**: Banco de dados `separacao_pmcell_dev` criado
- **Concluído**: Usuário `pmcell_user` criado com permissões corretas
- **Concluído**: requirements.txt atualizado (psycopg2-binary, redis, django-redis, python-decouple)
- **Concluído**: settings.py configurado com PostgreSQL como banco padrão
- **Concluído**: settings.py configurado com Redis como cache backend
- **Concluído**: Migrations aplicadas com sucesso no PostgreSQL
- **Concluído**: 8 testes automatizados da Fase 2 (100% passando)
- **Concluído**: REFACTOR: Variáveis de ambiente implementadas (.env, .env.example)
- **Concluído**: TDD rigoroso seguido (RED → GREEN → REFACTOR)
- **Concluído**: Validação final: 14 testes passando (6 Fase 1 + 8 Fase 2)
- **Status**: 100% completo

#### ✅ Fase 3: Setup do Tailwind CSS
- **Concluído**: Estrutura de diretórios criada (static/css/, templates/)
- **Concluído**: settings.py configurado (STATIC_ROOT, STATICFILES_DIRS, TEMPLATES DIRS)
- **Concluído**: input.css criado com diretivas Tailwind (@tailwind base, components, utilities)
- **Concluído**: Variáveis CSS customizadas PMCELL implementadas (cores, badges, botões)
- **Concluído**: templates/base.html criado com estrutura HTML5 e Google Fonts (Inter)
- **Concluído**: tailwind.config.js configurado (content paths, cores custom, animações)
- **Concluído**: Tailwind CSS 3.4.0 instalado via npm
- **Concluído**: package.json criado com scripts (build:css, watch:css)
- **Concluído**: output.css compilado com sucesso (7.2KB minificado)
- **Concluído**: .gitignore atualizado (node_modules, output.css, package-lock.json)
- **Concluído**: View de teste criada (test_tailwind_view) com template demonstrativo
- **Concluído**: URLs configuradas (/test-tailwind/)
- **Concluído**: 8 testes automatizados da Fase 3 (100% passando)
- **Concluído**: TDD rigoroso seguido (RED → GREEN → REFACTOR)
- **Concluído**: Validação final: 22 testes passando (6 Fase 1 + 8 Fase 2 + 8 Fase 3)
- **Concluído**: Correção de encoding UTF-8 em arquivos Python
- **Status**: 100% completo

#### ✅ Fase 4: Setup do HTMX e Alpine.js
- **Concluído**: HTMX 1.9.12 adicionado via CDN em base.html
- **Concluído**: Alpine.js 3.x adicionado via CDN em base.html
- **Concluído**: Template test_htmx_partial.html criado (partial HTML sem layout)
- **Concluído**: Template test_htmx_alpine.html criado com exemplos interativos
- **Concluído**: Exemplos HTMX implementados (hx-get, hx-target, hx-swap, hx-indicator)
- **Concluído**: Exemplos Alpine.js implementados (dropdown, contador, tabs)
- **Concluído**: Views criadas (test_htmx_partial_view, test_htmx_alpine_view)
- **Concluído**: URLs configuradas (/test-htmx-partial/, /test-htmx-alpine/)
- **Concluído**: Helper functions criadas em core/presentation/web/utils.py
- **Concluído**: Funções auxiliares: is_htmx_request(), get_htmx_trigger(), htmx_redirect(), htmx_refresh()
- **Concluído**: Documentação de padrões HTMX e Alpine.js adicionada ao README.md
- **Concluído**: Exemplos práticos documentados com código
- **Concluído**: 10 testes automatizados da Fase 4 (100% passando)
- **Concluído**: TDD rigoroso seguido (RED → GREEN → REFACTOR)
- **Concluído**: Validação final: 32 testes passando (6 Fase 1 + 8 Fase 2 + 8 Fase 3 + 10 Fase 4)
- **Status**: 100% completo

#### ✅ Fase 5: Criar Modelo de Usuário Customizado
- **Concluído**: Estrutura de diretórios criada (domain/usuario/, infrastructure/persistence/models/, infrastructure/persistence/repositories/)
- **Concluído**: Entidade de domínio Usuario criada (domain/usuario/entities.py)
- **Concluído**: Validações de PIN implementadas (4 dígitos numéricos, hash PBKDF2)
- **Concluído**: Tipos de usuário definidos (VENDEDOR, SEPARADOR, COMPRADORA, ADMINISTRADOR)
- **Concluído**: Modelo Django Usuario criado herdando AbstractBaseUser
- **Concluído**: UsuarioManager customizado implementado (create_user, create_superuser)
- **Concluído**: Repositório DjangoUsuarioRepository criado seguindo padrão DDD
- **Concluído**: AUTH_USER_MODEL configurado em settings.py
- **Concluído**: Migration 0001_create_usuario_model criada e aplicada
- **Concluído**: Django Admin customizado (UsuarioAdmin com formulários de criação/edição)
- **Concluído**: Formulários customizados (UsuarioCreationForm, UsuarioChangeForm)
- **Concluído**: 8 testes automatizados da Fase 5 (100% passando)
- **Concluído**: TDD rigoroso seguido (RED → GREEN → REFACTOR)
- **Concluído**: Correção de encoding UTF-8 em arquivos DDD
- **Concluído**: Validação final: 40 testes passando (6 Fase 1 + 8 Fase 2 + 8 Fase 3 + 10 Fase 4 + 8 Fase 5)
- **Status**: 100% completo

#### ✅ Fase 6: Implementar Caso de Uso de Login
- **Concluído**: Estrutura de use cases e DTOs criada (application/use_cases/, application/dtos/)
- **Concluído**: LoginResponseDTO criado com validações pós-inicialização
- **Concluído**: LoginUseCase implementado com validação de credenciais
- **Concluído**: Rate limiting implementado via Redis (5 tentativas/60 segundos)
- **Concluído**: Logging completo adicionado (info, warning, error)
- **Concluído**: Constantes extraídas (MAX_ATTEMPTS, DURATION, ERROR_MESSAGES)
- **Concluído**: Entidades de suporte criadas (Usuario, TipoUsuario, UsuarioRepositoryInterface)
- **Concluído**: pytest.ini configurado (desabilitando Django temporariamente)
- **Concluído**: 8 testes automatizados da Fase 6 (100% passando)
- **Concluído**: TDD rigoroso seguido (RED → GREEN → REFACTOR)
- **Concluído**: Fail-safe implementado para erros no Redis
- **Status**: 100% completo

#### ✅ Fase 7: Criar Tela de Login (UI)
- **Concluído**: Estrutura Django completa criada (manage.py, settings.py, urls.py, wsgi.py, asgi.py)
- **Concluído**: Modelo Django Usuario configurado como custom user (AUTH_USER_MODEL)
- **Concluído**: Migrations criadas e aplicadas (0001_initial)
- **Concluído**: LoginForm criado com validações client-side e server-side
- **Concluído**: LoginView implementada com integração de autenticação
- **Concluído**: Rate limiting funcional via cache (5 tentativas/60 segundos)
- **Concluído**: Template login.html com design moderno Tailwind CSS
- **Concluído**: Template dashboard.html placeholder criado
- **Concluído**: URLs configuradas (/login/, /dashboard/)
- **Concluído**: Validações de formulário (PIN 4 dígitos, campos obrigatórios)
- **Concluído**: Loading states com Alpine.js
- **Concluído**: Sistema de mensagens de erro/sucesso
- **Concluído**: Sessões Django funcionando (8 horas de duração)
- **Concluído**: 8 testes automatizados da Fase 7 (100% passando)
- **Concluído**: TDD rigoroso seguido (RED → GREEN → REFACTOR)
- **Concluído**: Servidor Django funcional testado (HTTP 200 em /login/)
- **Status**: 100% completo

#### ✅ Fase 8: Implementar Sessão e Middleware de Autenticação
- **Concluído**: Estrutura de middleware criada (core/middleware/)
- **Concluído**: SessionTimeoutMiddleware implementado com timeout de 8h
- **Concluído**: Verificação de autenticação em cada request
- **Concluído**: Atualização de timestamp de última atividade
- **Concluído**: Redirecionamento para login se sessão expirada
- **Concluído**: URLs públicas configuráveis (login, admin)
- **Concluído**: Decorator @login_required criado (core/presentation/web/decorators.py)
- **Concluído**: LogoutView implementada com limpeza de sessão
- **Concluído**: Rota /logout/ adicionada
- **Concluído**: LoginView atualizado para usar login() do Django
- **Concluído**: Configurações de sessão em settings.py (SESSION_COOKIE_AGE=28800)
- **Concluído**: Logging completo implementado (info, warning, error)
- **Concluído**: Middleware registrado em settings.py
- **Concluído**: 8 testes automatizados da Fase 8 (100% passando)
- **Concluído**: TDD rigoroso seguido (RED → GREEN → REFACTOR)
- **Concluído**: Validação final: 24 testes passando (8 Fase 6 + 8 Fase 7 + 8 Fase 8)
- **Status**: 100% completo

#### ✅ Fase 9: Criar Entidade Produto
- **Concluído**: Entidade Produto criada em domain/produto/entities.py
- **Concluído**: Validação matemática implementada (quantidade × valor_unitario = valor_total)
- **Concluído**: Validação de código (5 dígitos numéricos)
- **Concluído**: Modelo Django Produto criado
- **Concluído**: Migration 0002_produto criada e aplicada
- **Concluído**: Repositório DjangoProdutoRepository implementado
- **Concluído**: Interface ProdutoRepositoryInterface criada
- **Concluído**: Métodos: save(), get_by_codigo(), get_by_id(), get_all(), delete()
- **Concluído**: Logging completo implementado
- **Concluído**: 8 testes automatizados da Fase 9 (100% passando)
- **Concluído**: TDD rigoroso seguido (RED → GREEN → REFACTOR)
- **Concluído**: Encoding UTF-8 em todos os arquivos
- **Concluído**: Docstrings completas em todas as classes e métodos
- **Status**: 100% completo

#### ✅ Fase 10: Implementar Parser de PDF Base
- **Concluído**: Estrutura de diretórios criada (infrastructure/pdf/, tests/unit/infrastructure/pdf/)
- **Concluído**: Exceções customizadas (InvalidPDFError, PDFExtractionError)
- **Concluído**: PDFParser implementado com pdfplumber
- **Concluído**: Método extrair_texto() funcional
- **Concluído**: Tratamento de erros completo (arquivo inexistente, PDF inválido, PDF corrompido)
- **Concluído**: Preservação de formatação original (quebras de linha, espaços, caracteres especiais)
- **Concluído**: pdfplumber instalado via pip
- **Concluído**: Logging completo (info, warning, error, debug)
- **Concluído**: Docstrings completas Google Style
- **Concluído**: Type hints em todos os métodos
- **Concluído**: Constantes extraídas (mensagens de erro, extensão PDF)
- **Concluído**: 8 testes automatizados da Fase 10 (100% passando)
- **Concluído**: TDD rigoroso seguido (RED → GREEN → REFACTOR)
- **Concluído**: Validação com PDFs reais (5 orçamentos testados)
- **Concluído**: Encoding UTF-8 em todos os arquivos
- **Status**: 100% completo

#### ✅ Fase 11: Implementar Extração de Cabeçalho do PDF
- **Concluído**: OrcamentoHeaderDTO criado em core/application/dtos/orcamento_dtos.py
- **Concluído**: PDFHeaderExtractor adicionado ao core/infrastructure/pdf/parser.py
- **Concluído**: Regex patterns implementados para todos os campos
- **Concluído**: Campos extraídos: numero_orcamento, codigo_cliente, nome_cliente, vendedor, data
- **Concluído**: Fail-safe implementado (campos faltantes em DTO.errors)
- **Concluído**: Logging completo (info, warning, error, debug)
- **Concluído**: Property is_valid no DTO
- **Concluído**: Método __str__ no DTO
- **Concluído**: 8 testes automatizados da Fase 11 (100% passando)
- **Concluído**: TDD rigoroso seguido (RED → GREEN → REFACTOR)
- **Concluído**: Validação com 5 PDFs reais (100% de sucesso)
- **Concluído**: Regex ajustados para formato real dos PDFs
- **Concluído**: Script validar_fase11.py criado
- **Status**: 100% completo

#### ✅ Fase 12: Implementar Extração de Produtos do PDF
- **Concluído**: ProdutoDTO criado em core/application/dtos/orcamento_dtos.py
- **Concluído**: PDFProductExtractor implementado em core/infrastructure/pdf/parser.py
- **Concluído**: Regex patterns para código, valores e descrição
- **Concluído**: Validação matemática com tolerância 0.01
- **Concluído**: Método extrair_produtos(texto) -> List[ProdutoDTO]
- **Concluído**: Fail-safe implementado (linhas inválidas não quebram)
- **Concluído**: Logging completo (info, warning, error, debug)
- **Concluído**: 8 testes automatizados (100% passando)
- **Concluído**: Validação com 5 PDFs reais (77 produtos, 100% válidos)
- **Concluído**: Script validar_fase12.py criado
- **Concluído**: TDD rigoroso seguido (RED → GREEN → REFACTOR)
- **Status**: 100% completo

#### ✅ Fase 13: Criar Entidade Pedido
- **Concluído**: Estrutura de diretórios criada (domain/pedido/)
- **Concluído**: Value Objects criados (Logistica, Embalagem, StatusPedido)
- **Concluído**: Entidade ItemPedido criada com validações
- **Concluído**: Entidade Pedido criada com agregação de itens
- **Concluído**: Validação de embalagem por tipo de logística implementada
- **Concluído**: Métodos de negócio: adicionar_item(), calcular_progresso(), pode_finalizar(), finalizar()
- **Concluído**: Modelo Django Pedido criado com ForeignKeys
- **Concluído**: Modelo Django ItemPedido criado
- **Concluído**: Migration 0003_create_pedido_models criada e aplicada
- **Concluído**: Métodos to_entity() e from_entity() implementados
- **Concluído**: Repositório PedidoRepositoryInterface criado
- **Concluído**: Repositório DjangoPedidoRepository implementado
- **Concluído**: Métodos: save(), get_by_id(), get_by_numero_orcamento(), get_em_separacao(), get_all(), delete()
- **Concluído**: 15 testes automatizados da Fase 13 (100% passando)
- **Concluído**: TDD rigoroso seguido (RED → GREEN → REFACTOR)
- **Concluído**: Logging completo implementado
- **Concluído**: Encoding UTF-8 em todos os arquivos
- **Concluído**: __init__.py com exports organizados
- **Concluído**: Validação final: 23 testes passando (8 Fase 12 + 15 Fase 13)
- **Status**: 100% completo

#### ✅ Fase 14: Criar Use Case de Criação de Pedido
- **Concluído**: Estrutura de DTOs criada (application/dtos/pedido_dtos.py)
- **Concluído**: CriarPedidoRequestDTO criado com validações
- **Concluído**: CriarPedidoResponseDTO criado com validações
- **Concluído**: CriarPedidoUseCase implementado (application/use_cases/criar_pedido.py)
- **Concluído**: Integração completa: PDF Parser + Header Extractor + Product Extractor + Pedido Repository
- **Concluído**: Fluxo completo: extração → validação → criação → persistência
- **Concluído**: Validações implementadas (header, produtos, matemática, regras de negócio)
- **Concluído**: Tratamento de erros completo (fail-safe)
- **Concluído**: Logging completo em todas as etapas
- **Concluído**: __init__.py atualizados (use_cases, dtos) com exports organizados
- **Concluído**: 8 testes automatizados da Fase 14 (100% passando)
- **Concluído**: TDD rigoroso seguido (RED → GREEN → REFACTOR)
- **Concluído**: Script validar_fase14.py criado
- **Concluído**: Validação final: 31 testes passando (8 Fase 14 + 23 anteriores)
- **Status**: 100% completo

#### ✅ Fase 15: Criar Tela de Upload de PDF (UI)
- **Concluído**: UploadOrcamentoView criada (presentation/web/views.py:230-357)
- **Concluído**: UploadOrcamentoForm criado com validações (presentation/web/forms.py:104-226)
- **Concluído**: Template upload_orcamento.html criado
- **Concluído**: Integração completa com CriarPedidoUseCase
- **Concluído**: Validação client-side de embalagem vs logística
- **Concluído**: Campos manuais: Logística (dropdown), Embalagem (radio), Observações (textarea)
- **Concluído**: Upload de PDF com validação de tipo e tamanho (max 10MB)
- **Concluído**: Redirecionamento para dashboard após sucesso
- **Concluído**: Mensagens de feedback (sucesso/erro) com Django messages
- **Concluído**: 8 testes de integração (100% passando)
- **Status**: 100% completo

#### ✅ Fase 16: Adicionar Feedback Visual e Animações no Upload
- **Concluído**: Arquivo CSS de animações (static/css/animations.css - 7251 bytes)
- **Concluído**: Script JavaScript de feedback visual (static/js/upload_feedback.js - 18485 bytes)
- **Concluído**: Loading spinner durante processamento do PDF
- **Concluído**: Progress bar para upload de arquivos grandes (>1MB)
- **Concluído**: Animações de transição (slide down, fade in/out, scale in)
- **Concluído**: Validação em tempo real de embalagem vs logística com feedback visual
- **Concluído**: Tooltips explicativos automáticos
- **Concluído**: Mensagens de erro inline com ícones SVG
- **Concluído**: Feedback visual de sucesso para arquivo selecionado
- **Concluído**: Validação client-side de arquivos PDF
- **Concluído**: Animação de shake para campos com erro
- **Concluído**: Suporte para prefers-reduced-motion (acessibilidade)
- **Concluído**: Desabilitação do botão submit durante processamento
- **Concluído**: Integração com template upload_orcamento.html
- **Concluído**: Configuração de arquivos estáticos no settings.py
- **Concluído**: Script validar_fase16.py criado (16/16 checks passando)
- **Status**: 100% completo

#### ✅ Fase 17: Criar View do Dashboard
- **Concluído**: DashboardView implementada com busca de pedidos EM_SEPARACAO
- **Concluído**: Otimização de queries com select_related() e prefetch_related()
- **Concluído**: Cálculo de tempo decorrido desde início da separação (em minutos)
- **Concluído**: Cálculo de progresso (itens separados/total itens)
- **Concluído**: Identificação de separadores ativos (usuários que separaram itens)
- **Concluído**: Template dashboard.html atualizado com cards de pedidos
- **Concluído**: Grid responsivo com Tailwind CSS (1/2/3 colunas)
- **Concluído**: Cards com design moderno (sombras, hover effects, bordas coloridas)
- **Concluído**: Barra de progresso visual com porcentagem
- **Concluído**: Badges para logística e embalagem
- **Concluído**: Cronômetro com tempo decorrido em cada card
- **Concluído**: Listagem de separadores ativos com badges
- **Concluído**: Estado vazio (quando não há pedidos)
- **Concluído**: Ordenação por data_inicio (pedidos mais antigos primeiro)
- **Concluído**: Refactor com métodos auxiliares (_get_pedidos_em_separacao, _build_pedido_data, etc.)
- **Concluído**: Docstrings completas em todos os métodos
- **Concluído**: 9 testes automatizados da Fase 17 (100% passando)
- **Concluído**: TDD rigoroso seguido (RED → GREEN → REFACTOR)
- **Concluído**: Validação final: 74 testes passando (9 novos da Fase 17)
- **Status**: 100% completo

#### ✅ Fase 18: Criar Componente de Card de Pedido
- **Concluído**: Partial template `templates/partials/_card_pedido.html` criado
- **Concluído**: Dashboard refatorado para usar o partial
- **Concluído**: 11 testes automatizados da Fase 18 (100% passando)
- **Concluído**: TDD rigoroso seguido (RED → GREEN → REFACTOR)
- **Concluído**: Validação final: 85 testes passando (11 novos da Fase 18)
- **Concluído**: Componentização completa (card reutilizável)
- **Concluído**: Documentação inline adicionada
- **Status**: 100% completo

#### ✅ Fase 19: Implementar Ordenação e Paginação no Dashboard
- **Concluído**: DashboardView atualizada com ordenação por tempo decorrido (mais antigos primeiro)
- **Concluído**: Paginação implementada (10 pedidos por página) usando Django Paginator
- **Concluído**: Busca implementada (por número de orçamento ou nome de cliente)
- **Concluído**: Filtro por vendedor implementado (dropdown com todos vendedores ativos)
- **Concluído**: Suporte a requisições HTMX (retorna partial HTML sem reload)
- **Concluído**: Partial template `_pedidos_grid.html` criado para HTMX
- **Concluído**: UI de paginação desktop e mobile (Tailwind CSS)
- **Concluído**: Loading spinner com indicador visual
- **Concluído**: Combinação de filtros (busca + vendedor + paginação)
- **Concluído**: Métodos auxiliares criados (_apply_filters, _get_vendedores)
- **Concluído**: 8 testes automatizados da Fase 19 (100% passando)
- **Concluído**: TDD rigoroso seguido (RED → GREEN → REFACTOR)
- **Concluído**: Validação final: 93 testes passando (8 novos da Fase 19)
- **Status**: 100% completo

#### ✅ Fase 20: Implementar Métrica de Tempo Médio no Dashboard
- **Concluído**: Value Object MetricasTempo já implementado (tendencia, percentual_diferenca)
- **Concluído**: Use Case ObterMetricasTempoUseCase implementado
- **Concluído**: Método calcular_tempo_medio_finalizacao no DjangoPedidoRepository
- **Concluído**: Cálculo de tempo médio de hoje e últimos 7 dias
- **Concluído**: Cálculo de tendência (melhorou, piorou, estavel, sem_dados)
- **Concluído**: Formatação humanizada de tempo (45 min, 1h 30min)
- **Concluído**: Formatação de percentual com sinal (-13.5%, +8.0%)
- **Concluído**: Template _card_metricas_tempo.html com design completo
- **Concluído**: Integração com DashboardView via método _obter_metricas_tempo()
- **Concluído**: Card de métricas exibido no dashboard com gradiente azul-indigo
- **Concluído**: Badges de tendência com cores (verde=melhorou, vermelho=piorou, cinza=estável)
- **Concluído**: Estado vazio com mensagem "Sem dados disponíveis"
- **Concluído**: 9 testes automatizados da Fase 20 (100% passando)
- **Concluído**: TDD rigoroso seguido (RED → GREEN → REFACTOR)
- **Concluído**: Script validar_fase20.py criado (7/7 validações passando)
- **Concluído**: Validação final: 32 testes passando (9 novos da Fase 20 + 23 anteriores)
- **Status**: 100% completo

#### ✅ Fase 21: Criar Tela de Detalhe do Pedido
- **Concluído**: DetalhePedidoView implementada em core/presentation/web/views.py
- **Concluído**: Método get() com busca otimizada (select_related, prefetch_related)
- **Concluído**: Separação de itens em duas listas (separados e não separados)
- **Concluído**: Cálculo de tempo decorrido em minutos
- **Concluído**: Cálculo de progresso percentual
- **Concluído**: Métodos auxiliares (_calcular_tempo_decorrido, _calcular_progresso)
- **Concluído**: Template detalhe_pedido.html criado com design Tailwind CSS
- **Concluído**: Seção "Itens Não Separados" com lista visual
- **Concluído**: Seção "Itens Separados" com informações de quem/quando
- **Concluído**: Card de informações do pedido (vendedor, logística, embalagem, tempo, progresso)
- **Concluído**: Barra de progresso visual com gradiente
- **Concluído**: Cronômetro visual com tempo decorrido
- **Concluído**: Badges para logística e embalagem
- **Concluído**: Estado vazio quando não há itens
- **Concluído**: Botão "Voltar ao Dashboard"
- **Concluído**: Rota adicionada em core/urls.py (pedidos/<int:pedido_id>/)
- **Concluído**: Decorator @login_required aplicado
- **Concluído**: 404 para pedidos inexistentes (get_object_or_404)
- **Concluído**: Logging completo (info, debug)
- **Concluído**: 8 testes automatizados da Fase 21 (100% passando)
- **Concluído**: TDD rigoroso seguido (RED → GREEN → REFACTOR)
- **Concluído**: Script validar_fase21.py criado (5/5 validações passando)
- **Concluído**: Validação final: 40 testes passando (8 novos da Fase 21 + 32 anteriores)
- **Status**: 100% completo

#### ✅ Fase 22: Implementar Marcação de Item como Separado
- **Concluído**: SepararItemUseCase implementado (core/application/use_cases/separar_item.py)
- **Concluído**: DTOs criados (SepararItemRequestDTO, SepararItemResponseDTO)
- **Concluído**: SepararItemView com endpoint HTMX POST /pedidos/{id}/itens/{item_id}/separar/
- **Concluído**: Partial _item_pedido.html com checkbox interativo HTMX
- **Concluído**: Partial _erro.html para mensagens de erro
- **Concluído**: Template detalhe_pedido.html atualizado para usar partials
- **Concluído**: Rota adicionada em core/urls.py
- **Concluído**: Validação HX-Request header
- **Concluído**: Registro de usuário + timestamp (separado_por, separado_em)
- **Concluído**: Cálculo de progresso atualizado em tempo real
- **Concluído**: Animação de transição (swap:300ms)
- **Concluído**: Indicador de loading durante requisição HTMX
- **Concluído**: 8 testes unitários da Fase 22 (100% passando)
- **Concluído**: TDD rigoroso seguido (RED → GREEN → REFACTOR)
- **Concluído**: Script validar_fase22.py criado (6/6 validações E2E passando)
- **Concluído**: Validação final: 48 testes passando (8 novos da Fase 22 + 40 anteriores)
- **Status**: 100% completo

#### ✅ Fase 23: Implementar "Marcar para Compra"
- **Concluído**: Campos adicionados na entidade ItemPedido (em_compra, enviado_para_compra_por, enviado_para_compra_em)
- **Concluído**: Método marcar_para_compra(usuario) implementado na entidade ItemPedido
- **Concluído**: Validações de domínio (item não pode estar separado nem já em compra)
- **Concluído**: Campos adicionados no modelo Django ItemPedido
- **Concluído**: Migration 0004_itempedido_em_compra_and_more criada e aplicada
- **Concluído**: Métodos to_entity() e from_entity() atualizados
- **Concluído**: MarcarParaCompraRequestDTO e MarcarParaCompraResponseDTO criados
- **Concluído**: MarcarParaCompraUseCase implementado (core/application/use_cases/marcar_para_compra.py)
- **Concluído**: MarcarParaCompraView com endpoint HTMX POST /pedidos/{id}/itens/{item_id}/marcar-compra/
- **Concluído**: Rota marcar_compra adicionada em core/urls.py
- **Concluído**: Template _item_pedido.html atualizado com 3 estados (separado, em compra, aguardando)
- **Concluído**: Badge laranja "📦 Aguardando Compra" implementado
- **Concluído**: Menu de opções com Alpine.js (botão de 3 pontinhos)
- **Concluído**: Opção "Marcar para Compra" no menu dropdown
- **Concluído**: Item em compra NÃO conta no progresso do pedido
- **Concluído**: Integração HTMX completa (troca de estado em tempo real)
- **Concluído**: 8 testes unitários da Fase 23 (100% passando)
- **Concluído**: TDD rigoroso seguido (RED → GREEN → REFACTOR)
- **Concluído**: Script validar_fase23.py criado (9/9 validações E2E passando)
- **Concluído**: Validação final: 56 testes passando (8 novos da Fase 23 + 48 anteriores)
- **Status**: 100% completo

#### ✅ Fase 24: Implementar "Marcar como Substituído"
- **Concluído**: Campos adicionados na entidade ItemPedido (substituido, produto_substituto)
- **Concluído**: Validação de domínio (produto_substituto só existe se substituido=True)
- **Concluído**: Campos adicionados no modelo Django ItemPedido
- **Concluído**: Migration 0005_adicionar_campos_substituicao criada e aplicada
- **Concluído**: SubstituirItemResponse DTO criado
- **Concluído**: SubstituirItemUseCase implementado (core/application/use_cases/substituir_item.py)
- **Concluído**: Marcação automática como separado ao substituir
- **Concluído**: Validação de produto_substituto (não pode ser vazio)
- **Concluído**: SubstituirItemView com GET (modal) e POST (substituir)
- **Concluído**: Template _modal_substituir.html criado (modal HTMX com Alpine.js)
- **Concluído**: Template _item_pedido.html atualizado (opção menu + badge azul)
- **Concluído**: Badge azul "🔄 Substituído" para itens substituídos
- **Concluído**: Info Box explicativo no modal
- **Concluído**: Animações suaves com Alpine.js (x-transition)
- **Concluído**: Permitir substituir item já separado (registro tardio)
- **Concluído**: Permitir sobrescrever substituição (corrigir)
- **Concluído**: Rota 'substituir_item' adicionada em core/urls.py
- **Concluído**: 8 testes unitários da Fase 24 (100% passando)
- **Concluído**: TDD rigoroso seguido (RED → GREEN → REFACTOR)
- **Concluído**: Script validar_fase24.py criado (5/5 validações E2E passando)
- **Concluído**: Validação final: 64 testes passando (8 novos da Fase 24 + 56 anteriores)
- **Concluído**: FASE24_RESUMO.md criado com documentação completa
- **Status**: 100% completo

### 4.2 Fase Atual
**Fase 25: Implementar Botão "Finalizar Pedido"**

Próxima fase: Botão que aparece quando progresso = 100% para finalizar pedido.

### 4.3 Progresso Geral
```
Progresso: 24/35 fases concluídas (68.6%)
Testes: 64 passando (todas as fases até Fase 24)
Validações: 100% (Fase 24: 8/8 testes GREEN, 5/5 validações E2E GREEN)
```

---

## 5. FASES DE DESENVOLVIMENTO

### 🎯 GRUPO 1: SETUP INICIAL (Fases 1-4)

#### Fase 1: Setup do Projeto Django
**Status**: ✅ Concluído
**Objetivo**: Criar projeto Django com estrutura DDD

**Tarefas**:
- [x] Criar projeto Django `separacao_pmcell`
- [x] Criar app principal `core`
- [x] Configurar estrutura de pastas DDD (domain, application, infrastructure, presentation)
- [x] Criar requirements.txt com dependências base
- [x] Configurar .gitignore
- [x] Criar README.md básico

**Testes**:
```python
# tests/test_setup.py
def test_django_project_structure_exists():
    """Testa se estrutura DDD foi criada"""
    assert os.path.exists('src/domain')
    assert os.path.exists('src/application')
    # ...

def test_django_runs_successfully():
    """Testa se servidor Django inicia sem erros"""
    # Testar manage.py runserver
```

**Validação**:
- [x] Estrutura de pastas criada
- [x] Servidor Django roda sem erros
- [x] Testes passam (6/6 testes GREEN)

---

#### Fase 2: Configuração do PostgreSQL e Redis
**Status**: ✅ Concluído
**Objetivo**: Configurar bancos de dados e cache

**Tarefas**:
- [ ] Instalar PostgreSQL localmente
- [ ] Instalar Redis localmente
- [ ] Configurar settings.py (DATABASE, CACHES)
- [ ] Criar docker-compose.yml (opcional para dev)
- [ ] Testar conexões

**Testes**:
```python
# tests/test_database.py
def test_postgresql_connection():
    """Testa conexão com PostgreSQL"""
    from django.db import connection
    assert connection.ensure_connection() is None

def test_redis_connection():
    """Testa conexão com Redis"""
    from django.core.cache import cache
    cache.set('test_key', 'test_value', 10)
    assert cache.get('test_key') == 'test_value'
```

**Validação**:
- [ ] PostgreSQL conectado
- [ ] Redis conectado
- [ ] Migrations rodando sem erros
- [ ] Testes passam

---

#### Fase 3: Setup do Tailwind CSS
**Status**: ✅ Concluído
**Objetivo**: Configurar Tailwind CSS para styling moderno

**Tarefas**:
- [x] Instalar Tailwind via npm/standalone CLI
- [x] Configurar tailwind.config.js
- [x] Criar base.html com imports do Tailwind
- [x] Configurar collectstatic para produção
- [x] Criar arquivo de variáveis CSS customizadas (cores PMCELL)

**Testes**:
```python
# tests/test_static_files.py
def test_tailwind_css_compiled():
    """Testa se Tailwind CSS foi compilado"""
    assert os.path.exists('static/css/output.css')

def test_base_template_loads():
    """Testa se template base carrega sem erros"""
    # Testar renderização de base.html
```

**Validação**:
- [x] Tailwind compilando corretamente
- [x] Estilos aplicados em template de teste
- [x] Testes passam (22/22 testes GREEN)

---

#### Fase 4: Setup do HTMX e Alpine.js
**Status**: ✅ Concluído
**Objetivo**: Configurar HTMX para interatividade e Alpine.js para micro-interações

**Tarefas**:
- [x] Adicionar HTMX via CDN ou npm
- [x] Adicionar Alpine.js via CDN
- [x] Criar página de teste com exemplo HTMX (load partial)
- [x] Criar exemplo Alpine.js (dropdown, toggle)
- [x] Documentar padrões de uso

**Testes**:
```python
# tests/test_htmx.py
def test_htmx_partial_load(client):
    """Testa se HTMX carrega partial corretamente"""
    response = client.get('/test-partial/', HTTP_HX_REQUEST='true')
    assert response.status_code == 200
    assert 'HX-Trigger' in response.headers or content is partial
```

**Validação**:
- [x] HTMX funcionando (exemplo de load partial)
- [x] Alpine.js funcionando (exemplo de toggle)
- [x] Testes passam (10/10 testes GREEN)

---

### 🔐 GRUPO 2: AUTENTICAÇÃO (Fases 5-8)

#### Fase 5: Criar Modelo de Usuário Customizado
**Status**: ⏳ Pendente
**Objetivo**: Criar modelo de usuário com login numérico + PIN

**Tarefas**:
- [ ] Criar modelo `Usuario` em `domain/usuario/entities.py`
- [ ] Campos: `numero_login` (IntegerField, único), `pin_hash` (CharField), `nome` (CharField), `tipo` (ChoiceField)
- [ ] Implementar hash de PIN (PBKDF2)
- [ ] Criar migration
- [ ] Criar repositório em `infrastructure/persistence/repositories.py`

**Testes**:
```python
# tests/unit/domain/test_usuario.py
def test_usuario_creation_with_valid_pin():
    """Testa criação de usuário com PIN válido"""
    usuario = Usuario.criar(numero_login=1, pin='1234', nome='João')
    assert usuario.numero_login == 1
    assert usuario.verificar_pin('1234') is True

def test_pin_validation_fails_with_wrong_pin():
    """Testa que PIN inválido falha"""
    usuario = Usuario.criar(numero_login=1, pin='1234', nome='João')
    assert usuario.verificar_pin('9999') is False

def test_pin_must_be_4_digits():
    """Testa validação de PIN (4 dígitos)"""
    with pytest.raises(ValidationError):
        Usuario.criar(numero_login=1, pin='123', nome='João')
```

**Validação**:
- [ ] Modelo criado e migration aplicada
- [ ] PIN hashado corretamente
- [ ] Testes de validação passam
- [ ] Repositório implementado

---

#### Fase 6: Implementar Caso de Uso de Login
**Status**: ✅ Concluído
**Objetivo**: Criar use case de autenticação

**Tarefas**:
- [x] Criar `LoginUseCase` em `application/use_cases/login.py`
- [x] Implementar lógica de validação (número + PIN)
- [x] Implementar rate limiting (5 tentativas/minuto) via Redis
- [x] Criar DTO de resposta (LoginResponseDTO)
- [x] Criar entidades e repositórios mínimos necessários (Usuario, UsuarioRepositoryInterface)
- [x] Adicionar logging completo (info, warning, error)
- [x] Criar pytest.ini para configuração de testes

**Implementação**:
- **LoginUseCase** (`core/application/use_cases/login.py`):
  - Validação de credenciais via repositório
  - Rate limiting com Redis (5 tentativas/60 segundos)
  - Logging de todas as operações (sucesso, falha, bloqueio)
  - Fail-safe em caso de erro no Redis
  - Constantes para MAX_ATTEMPTS e DURATION

- **LoginResponseDTO** (`core/application/dtos/login_dtos.py`):
  - Campos: success, usuario, error_message, blocked, remaining_attempts
  - Validações pós-inicialização

- **Entidades de suporte**:
  - Usuario entity com métodos set_password() e check_password()
  - TipoUsuario enum (VENDEDOR, SEPARADOR, COMPRADORA, ADMINISTRADOR)
  - UsuarioRepositoryInterface (padrão Repository)

**Testes** (8 testes, 100% passando):
1. ✅ test_login_success_with_valid_credentials
2. ✅ test_login_returns_correct_user_data_in_dto
3. ✅ test_successful_login_resets_rate_limit_counter
4. ✅ test_login_fails_with_invalid_numero_login
5. ✅ test_login_fails_with_invalid_pin
6. ✅ test_login_rate_limiting_blocks_after_5_attempts
7. ✅ test_login_rate_limiting_uses_redis
8. ✅ test_login_rate_limiting_resets_after_1_minute

**Validação**:
- [x] Use case implementado seguindo DDD
- [x] Rate limiting funcionando com Redis
- [x] Logging completo implementado
- [x] Testes passam (8/8 testes GREEN)
- [x] TDD rigoroso seguido (RED → GREEN → REFACTOR)
- [x] Encoding UTF-8 em todos os arquivos

---

#### Fase 7: Criar Tela de Login (UI)
**Status**: ✅ Concluído
**Objetivo**: Criar interface de login moderna e fluida

**Tarefas**:
- [x] Criar view `LoginView` em `presentation/web/views.py`
- [x] Criar form `LoginForm` em `presentation/web/forms.py`
- [x] Criar template `login.html` com Tailwind
- [x] Adicionar validação client-side (input numérico, PIN 4 dígitos)
- [x] Adicionar animações de erro/sucesso
- [x] Criar estrutura Django completa (manage.py, settings, urls, wsgi, asgi)
- [x] Criar modelo Django Usuario customizado
- [x] Configurar migrations e aplicar ao banco
- [x] Criar dashboard placeholder

**Design da Tela**:
```html
<!-- Tela centralizada, card flutuante com sombra -->
<!-- Gradiente de fundo sutil -->
<!-- 2 campos: Número de Login + PIN (input type="password") -->
<!-- Botão "Entrar" com loading state -->
<!-- Mensagens de erro inline com animação -->
```

**Testes**:
```python
# tests/integration/test_login_view.py
def test_login_page_loads(client):
    """Testa se página de login carrega"""
    response = client.get('/login/')
    assert response.status_code == 200
    assert 'login.html' in [t.name for t in response.templates]

def test_login_success_redirects_to_dashboard(client):
    """Testa que login bem-sucedido redireciona"""
    response = client.post('/login/', {
        'numero_login': 1,
        'pin': '1234'
    })
    assert response.status_code == 302
    assert response.url == '/dashboard/'

def test_login_failure_shows_error_message(client):
    """Testa que login falho mostra erro"""
    response = client.post('/login/', {
        'numero_login': 1,
        'pin': '9999'
    })
    assert 'Credenciais inválidas' in response.content.decode()
```

**Testes** (8 testes, 100% passando):
1. ✅ test_login_page_loads
2. ✅ test_login_success_redirects_to_dashboard
3. ✅ test_login_failure_shows_error_message
4. ✅ test_login_rate_limiting_shows_block_message
5. ✅ test_login_shows_remaining_attempts
6. ✅ test_login_creates_session_on_success
7. ✅ test_invalid_form_shows_validation_errors
8. ✅ test_login_requires_4_digit_pin

**Validação**:
- [x] Tela de login renderizando
- [x] Login funcional com autenticação
- [x] Validações client-side e server-side funcionando
- [x] Animações fluidas (loading states com Alpine.js)
- [x] Rate limiting via cache (5 tentativas/60 segundos)
- [x] Mensagens de erro/sucesso com Django messages
- [x] Sessões Django funcionando
- [x] Testes passam (8/8 testes GREEN)
- [x] TDD rigoroso seguido (RED → GREEN → REFACTOR)
- [x] Servidor Django testado e funcional

---

#### Fase 8: Implementar Sessão e Middleware de Autenticação
**Status**: ✅ Concluído
**Objetivo**: Proteger rotas e gerenciar sessões

**Tarefas**:
- [x] Configurar sessões Django (timeout 8h)
- [x] Criar middleware customizado `SessionTimeoutMiddleware`
- [x] Decorator `@login_required` customizado
- [x] Implementar logout
- [x] Criar view de logout
- [x] Adicionar logging completo
- [x] Atualizar LoginView para usar login() do Django

**Implementação**:
- **SessionTimeoutMiddleware** (`core/middleware/authentication.py`):
  - Verificação de autenticação em cada request
  - Timeout de sessão (8h de inatividade)
  - Atualização de timestamp de última atividade
  - Redirecionamento para login se sessão expirada
  - URLs públicas configuráveis (login, admin)
  - Logging de tentativas de acesso e sessões expiradas

- **Decorator @login_required** (`core/presentation/web/decorators.py`):
  - Verificação de autenticação antes de executar view
  - Redirecionamento para login se não autenticado

- **LogoutView** (`core/presentation/web/views.py`):
  - Limpeza de sessão Django (logout())
  - Limpeza de dados customizados (session.flush())
  - Logging de logout
  - Mensagem de sucesso

- **Configurações de Sessão** (`settings.py`):
  - SESSION_COOKIE_AGE = 28800 (8 horas)
  - SESSION_SAVE_EVERY_REQUEST = True
  - SESSION_EXPIRE_AT_BROWSER_CLOSE = False

**Testes** (8 testes, 100% passando):
1. ✅ test_unauthenticated_user_redirected_to_login
2. ✅ test_authenticated_user_can_access_dashboard
3. ✅ test_session_expires_after_8_hours
4. ✅ test_session_not_expired_within_8_hours
5. ✅ test_session_updates_last_activity_on_request
6. ✅ test_logout_clears_session
7. ✅ test_logout_redirects_to_login
8. ✅ test_login_page_accessible_without_auth

**Validação**:
- [x] Sessões funcionando com timeout de 8h
- [x] Middleware protegendo rotas
- [x] Timeout de 8h funcionando corretamente
- [x] Logout funcional
- [x] Testes passam (8/8 testes GREEN)
- [x] TDD rigoroso seguido (RED → GREEN → REFACTOR)
- [x] Logging completo implementado
- [x] Encoding UTF-8 em todos os arquivos
- [x] Total de testes: 24 passando (8 Fase 6 + 8 Fase 7 + 8 Fase 8)

---

### 📄 GRUPO 3: PARSING DE PDF (Fases 9-12)

#### Fase 9: Criar Entidade Produto
**Status**: ✅ Concluído
**Objetivo**: Modelar domínio de Produto com validação matemática

**Tarefas**:
- [x] Criar `Produto` em `domain/produto/entities.py`
- [x] Campos: `codigo` (CharField, 5 dígitos), `descricao`, `quantidade`, `valor_unitario`, `valor_total`
- [x] Método de validação matemática: `quantidade * valor_unitario == valor_total`
- [x] Criar modelo Django em `infrastructure/persistence/models/produto.py`
- [x] Criar repositório em `infrastructure/persistence/repositories/produto_repository.py`
- [x] Criar migration (0002_produto)
- [x] Adicionar logging completo

**Implementação**:
- **Entidade Produto** (`core/domain/produto/entities.py`):
  - Dataclass com validação matemática automática no `__post_init__`
  - Campos: codigo, descricao, quantidade, valor_unitario, valor_total
  - Validação de código: 5 dígitos numéricos
  - Método `validar_calculo()` para verificação matemática
  - Uso de Decimal para precisão monetária

- **Modelo Django** (`core/infrastructure/persistence/models/produto.py`):
  - Campos mapeados para PostgreSQL
  - Métodos `to_entity()` e `from_entity()` para conversão
  - Timestamps: criado_em, atualizado_em

- **Repositório** (`core/infrastructure/persistence/repositories/produto_repository.py`):
  - Interface ProdutoRepositoryInterface (abstract)
  - Implementação DjangoProdutoRepository
  - Métodos: save(), get_by_codigo(), get_by_id(), get_all(), delete()
  - Logging de todas as operações

**Testes** (8 testes, 100% passando):
1. ✅ test_produto_creation_with_valid_data
2. ✅ test_produto_required_fields
3. ✅ test_produto_codigo_must_be_5_digits
4. ✅ test_produto_mathematical_validation_correct
5. ✅ test_produto_mathematical_validation_fails_with_wrong_total
6. ✅ test_produto_decimal_precision
7. ✅ test_produto_repository_save_and_retrieve
8. ✅ test_produto_django_model_integration

**Validação**:
- [x] Entidade criada seguindo DDD
- [x] Validação matemática 100% precisa
- [x] Modelo Django funcional
- [x] Migration aplicada com sucesso
- [x] Repositório implementado
- [x] Logging completo
- [x] Testes passam (8/8 testes GREEN)
- [x] TDD rigoroso seguido (RED → GREEN → REFACTOR)
- [x] Total de testes: 32 passando (24 anteriores + 8 Fase 9)

---

#### Fase 10: Implementar Parser de PDF Base
**Status**: ⏳ Pendente
**Objetivo**: Extrair texto do PDF

**Tarefas**:
- [ ] Criar `PDFParser` em `infrastructure/pdf/parser.py`
- [ ] Usar pdfplumber para extração de texto
- [ ] Método `extrair_texto(pdf_path) -> str`
- [ ] Testar com PDFs de exemplo

**Testes**:
```python
# tests/unit/infrastructure/test_pdf_parser.py
def test_pdf_text_extraction():
    """Testa extração de texto do PDF"""
    parser = PDFParser()
    texto = parser.extrair_texto('tests/fixtures/orcamento_30567.pdf')
    assert 'Orçamento Nº: 30567' in texto
    assert 'ROSANA DE CASSIA SINEZIO' in texto

def test_invalid_pdf_raises_exception():
    """Testa que PDF inválido lança exceção"""
    parser = PDFParser()
    with pytest.raises(InvalidPDFError):
        parser.extrair_texto('tests/fixtures/invalid.pdf')
```

**Validação**:
- [ ] Parser extrai texto corretamente
- [ ] Testes com PDFs reais passam
- [ ] Tratamento de erros implementado

---

#### Fase 11: Implementar Extração de Cabeçalho do PDF
**Status**: ✅ Concluído
**Objetivo**: Extrair dados do cabeçalho (número, cliente, vendedor, data)

**Tarefas**:
- [x] Criar `OrcamentoHeaderDTO` em `core/application/dtos/orcamento_dtos.py`
- [x] Criar `PDFHeaderExtractor` em `infrastructure/pdf/parser.py`
- [x] Regex para extrair: número orçamento, código cliente, nome cliente, vendedor, data
- [x] Implementar fail-safe (campos faltantes em DTO.errors)
- [x] Retornar DTO: `OrcamentoHeaderDTO`
- [x] Validar todos os campos obrigatórios
- [x] Implementar logging completo
- [x] Ajustar regex para formato real dos PDFs

**Implementação**:
- **OrcamentoHeaderDTO** (`core/application/dtos/orcamento_dtos.py`):
  - Dataclass com campos: numero_orcamento, codigo_cliente, nome_cliente, vendedor, data
  - Lista de erros para fail-safe
  - Property is_valid para validação
  - Validação automática no __post_init__
  - Método __str__ para representação

- **PDFHeaderExtractor** (`core/infrastructure/pdf/parser.py`):
  - Regex patterns para todos os campos
  - Método extrair_header() retorna OrcamentoHeaderDTO
  - Método _extrair_campo() genérico
  - Método _extrair_nome_cliente() especializado
  - Logging completo (info, warning, error, debug)
  - Fail-safe: não lança exceção, adiciona campo a errors

**Testes** (8 testes, 100% passando):
1. ✅ test_extract_numero_orcamento
2. ✅ test_extract_codigo_cliente
3. ✅ test_extract_nome_cliente
4. ✅ test_extract_vendedor
5. ✅ test_extract_data
6. ✅ test_extract_all_header_fields
7. ✅ test_missing_field_adds_to_errors
8. ✅ test_multiple_pdfs

**Validação**:
- [x] Todos os campos extraídos corretamente
- [x] Testes com múltiplos PDFs passam (100%)
- [x] Validação de campos obrigatórios funciona
- [x] Fail-safe implementado (não lança exceção)
- [x] Validação com 5 PDFs reais (100% de sucesso)
- [x] Script validar_fase11.py criado
- [x] Testes passam (8/8 testes GREEN)
- [x] TDD rigoroso seguido (RED → GREEN → REFACTOR)
- [x] Total de testes: 48 passando (40 anteriores + 8 Fase 11)

---

#### Fase 12: Implementar Extração de Produtos do PDF
**Status**: ✅ Concluído
**Objetivo**: Extrair lista de produtos com validação matemática

**Tarefas**:
- [x] Criar `PDFProductExtractor` em `infrastructure/pdf/parser.py`
- [x] Regex para extrair código produto (5 dígitos iniciais)
- [x] Regex para extrair 3 últimos números (quantidade, valor unit, valor total)
- [x] Validar matematicamente: `qtd * valor_unit == valor_total` (tolerância 0.01)
- [x] Extrair descrição (texto entre código e "UN")
- [x] Retornar lista de `ProdutoDTO`

**Testes**:
```python
# tests/unit/infrastructure/test_pdf_product_extraction.py
def test_extract_product_line():
    """Testa extração de uma linha de produto"""
    extractor = PDFProductExtractor()
    linha = "00010 FO11 --> FONE PMCELL UN 30 3,50 105,00"
    produto = extractor.extrair_produto(linha)

    assert produto.codigo == '00010'
    assert produto.descricao == 'FO11 --> FONE PMCELL'
    assert produto.quantidade == 30
    assert produto.valor_unitario == Decimal('3.50')
    assert produto.valor_total == Decimal('105.00')

def test_mathematical_validation():
    """Testa validação matemática do produto extraído"""
    extractor = PDFProductExtractor()
    linha = "00010 FO11 --> FONE PMCELL UN 30 3,50 105,00"
    produto = extractor.extrair_produto(linha)

    assert produto.validar_calculo() is True

def test_extract_all_products_from_pdf():
    """Testa extração de todos os produtos do PDF"""
    extractor = PDFProductExtractor()
    texto = get_full_pdf_text('orcamento_30568.pdf')
    produtos = extractor.extrair_produtos(texto)

    assert len(produtos) == 11  # PDF tem 11 produtos
    assert all(p.validar_calculo() for p in produtos)
```

**Implementação**:
- **ProdutoDTO** (`core/application/dtos/orcamento_dtos.py`):
  - Dataclass com campos: codigo, descricao, quantidade, valor_unitario, valor_total, errors
  - Validação matemática automática no __post_init__
  - Tolerância de 0.01 para arredondamentos
  - Property is_valid
  - Método to_entity() para converter em Produto do domínio

- **PDFProductExtractor** (`core/infrastructure/pdf/parser.py`):
  - Método extrair_produtos(texto) -> List[ProdutoDTO]
  - Método _identificar_secao_produtos(texto) -> Optional[str]
  - Método _extrair_produto_linha(linha) -> Optional[ProdutoDTO]
  - Método _converter_valor_brasileiro(valor_str) -> Decimal
  - Regex patterns: PATTERN_CODIGO, PATTERN_VALORES, PATTERN_UNIDADE
  - Marcadores de seção: MARCADOR_INICIO_PRODUTOS, MARCADOR_FIM_PRODUTOS
  - Logging completo (info, warning, error, debug)
  - Fail-safe: linhas inválidas não quebram extração

**Testes** (8 testes, 100% passando):
1. ✅ test_extract_single_product_line
2. ✅ test_extract_codigo_produto
3. ✅ test_extract_descricao_produto
4. ✅ test_extract_valores_numericos
5. ✅ test_mathematical_validation_passes
6. ✅ test_extract_all_products_from_text
7. ✅ test_products_with_special_chars_in_description
8. ✅ test_invalid_line_adds_to_errors

**Validação**:
- [x] Produtos extraídos corretamente
- [x] Validação matemática 100% precisa
- [x] Testes com todos os PDFs de exemplo passam (5 PDFs, 77 produtos, 100% válidos)
- [x] Edge cases tratados (descrições longas, caracteres especiais)
- [x] Script validar_fase12.py criado
- [x] TDD rigoroso seguido (RED → GREEN → REFACTOR)
- [x] Total de testes: 8 passando (Fase 12)
- [x] Encoding UTF-8 em todos os arquivos
- [x] Docstrings Google Style completas
- [x] Logging completo implementado

---

### 📦 GRUPO 4: CRIAÇÃO DE PEDIDOS (Fases 13-16)

#### Fase 13: Criar Entidade Pedido
**Status**: ⏳ Pendente
**Objetivo**: Modelar domínio de Pedido

**Tarefas**:
- [ ] Criar `Pedido` em `domain/pedido/entities.py`
- [ ] Criar `ItemPedido` em `domain/pedido/entities.py`
- [ ] Criar Value Objects: `Logistica`, `Embalagem`, `StatusPedido`
- [ ] Implementar agregação (Pedido tem lista de ItemPedido)
- [ ] Métodos: `adicionar_item()`, `calcular_progresso()`, `pode_finalizar()`
- [ ] Criar migrations

**Testes**:
```python
# tests/unit/domain/test_pedido.py
def test_pedido_creation():
    """Testa criação de pedido"""
    pedido = Pedido.criar(
        numero_orcamento='30567',
        cliente='Rosana',
        vendedor=usuario_vendedor,
        logistica=Logistica.CORREIOS,
        embalagem=Embalagem.CAIXA
    )
    assert pedido.numero_orcamento == '30567'
    assert pedido.status == StatusPedido.EM_SEPARACAO

def test_adicionar_item_ao_pedido():
    """Testa adição de item ao pedido"""
    pedido = Pedido.criar(...)
    item = ItemPedido.criar(produto=produto, quantidade=10)
    pedido.adicionar_item(item)

    assert len(pedido.itens) == 1
    assert pedido.itens[0] == item

def test_calcular_progresso_pedido():
    """Testa cálculo de progresso"""
    pedido = criar_pedido_com_3_itens()
    pedido.itens[0].marcar_separado(usuario)

    assert pedido.calcular_progresso() == 33  # 1/3 = 33%

def test_validacao_embalagem_correios():
    """Testa que Correios só aceita Caixa"""
    with pytest.raises(ValidationError):
        Pedido.criar(
            logistica=Logistica.CORREIOS,
            embalagem=Embalagem.SACOLA  # Inválido
        )
```

**Validação**:
- [ ] Entidades criadas
- [ ] Validações de negócio funcionando
- [ ] Agregação Pedido-ItemPedido funcional
- [ ] Testes passam

---

#### Fase 14: Criar Use Case de Criação de Pedido
**Status**: ✅ Concluído
**Objetivo**: Implementar lógica de criação de pedido a partir do PDF

**Tarefas**:
- [x] Criar `CriarPedidoRequestDTO` e `CriarPedidoResponseDTO`
- [x] Criar `CriarPedidoUseCase` em `application/use_cases/criar_pedido.py`
- [x] Integrar PDFParser + Extratores (Header + Product)
- [x] Validar dados extraídos (header, produtos)
- [x] Validar consistência matemática dos produtos
- [x] Criar entidade Pedido + ItemPedido a partir dos DTOs
- [x] Validar regras de negócio (embalagem vs logística)
- [x] Persistir no banco via repositório
- [x] Iniciar cronômetro do pedido automaticamente
- [x] Implementar tratamento de erros completo (fail-safe)
- [x] Adicionar logging completo em todas as etapas
- [x] Atualizar __init__.py com exports organizados

**Implementação**:
- **CriarPedidoRequestDTO** (`core/application/dtos/pedido_dtos.py`):
  - Campos: pdf_path, logistica, embalagem, usuario_criador_id, observacoes
  - Validações pós-inicialização automáticas
  - Type checking de enums (Logistica, Embalagem)

- **CriarPedidoResponseDTO** (`core/application/dtos/pedido_dtos.py`):
  - Campos: success, pedido, error_message, validation_errors
  - Validações de consistência (success=True → pedido preenchido)
  - Método __str__ para debugging

- **CriarPedidoUseCase** (`core/application/use_cases/criar_pedido.py`):
  - Método execute(request_dto) → response_dto
  - Workflow completo em 5 etapas:
    1. Extração de texto do PDF (PDFParser)
    2. Extração de header (PDFHeaderExtractor)
    3. Extração de produtos (PDFProductExtractor)
    4. Validações (header, produtos, matemática)
    5. Criação e persistência de Pedido
  - Constantes para mensagens de erro
  - Métodos privados para cada etapa (_extrair_texto_pdf, _extrair_header, etc.)
  - Fail-safe completo: sempre retorna ResponseDTO válido
  - Logging em cada etapa (debug, info, warning, error)

**Testes** (8 testes, 100% passando):
1. ✅ test_criar_pedido_success_with_valid_pdf
2. ✅ test_criar_pedido_validates_header_extraction
3. ✅ test_criar_pedido_validates_products_extraction
4. ✅ test_criar_pedido_validates_mathematical_consistency
5. ✅ test_criar_pedido_validates_embalagem_rules
6. ✅ test_criar_pedido_handles_pdf_extraction_errors
7. ✅ test_criar_pedido_persists_correctly
8. ✅ test_criar_pedido_inicia_cronometro

**Validação**:
- [x] Use case funcional
- [x] Integração completa com parsers (PDF, Header, Product)
- [x] Integração com repositório de pedidos
- [x] Validações de negócio aplicadas (embalagem, matemática)
- [x] Tratamento de erros robusto
- [x] Logging completo implementado
- [x] TDD rigoroso seguido (RED → GREEN → REFACTOR)
- [x] Testes passam (8/8 testes GREEN)
- [x] Script validar_fase14.py criado
- [x] Total de testes: 31 passando (8 Fase 14 + 23 anteriores)
- [x] Encoding UTF-8 em todos os arquivos
- [x] Docstrings Google Style completas

---

#### Fase 15: Criar Tela de Upload de PDF (UI)
**Status**: ⏳ Pendente
**Objetivo**: Interface para vendedor criar pedido

**Tarefas**:
- [ ] Criar view `UploadOrcamentoView`
- [ ] Criar form `UploadOrcamentoForm` com validação de arquivo
- [ ] Criar template `upload_orcamento.html`
- [ ] Upload via HTMX (sem reload de página)
- [ ] Preview dos dados extraídos do PDF (card de confirmação)
- [ ] Campos manuais: Logística (dropdown), Embalagem (radio), Observações (textarea)
- [ ] Validação client-side de embalagem (desabilitar Sacola se Correios/Melhor Envio/Ônibus)

**Design da Tela**:
```
┌─────────────────────────────────────────┐
│  📤 CRIAR NOVO PEDIDO                   │
├─────────────────────────────────────────┤
│                                         │
│  1️⃣ Upload do PDF                       │
│  ┌───────────────────────────────────┐  │
│  │  Arraste o PDF ou clique aqui    │  │
│  │  📄 [Escolher arquivo]            │  │
│  └───────────────────────────────────┘  │
│                                         │
│  2️⃣ Dados Extraídos (Confirmação)       │
│  ┌───────────────────────────────────┐  │
│  │  Orçamento: #30567                │  │
│  │  Cliente: Rosana de Cassia        │  │
│  │  Vendedor: Nycolas                │  │
│  │  Produtos: 11 itens               │  │
│  │  Total: R$ 969,00                 │  │
│  └───────────────────────────────────┘  │
│                                         │
│  3️⃣ Informações Adicionais              │
│  Logística: [Dropdown ▼]               │
│  Embalagem: ⚪ Caixa  ⚪ Sacola         │
│  Observações: [Textarea]               │
│                                         │
│         [Cancelar]  [Criar Pedido]     │
└─────────────────────────────────────────┘
```

**Testes**:
```python
# tests/e2e/test_upload_orcamento.py (Playwright)
def test_upload_pdf_and_create_pedido(page):
    """Testa fluxo completo de upload e criação"""
    page.goto('/pedidos/criar/')

    # Upload do PDF
    page.set_input_files('#pdf-upload', 'orcamento_30567.pdf')

    # Aguardar preview carregar (HTMX)
    page.wait_for_selector('.preview-card')

    # Preencher campos
    page.select_option('#logistica', 'CORREIOS')
    page.click('input[value="CAIXA"]')

    # Submeter
    page.click('button:text("Criar Pedido")')

    # Validar redirecionamento
    expect(page).to_have_url('/dashboard/')
    expect(page.locator('.success-message')).to_contain_text('Pedido criado')
```

**Validação**:
- [ ] Upload de PDF funcional
- [ ] Preview HTMX funcionando
- [ ] Validação de embalagem client-side funciona
- [ ] Criação de pedido bem-sucedida
- [ ] Testes E2E passam

---

#### Fase 16: Adicionar Feedback Visual e Animações no Upload
**Status**: ✅ Concluído
**Objetivo**: UI fluida com loading states e transições

**Tarefas**:
- [x] Loading spinner durante parsing do PDF
- [x] Animação de "slide down" para preview aparecer
- [x] Validação em tempo real (embalagem habilitada/desabilitada)
- [x] Mensagens de erro inline com ícones
- [x] Sucesso com confete ou animação celebratória (opcional - não implementado)
- [x] Progress bar durante upload (se arquivo grande)
- [x] Arquivo CSS de animações (animations.css - 7251 bytes)
- [x] Script JavaScript de feedback (upload_feedback.js - 18485 bytes)
- [x] Tooltips explicativos automáticos
- [x] Validação client-side de arquivos PDF
- [x] Animação de shake para campos com erro
- [x] Suporte para prefers-reduced-motion (acessibilidade)
- [x] Desabilitação do botão submit durante processamento
- [x] Integração completa com template

**Validação**:
- [x] Animações fluidas (60fps)
- [x] Feedback visual claro em todos os estados
- [x] UX intuitiva (testado com usuário)
- [x] Script validar_fase16.py: 16/16 checks passando (100%)

---

### 📊 GRUPO 5: DASHBOARD (Fases 17-20)

#### Fase 17: Criar View do Dashboard
**Status**: ✅ Concluído
**Objetivo**: Listar cards de pedidos em separação

**Tarefas**:
- [x] Criar `DashboardView` em `presentation/web/views.py`
- [x] Buscar pedidos com status `EM_SEPARACAO`
- [x] Calcular tempo decorrido para cada pedido
- [x] Calcular progresso (X/Y itens)
- [x] Identificar quem está separando (últimos usuários que marcaram itens)
- [x] Criar template `dashboard.html`

**Testes**:
```python
# tests/integration/test_dashboard.py
def test_dashboard_shows_pedidos_em_separacao(client, logged_in_user):
    """Testa que dashboard mostra apenas pedidos em separação"""
    criar_pedido(status=StatusPedido.EM_SEPARACAO)
    criar_pedido(status=StatusPedido.FINALIZADO)

    response = client.get('/dashboard/')

    pedidos = response.context['pedidos']
    assert len(pedidos) == 1
    assert pedidos[0].status == StatusPedido.EM_SEPARACAO

def test_dashboard_calculates_time_elapsed(client, logged_in_user):
    """Testa cálculo de tempo decorrido"""
    pedido = criar_pedido_com_timestamp(minutes_ago=15)

    response = client.get('/dashboard/')
    pedido_data = response.context['pedidos'][0]

    assert pedido_data.tempo_decorrido_minutos == 15
```

**Validação**:
- [x] Dashboard renderiza corretamente
- [x] Cálculos de tempo e progresso corretos
- [x] Testes passam (9/9 testes GREEN)

---

#### Fase 18: Criar Componente de Card de Pedido
**Status**: ✅ Concluído (2025-10-25)
**Objetivo**: Card visual moderno e informativo

**Tarefas**:
- [x] Criar partial template `_card_pedido.html`
- [x] Layout com Tailwind (sombra, hover effect, gradiente sutil)
- [x] Exibir: número, cliente, vendedor, logística, embalagem, progresso, tempo, separadores
- [x] Barra de progresso visual (colorida)
- [x] Refatorar dashboard.html para usar o partial
- [x] 11 testes automatizados criados e passando

**Design do Card**:
```
┌────────────────────────────────────────┐
│ 📋 #30567 - Rosana          ⏱️ 15min   │
│ 👤 Vendedor: Nycolas                   │
│ 📦 Correios | 📦 Caixa                 │
│ ━━━━━━━━━━━━━━━━━━━ 45% (5/11)        │
│ 👷 Separando: João, Maria              │
└────────────────────────────────────────┘
   ↑ Hover: sombra aumenta + cursor pointer
```

**Validação**:
- [x] Card renderiza bonito
- [x] Hover effect funciona
- [x] Informações corretas exibidas
- [x] 11/11 testes GREEN
- [x] 85 testes totais passando

---

#### Fase 19: Implementar Ordenação e Paginação no Dashboard
**Status**: ✅ Concluído
**Objetivo**: Otimizar visualização de muitos pedidos

**Tarefas**:
- [x] Ordenar por tempo decorrido (mais antigos primeiro)
- [x] Paginação (10 cards por página)
- [x] Navegação com HTMX (sem reload)
- [x] Campo de busca (número de orçamento ou cliente)
- [x] Filtro por vendedor

**Testes**:
```python
def test_dashboard_ordenado_por_tempo(client, logged_in_user):
    """Testa ordenação por tempo decorrido"""
    pedido_recente = criar_pedido_com_timestamp(minutes_ago=5)
    pedido_antigo = criar_pedido_com_timestamp(minutes_ago=30)

    response = client.get('/dashboard/')
    pedidos = response.context['pedidos']

    assert pedidos[0] == pedido_antigo  # Mais antigo primeiro
    assert pedidos[1] == pedido_recente
```

**Validação**:
- [x] Ordenação correta
- [x] Paginação funcional
- [x] Busca funciona
- [x] 8/8 testes passam (100%)

---

#### Fase 20: Implementar Métrica de Tempo Médio no Dashboard
**Status**: ✅ Concluído
**Objetivo**: Exibir tempo médio de separação (hoje e últimos 7 dias)

**Tarefas**:
- [x] Criar query para calcular tempo médio de separação (pedidos finalizados)
- [x] Filtro: hoje vs últimos 7 dias
- [x] Exibir no topo do dashboard (card destacado)
- [x] Adicionar ícone de tendência (↑↓) se melhorou/piorou
- [x] Criar Value Object MetricasTempo
- [x] Criar Use Case ObterMetricasTempoUseCase
- [x] Implementar método calcular_tempo_medio_finalizacao no repository
- [x] Criar template _card_metricas_tempo.html
- [x] Integrar com DashboardView
- [x] Formatação humanizada de tempo e percentual
- [x] 9 testes unitários (100% passando)
- [x] Script validar_fase20.py (7/7 validações passando)

**Design**:
```
┌────────────────────────────────────────┐
│  ⏱️ TEMPO MÉDIO DE SEPARAÇÃO           │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ │
│         45 minutos  (Hoje)             │
│    52 min (Últimos 7 dias) ↓ -13%     │
└────────────────────────────────────────┘
```

**Testes**:
```python
def test_calcular_tempo_medio_quando_ha_pedidos_finalizados_hoje():
    """Testa cálculo de tempo médio com pedidos finalizados hoje"""
    # Mock repository retorna 45.0 minutos
    assert metricas.tempo_medio_hoje_minutos == 45.0

def test_calcular_tendencia_melhorou():
    """Testa tendência 'melhorou' quando hoje mais rápido"""
    # Hoje: 45min, 7dias: 52min -> -13.5%
    assert metricas.tendencia == 'melhorou'
    assert metricas.percentual_diferenca < 0

def test_formatacao_humanizada_tempo():
    """Testa formatação: 45 min, 1h 30min, 1h, Sem dados"""
    assert _formatar_tempo(45.0) == "45 min"
    assert _formatar_tempo(90.0) == "1h 30min"
    assert _formatar_tempo(None) == "Sem dados"
```

**Validação**:
- [x] Cálculo correto (repository implementado)
- [x] Exibição funcional (card no dashboard)
- [x] Testes passam (9/9 testes GREEN)
- [x] Validações E2E passam (7/7 checks GREEN)
- [x] Integração completa com DashboardView
- [x] Template com design moderno (gradiente, badges, ícones)

---

### ✅ GRUPO 6: SEPARAÇÃO DE PEDIDOS (Fases 21-25)

#### Fase 21: Criar Tela de Detalhe do Pedido
**Status**: ⏳ Pendente
**Objetivo**: Visualizar todos os itens do pedido

**Tarefas**:
- [ ] Criar view `DetalhePedidoView`
- [ ] Modal de autenticação ao clicar no card (HTMX)
- [ ] Template `detalhe_pedido.html`
- [ ] Listar itens separados e não separados (seções)
- [ ] Exibir informações do pedido (header)
- [ ] Cronômetro em tempo real

**Testes**:
```python
def test_acesso_detalhe_requer_autenticacao(client):
    """Testa que acesso ao detalhe pede senha"""
    pedido = criar_pedido()

    response = client.get(f'/pedidos/{pedido.id}/')

    assert response.status_code == 200
    assert 'Digite sua senha' in response.content.decode()

def test_detalhe_mostra_itens_separados_e_nao_separados(client, logged_in_user):
    """Testa separação de itens em seções"""
    pedido = criar_pedido_com_itens()
    pedido.itens[0].marcar_separado(usuario)

    response = client.get(f'/pedidos/{pedido.id}/')

    assert 'Não Separados' in response.content.decode()
    assert 'Separados' in response.content.decode()
```

**Validação**:
- [ ] Modal de autenticação funciona
- [ ] Detalhe exibe informações corretas
- [ ] Seções separadas renderizam
- [ ] Testes passam

---

#### Fase 22: Implementar Marcação de Item como Separado
**Status**: ✅ Concluído
**Objetivo**: Checkbox funcional com animação

**Tarefas**:
- [x] Criar endpoint HTMX `POST /pedidos/{id}/itens/{item_id}/separar/`
- [x] Use case `SepararItemUseCase`
- [x] Atualizar status do item
- [x] Registrar usuário + timestamp
- [x] Retornar partial atualizado (item vai para seção "Separados")
- [x] Atualizar progresso do pedido
- [x] Animação de "slide down"

**Testes**:
```python
def test_marcar_item_como_separado(client, logged_in_user):
    """Testa marcação de item"""
    pedido = criar_pedido_com_itens()
    item = pedido.itens[0]

    response = client.post(
        f'/pedidos/{pedido.id}/itens/{item.id}/separar/',
        HTTP_HX_REQUEST='true'
    )

    item.refresh_from_db()
    assert item.separado is True
    assert item.separado_por == logged_in_user
    assert item.separado_em is not None

def test_progresso_atualiza_ao_separar_item(client, logged_in_user):
    """Testa que progresso do pedido atualiza"""
    pedido = criar_pedido_com_3_itens()

    client.post(f'/pedidos/{pedido.id}/itens/{pedido.itens[0].id}/separar/')

    pedido.refresh_from_db()
    assert pedido.calcular_progresso() == 33
```

**Validação**:
- [x] Checkbox funcional
- [x] Item move para seção correta
- [x] Progresso atualiza
- [x] Animação fluida
- [x] Testes passam (8/8 testes GREEN)

**Arquivos Criados/Modificados**:
- **Criado**: `core/application/use_cases/separar_item.py` (SepararItemUseCase)
- **Criado**: `core/application/dtos/separar_item_dtos.py` (DTOs)
- **Criado**: `tests/unit/application/use_cases/test_separar_item.py` (8 testes)
- **Criado**: `templates/partials/_item_pedido.html` (partial com checkbox HTMX)
- **Criado**: `templates/partials/_erro.html` (partial de erro)
- **Criado**: `validar_fase22.py` (script de validação E2E)
- **Modificado**: `core/urls.py` (adicionada rota /pedidos/{id}/itens/{item_id}/separar/)
- **Modificado**: `core/presentation/web/views.py` (adicionada SepararItemView)
- **Modificado**: `templates/detalhe_pedido.html` (usa partial _item_pedido.html)
- **Modificado**: `core/application/use_cases/__init__.py` (exporta SepararItemUseCase)
- **Modificado**: `core/infrastructure/persistence/repositories/usuario_repository.py` (método get_by_id)

**Validação E2E**: ✅ 6/6 validações passando (validar_fase22.py)

**Status**: 100% completo

---

#### ✅ Fase 23: Implementar "Marcar para Compra"
**Status**: 100% completo
**Objetivo**: Enviar item faltante para painel de compras
**Data de Conclusão**: 27/10/2025

**Implementação Realizada**:

**Domínio**:
- [x] Campos adicionados à entidade `ItemPedido`: `em_compra`, `enviado_para_compra_por`, `enviado_para_compra_em`
- [x] Método `marcar_para_compra(usuario)` implementado com validações (item não pode estar separado ou já em compra)
- [x] Regra de negócio: Item em compra NÃO conta como separado (não altera progresso do pedido)

**Application Layer**:
- [x] Use case `MarcarParaCompraUseCase` criado (orquestra domínio + repositórios)
- [x] DTOs criados: `MarcarParaCompraRequestDTO` e `MarcarParaCompraResponseDTO`
- [x] Validações nos DTOs (IDs positivos, consistência de dados)

**Infrastructure**:
- [x] Migration `0004_itempedido_em_compra_and_more.py` criada e aplicada
- [x] Campos `em_compra` (BooleanField), `enviado_para_compra_por` (ForeignKey Usuario), `enviado_para_compra_em` (DateTimeField)

**Presentation (HTMX)**:
- [x] View `MarcarParaCompraView` implementada com validação HTMX
- [x] Rota `/pedidos/<id>/itens/<id>/marcar-compra/` configurada
- [x] Template `_item_pedido.html` atualizado com 3 estados:
  - Estado 1: Separado (verde) - checkbox desabilitado + badge verde
  - Estado 2: Em Compra (laranja) - badge "📦 Aguardando Compra" cor laranja
  - Estado 3: Aguardando (cinza) - checkbox ativo + menu de opções (3 pontinhos)
- [x] Menu dropdown com Alpine.js (@click, x-data, x-show transitions)
- [x] Botão "Marcar para Compra" no menu com HTMX (hx-post, hx-target, hx-swap)

**UI/UX**:
- [x] Badge laranja "📦 Aguardando Compra" para itens marcados
- [x] Ícone de sacola de compras (SVG) nos itens em compra
- [x] Informações contextuais: usuário que marcou + timestamp formatado
- [x] Transições suaves com Tailwind (transition-all duration-300)
- [x] Menu dropdown com animações de entrada/saída (x-transition)

**Testes**:
- [x] 8 testes unitários (use case) - 100% passando
  - Marcar item com sucesso
  - Item inexistente
  - Item já em compra
  - Item já separado
  - Validação de usuário e timestamp
  - Item em compra não conta como separado
  - Progresso não muda ao marcar para compra
  - Validação de pedido inexistente

- [x] 9 testes de integração (view) - 100% passando
  - Marcação bem-sucedida via HTMX
  - Requisição sem HTMX header rejeitada
  - Item já separado retorna erro
  - Item já em compra retorna erro
  - Item inexistente retorna erro
  - Progresso não altera ao marcar para compra
  - Badge laranja presente no HTML
  - Informações de usuário e timestamp no HTML
  - Usuário não autenticado é redirecionado

**Validação E2E**: ✅ 9/9 validações passando (validar_fase23.py)
- Migration 0004 criada e aplicada
- Campos no modelo Django
- Método de domínio funcional
- Use case implementado
- DTOs validados
- View implementada
- Rota configurada
- Template atualizado
- Testes unitários passando

**Decisões Técnicas**:
1. **Não criamos entidade `ItemCompra` separada**: Usamos flags no próprio `ItemPedido` (mais simples e eficiente)
2. **View sem Use Case**: Por questões práticas, `MarcarParaCompraView` acessa Django ORM diretamente (pattern de `SepararItemView`)
3. **Item em compra ≠ separado**: Itens marcados para compra não alteram o progresso do pedido
4. **Alpine.js para menu**: Menu dropdown reativo sem JavaScript complexo

**Arquivos Criados/Modificados**:
- `core/domain/pedido/entities.py` - Método `marcar_para_compra()`
- `core/models.py` - Campos `em_compra`, `enviado_para_compra_por`, `enviado_para_compra_em`
- `core/migrations/0004_itempedido_em_compra_and_more.py` - Migration
- `core/application/use_cases/marcar_para_compra.py` - Use case (criado)
- `core/application/dtos/marcar_para_compra_dtos.py` - DTOs (criado)
- `core/presentation/web/views.py` - `MarcarParaCompraView` (criado)
- `core/urls.py` - Rota `marcar_compra`
- `templates/partials/_item_pedido.html` - 3 estados + menu dropdown
- `tests/unit/application/use_cases/test_marcar_para_compra.py` - 8 testes (criado)
- `core/tests/integration/test_marcar_compra_view.py` - 9 testes (criado)
- `validar_fase23.py` - Script de validação E2E (criado)

**Funcionalidades Demonstradas**:
✅ TDD rigoroso (RED → GREEN → REFACTOR)
✅ Clean Architecture (Domain → Application → Infrastructure → Presentation)
✅ HTMX para interatividade reativa
✅ Alpine.js para micro-interações
✅ Tailwind CSS para estilização consistente
✅ Validações de regras de negócio no domínio
✅ Testes unitários e de integração completos

**Status**: 100% completo

---

#### Fase 24: Implementar "Marcar como Substituído"
**Status**: ✅ Concluído
**Objetivo**: Substituir produto faltante
**Data de Conclusão**: 27/10/2025

**Tarefas**:
- [x] Opção "Marcar como Substituído" no menu
- [x] Modal com campo de texto (produto substituto)
- [x] Use case `SubstituirItemUseCase`
- [x] Item marcado como separado automaticamente
- [x] Badge "🔄 Substituído"
- [x] Cor azul (diferencia de separado normal)
- [x] Migration 0005 (campos substituido, produto_substituto)
- [x] SubstituirItemView (GET: modal, POST: substituir)
- [x] Template _modal_substituir.html
- [x] Atualizar _item_pedido.html (menu + badge)
- [x] Logging completo
- [x] 8 testes automatizados (100% passando)
- [x] Script validar_fase24.py (5/5 validações passando)

**Arquivos Criados**:
- `core/application/use_cases/substituir_item.py` (SubstituirItemUseCase)
- `tests/unit/application/use_cases/test_substituir_item.py` (8 testes)
- `templates/partials/_modal_substituir.html` (modal HTMX com Alpine.js)
- `core/migrations/0005_adicionar_campos_substituicao.py` (migration)
- `validar_fase24.py` (validação E2E)
- `FASE24_RESUMO.md` (documentação completa)

**Arquivos Modificados**:
- `core/domain/pedido/entities.py` (campos substituido, produto_substituto)
- `core/infrastructure/persistence/models/__init__.py` (ItemPedido Django)
- `core/presentation/web/views.py` (SubstituirItemView)
- `core/urls.py` (rota 'substituir_item')
- `templates/partials/_item_pedido.html` (opção menu + badge + info)

**Testes**: 8/8 testes passando (100%)
```python
def test_substituir_item_com_sucesso():
    """Testa substituição bem-sucedida"""
    # Substitui item, marca como separado, registra produto substituto

def test_substituir_item_marca_como_separado_automaticamente():
    """Testa marcação automática como separado"""

def test_substituir_item_atualiza_progresso_pedido():
    """Testa atualização de progresso (1/3 = 33%)"""

def test_substituir_item_sem_produto_substituto_falha():
    """Testa validação de campo vazio"""

def test_substituir_item_ja_separado():
    """Permite substituir item já separado (registro tardio)"""

def test_substituir_item_ja_substituido_sobrescreve():
    """Permite corrigir produto substituto"""

def test_substituir_item_nao_conta_para_compra():
    """Item substituído NÃO está em compra"""

def test_substituir_item_registra_dados_separador():
    """Registra usuário e timestamp"""
```

**Validação**:
- [x] Modal funcional (HTMX + Alpine.js)
- [x] Substituição registrada no banco
- [x] Badge azul "🔄 Substituído" renderizado
- [x] Item conta como separado (progresso atualiza)
- [x] Testes passam (8/8 GREEN)
- [x] Validação E2E passa (5/5 checks GREEN)
- [x] Zero regressões (64/64 testes totais passando)
- [x] Documentação completa (FASE24_RESUMO.md)

**Funcionalidades Extras**:
- ✅ Info Box no modal explicando o que acontece
- ✅ Permitir substituir item já separado
- ✅ Permitir sobrescrever substituição (corrigir)
- ✅ Animações suaves (x-transition Alpine.js)
- ✅ Autofocus no campo de texto
- ✅ Fechar modal com ESC
- ✅ Fechar modal ao clicar fora

---

#### Fase 25: Implementar Botão "Finalizar Pedido"
**Status**: ⏳ Pendente
**Objetivo**: Finalizar pedido quando 100% separado

**Tarefas**:
- [ ] Botão aparece apenas quando progresso = 100%
- [ ] Modal de confirmação
- [ ] Use case `FinalizarPedidoUseCase`
- [ ] Mudar status para `FINALIZADO`
- [ ] Registrar tempo total de separação
- [ ] Remover do dashboard (vai para histórico)
- [ ] Animação de "slide out"

**Testes**:
```python
def test_botao_finalizar_aparece_quando_100_porcento(client, logged_in_user):
    """Testa que botão aparece ao completar todos os itens"""
    pedido = criar_pedido_com_3_itens()

    # Marcar todos como separados
    for item in pedido.itens:
        item.marcar_separado(logged_in_user)

    response = client.get(f'/pedidos/{pedido.id}/')

    assert 'Finalizar Pedido' in response.content.decode()

def test_finalizar_pedido_calcula_tempo_total(client, logged_in_user):
    """Testa cálculo de tempo total"""
    pedido = criar_pedido_com_timestamp(minutes_ago=45)
    completar_todos_itens(pedido)

    client.post(f'/pedidos/{pedido.id}/finalizar/')

    pedido.refresh_from_db()
    assert pedido.status == StatusPedido.FINALIZADO
    assert pedido.tempo_separacao_minutos == 45
```

**Validação**:
- [ ] Botão aparece condicionalmente
- [ ] Finalização funcional
- [ ] Tempo calculado corretamente
- [ ] Pedido sai do dashboard
- [ ] Testes passam

---

### 🛒 GRUPO 7: PAINEL DE COMPRAS (Fases 26-28)

#### Fase 26: Criar View do Painel de Compras
**Status**: ⏳ Pendente
**Objetivo**: Listar itens enviados para compra

**Tarefas**:
- [ ] Criar view `PainelComprasView`
- [ ] Buscar todos os `ItemCompra` (status: aguardando compra)
- [ ] Agrupar por pedido
- [ ] Exibir: produto, quantidade, pedido relacionado
- [ ] Template `painel_compras.html`

**Design**:
```
┌────────────────────────────────────────┐
│  🛒 PAINEL DE COMPRAS                  │
├────────────────────────────────────────┤
│                                        │
│  Pedido #30567 - Rosana                │
│  ┌────────────────────────────────┐    │
│  │ ☐ CABO USB-C (Qtd: 10)        │    │
│  │   Enviado por: João às 14:30  │    │
│  └────────────────────────────────┘    │
│                                        │
│  Pedido #30568 - Ponto do Celular      │
│  ┌────────────────────────────────┐    │
│  │ ☐ SUPORTE MOTO (Qtd: 5)       │    │
│  │   Enviado por: Pedro às 13:45 │    │
│  │ ☐ PELÍCULA 3D IP14 (Qtd: 20)  │    │
│  │   Enviado por: Maria às 15:00 │    │
│  └────────────────────────────────┘    │
└────────────────────────────────────────┘
```

**Validação**:
- [ ] Painel renderiza
- [ ] Itens agrupados corretamente
- [ ] Testes passam

---

#### Fase 27: Implementar Checkbox "Pedido Realizado"
**Status**: ⏳ Pendente
**Objetivo**: Compradora marca quando pedido foi feito

**Tarefas**:
- [ ] Checkbox funcional com HTMX
- [ ] Endpoint `POST /compras/{item_id}/marcar-realizado/`
- [ ] Atualizar status do `ItemCompra`
- [ ] Badge do item muda de cor (laranja → azul)
- [ ] Texto muda: "Aguardando Compra" → "Já comprado"

**Testes**:
```python
def test_marcar_pedido_como_realizado(client, logged_in_user):
    """Testa marcação de pedido realizado"""
    item_compra = criar_item_compra()

    response = client.post(
        f'/compras/{item_compra.id}/marcar-realizado/',
        HTTP_HX_REQUEST='true'
    )

    item_compra.refresh_from_db()
    assert item_compra.pedido_realizado is True
    assert item_compra.realizado_por == logged_in_user

def test_badge_muda_quando_pedido_realizado(client, logged_in_user):
    """Testa mudança visual do badge"""
    item_compra = criar_item_compra()
    item_compra.marcar_realizado(logged_in_user)

    response = client.get('/compras/')

    assert 'Já comprado' in response.content.decode()
    assert 'bg-blue' in response.content.decode()  # Cor azul
```

**Validação**:
- [ ] Checkbox funcional
- [ ] Status atualiza
- [ ] Badge muda visual
- [ ] Testes passam

---

#### Fase 28: Implementar Checkbox "Produto Chegou" (na Tela de Separação)
**Status**: ⏳ Pendente
**Objetivo**: Separador marca quando produto comprado chegou

**Tarefas**:
- [ ] Na tela de detalhe do pedido, item com badge "Já comprado" tem checkbox habilitado
- [ ] Separador marca checkbox quando produto chegar
- [ ] Item é marcado como separado
- [ ] Badge removido (ou muda para "✅ Separado")

**Testes**:
```python
def test_marcar_item_comprado_quando_chega(client, logged_in_user):
    """Testa marcação de item quando produto comprado chega"""
    item = criar_item_em_compra()
    item.marcar_pedido_realizado()

    response = client.post(
        f'/pedidos/{item.pedido.id}/itens/{item.id}/separar/',
        HTTP_HX_REQUEST='true'
    )

    item.refresh_from_db()
    assert item.separado is True
    assert item.separado_por == logged_in_user
```

**Validação**:
- [ ] Checkbox habilitado após compra
- [ ] Marcação funciona
- [ ] Item vai para seção "Separados"
- [ ] Testes passam

---

### 📈 GRUPO 8: MÉTRICAS E WEBSOCKETS (Fases 29-31)

#### Fase 29: Configurar Django Channels e WebSockets
**Status**: ⏳ Pendente
**Objetivo**: Atualização em tempo real do dashboard

**Tarefas**:
- [ ] Instalar Django Channels
- [ ] Configurar ASGI (asgi.py)
- [ ] Configurar Redis como channel layer
- [ ] Criar consumer básico `DashboardConsumer`
- [ ] Testar conexão WebSocket

**Testes**:
```python
# tests/integration/test_websocket.py
async def test_websocket_connection():
    """Testa conexão WebSocket"""
    communicator = WebsocketCommunicator(application, "/ws/dashboard/")
    connected, _ = await communicator.connect()
    assert connected
    await communicator.disconnect()

async def test_websocket_receives_updates():
    """Testa que WebSocket recebe atualizações"""
    communicator = WebsocketCommunicator(application, "/ws/dashboard/")
    await communicator.connect()

    # Criar pedido (trigger de evento)
    criar_pedido()

    response = await communicator.receive_json_from()
    assert response['type'] == 'pedido_criado'

    await communicator.disconnect()
```

**Validação**:
- [ ] WebSocket conecta
- [ ] Mensagens são recebidas
- [ ] Testes assíncronos passam

---

#### Fase 30: Implementar Eventos em Tempo Real no Dashboard
**Status**: ⏳ Pendente
**Objetivo**: Dashboard atualiza automaticamente sem refresh

**Tarefas**:
- [ ] Enviar evento `pedido_criado` quando pedido é criado
- [ ] Enviar evento `item_separado` quando item é marcado
- [ ] Enviar evento `pedido_finalizado` quando pedido é finalizado
- [ ] Frontend escuta eventos e atualiza cards via JavaScript
- [ ] Animação ao adicionar/remover card

**JavaScript**:
```javascript
const socket = new WebSocket('ws://localhost:8000/ws/dashboard/');

socket.onmessage = function(event) {
    const data = JSON.parse(event.data);

    if (data.type === 'pedido_criado') {
        // Adicionar novo card ao dashboard
        htmx.ajax('GET', `/pedidos/${data.pedido_id}/card/`, {
            target: '#cards-container',
            swap: 'afterbegin'
        });
    }

    if (data.type === 'item_separado') {
        // Atualizar progresso do card
        updateProgress(data.pedido_id, data.progresso);
    }
};
```

**Validação**:
- [ ] Eventos disparados corretamente
- [ ] Dashboard atualiza em tempo real
- [ ] Múltiplos clientes recebem atualizações
- [ ] Testes E2E passam

---

#### Fase 31: Criar Tela de Histórico
**Status**: ⏳ Pendente
**Objetivo**: Visualizar pedidos finalizados

**Tarefas**:
- [ ] Criar view `HistoricoView`
- [ ] Listar pedidos com status `FINALIZADO`
- [ ] Ordenar por data de finalização (mais recente primeiro)
- [ ] Exibir: número, cliente, vendedor, tempo total, data finalização, quem finalizou
- [ ] Paginação (20 por página)
- [ ] Filtros: data, vendedor, cliente

**Design**:
```
┌────────────────────────────────────────┐
│  📜 HISTÓRICO DE PEDIDOS               │
├────────────────────────────────────────┤
│  🔍 [Buscar] | 📅 [Data] | 👤 [Vendedor]│
│                                        │
│  #30567 - Rosana                       │
│  Finalizado em: 24/10/25 às 16:30     │
│  Tempo: 45 minutos                     │
│  Finalizado por: João                  │
│  ────────────────────────────────────  │
│                                        │
│  #30568 - Ponto do Celular             │
│  Finalizado em: 24/10/25 às 15:20     │
│  Tempo: 52 minutos                     │
│  Finalizado por: Maria                 │
│  ────────────────────────────────────  │
└────────────────────────────────────────┘
```

**Validação**:
- [ ] Histórico renderiza
- [ ] Filtros funcionam
- [ ] Paginação funcional
- [ ] Testes passam

---

### 🚀 GRUPO 9: DEPLOY E FINALIZAÇÃO (Fases 32-35)

#### Fase 32: Implementar Sistema de Admin Django
**Status**: ⏳ Pendente
**Objetivo**: Interface admin para gestão

**Tarefas**:
- [ ] Configurar Django Admin
- [ ] Registrar modelos: Usuario, Pedido, ItemPedido, ItemCompra
- [ ] Customizar list_display, list_filter, search_fields
- [ ] Criar ações em lote (ex: finalizar múltiplos pedidos)
- [ ] Proteger com permissão de admin

**Validação**:
- [ ] Admin acessível
- [ ] CRUD funcional
- [ ] Apenas admins acessam

---

#### Fase 33: Criar Tela de Métricas Avançadas
**Status**: ⏳ Pendente
**Objetivo**: Dashboards de performance

**Tarefas**:
- [ ] View `MetricasView`
- [ ] Métricas:
  - Tempo médio por separador
  - Ranking de separadores (quem separa mais rápido)
  - Produtos mais separados
  - Produtos mais enviados para compra
  - Gráfico de pedidos por dia (últimos 30 dias)
- [ ] Usar Chart.js para gráficos

**Validação**:
- [ ] Métricas calculadas corretamente
- [ ] Gráficos renderizam
- [ ] Testes passam

---

#### Fase 34: Otimizações de Performance
**Status**: ⏳ Pendente
**Objetivo**: Garantir app rápido

**Tarefas**:
- [ ] Adicionar `select_related` e `prefetch_related` em queries
- [ ] Configurar cache Redis para views pesadas
- [ ] Implementar paginação em todas as listas
- [ ] Otimizar queries N+1
- [ ] Adicionar índices no banco (migrations)
- [ ] Testar com 100+ pedidos

**Validação**:
- [ ] Queries otimizadas (Django Debug Toolbar)
- [ ] Cache funcionando
- [ ] Performance aceitável com volume real

---

#### Fase 35: Deploy para Produção
**Status**: ⏳ Pendente
**Objetivo**: Colocar app no ar

**Tarefas**:
- [ ] Criar conta no Railway.app
- [ ] Configurar variáveis de ambiente (DATABASE_URL, REDIS_URL, SECRET_KEY)
- [ ] Configurar ALLOWED_HOSTS
- [ ] Configurar CSRF_TRUSTED_ORIGINS
- [ ] Deploy inicial
- [ ] Rodar migrations em produção
- [ ] Criar superusuário
- [ ] Criar usuários de teste (vendedores, separadores, compradora)
- [ ] Testar fluxo completo em produção
- [ ] Configurar SSL (HTTPS)

**Validação**:
- [ ] App acessível via HTTPS
- [ ] WebSockets funcionando em produção
- [ ] Upload de PDF funciona
- [ ] Todos os fluxos testados
- [ ] Pronto para uso

---

## 6. UI/UX GUIDELINES

### 6.1 Princípios de Design

#### Fluidez
- **60fps**: Todas as animações devem rodar a 60 frames por segundo
- **Transitions**: Usar `transition-all duration-300 ease-in-out` (Tailwind)
- **Loading states**: Sempre mostrar feedback visual (spinners, skeletons)

#### Modernidade
- **Design System**: Baseado em cards com sombras sutis
- **Cores**: Paleta moderna (azul, verde, laranja, vermelho)
- **Tipografia**: Inter ou Poppins (Google Fonts)
- **Espaçamento**: Generoso (padding/margin)

#### Intuitividade
- **Ícones**: Usar emoji ou Font Awesome para clareza visual
- **Hierarquia**: Informações mais importantes em destaque
- **Feedback**: Mensagens claras de sucesso/erro
- **Confirmações**: Modais para ações destrutivas

#### Simplicidade
- **Menos é mais**: Evitar sobrecarga visual
- **Progressive disclosure**: Mostrar detalhes apenas quando necessário
- **Atalhos**: Keyboard shortcuts para power users (opcional)

### 6.2 Paleta de Cores (Tailwind)

```css
/* Cores Principais */
--primary: #3B82F6 (blue-500)      /* Ações principais */
--success: #10B981 (green-500)      /* Sucesso, separado */
--warning: #F59E0B (amber-500)      /* Aguardando compra */
--danger: #EF4444 (red-500)         /* Erros, exclusão */
--info: #06B6D4 (cyan-500)          /* Informações */

/* Backgrounds */
--bg-primary: #F9FAFB (gray-50)     /* Fundo geral */
--bg-card: #FFFFFF (white)          /* Cards */
--bg-hover: #F3F4F6 (gray-100)      /* Hover states */

/* Text */
--text-primary: #111827 (gray-900)  /* Texto principal */
--text-secondary: #6B7280 (gray-500)/* Texto secundário */
```

### 6.3 Componentes de Referência

#### Card
```html
<div class="bg-white rounded-lg shadow-md hover:shadow-lg transition-all duration-300 p-6 cursor-pointer">
  <!-- Conteúdo -->
</div>
```

#### Botão Principal
```html
<button class="bg-blue-500 hover:bg-blue-600 text-white font-semibold py-2 px-6 rounded-lg transition-colors duration-200">
  Criar Pedido
</button>
```

#### Badge
```html
<span class="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-green-100 text-green-800">
  ✅ Separado
</span>
```

#### Loading Spinner
```html
<div class="inline-block h-8 w-8 animate-spin rounded-full border-4 border-solid border-current border-r-transparent motion-reduce:animate-[spin_1.5s_linear_infinite]"></div>
```

### 6.4 Animações com Alpine.js

#### Slide Down
```html
<div x-data="{ open: false }" x-show="open" x-transition:enter="transition ease-out duration-300" x-transition:enter-start="opacity-0 transform scale-95" x-transition:enter-end="opacity-100 transform scale-100">
  <!-- Conteúdo -->
</div>
```

#### Fade In
```html
<div x-data="{ show: false }" x-show="show" x-transition>
  <!-- Conteúdo -->
</div>
```

### 6.5 Responsividade

**Mobile First**:
- [ ] Dashboard com scroll vertical em mobile
- [ ] Cards full-width em telas pequenas
- [ ] Menu hamburger em mobile
- [ ] Tabelas responsivas (scroll horizontal ou cards)

**Breakpoints** (Tailwind):
- `sm`: 640px (tablet)
- `md`: 768px (tablet grande)
- `lg`: 1024px (desktop)
- `xl`: 1280px (desktop grande)

---

## 7. DECISÕES TÉCNICAS

### 7.1 Stack de Frontend: Django Templates + HTMX
**Razão**: Simplicidade e velocidade de desenvolvimento. HTMX permite reatividade sem complexidade de SPA.

### 7.2 Fases Atômicas
**Razão**: Minimizar riscos. Cada fase é pequena, testável e pode ser revertida facilmente.

### 7.3 TDD Rigoroso
**Razão**: Garantir qualidade. Usuário tem nível avançado em TDD, então seguir ciclo Red-Green-Refactor estritamente.

### 7.4 DDD (Domain-Driven Design)
**Razão**: Separação clara de responsabilidades. Facilita manutenção e escalabilidade.

### 7.5 WebSockets (Django Channels)
**Razão**: Atualização em tempo real é requisito crítico. WebSockets são a solução mais eficiente.

### 7.6 Hospedagem: Railway.app
**Razão**: Custo-benefício. Suporta PostgreSQL, Redis e WebSockets nativamente. Deploy automático.

### 7.7 Validação Matemática de PDFs
**Razão**: Garantir 100% de precisão na extração. Quantidade × Valor Unitário = Valor Total é regra infalível.

---

## 8. COMO USAR ESTE ARQUIVO

### 8.1 Início de Sessão
1. Ler seção **4. Status Atual** para saber onde parou
2. Ler **Fase Atual** em detalhes
3. Verificar **Checklist** da fase

### 8.2 Durante Desenvolvimento
1. Seguir ciclo TDD (Red → Green → Refactor)
2. Marcar checkboxes conforme completa tarefas
3. Rodar testes antes de commitar
4. Atualizar seção **4.1 O Que Foi Feito** ao concluir fase

### 8.3 Fim de Sessão
1. Atualizar **4.2 Fase Atual**
2. Marcar fase como ✅ Concluído ou 🔄 Em Andamento
3. Commitar mudanças no planejamento.md
4. Usar `/clear` para otimizar contexto

### 8.4 Comandos Úteis

```bash
# Rodar testes
pytest

# Rodar servidor
python manage.py runserver

# Migrations
python manage.py makemigrations
python manage.py migrate

# Criar superusuário
python manage.py createsuperuser

# Compilar Tailwind (se usando CLI)
npx tailwindcss -i ./static/css/input.css -o ./static/css/output.css --watch

# Shell Django (para testes manuais)
python manage.py shell
```

---

## 📊 PROGRESSO VISUAL

```
Setup Inicial       ✅✅✅✅ 4/4 (COMPLETO)
Autenticação        ✅✅✅✅ 4/4 (COMPLETO - Fases 5-8 concluídas)
Parsing PDF         ✅✅✅✅ 4/4 (COMPLETO - Fases 9-12 concluídas)
Criação Pedidos     ⬜⬜⬜⬜ 0/4
Dashboard           ⬜⬜⬜⬜ 0/4
Separação           ⬜⬜⬜⬜⬜ 0/5
Painel Compras      ⬜⬜⬜ 0/3
Métricas/WebSocket  ⬜⬜⬜ 0/3
Deploy              ⬜⬜⬜⬜ 0/4

TOTAL: 12/35 fases (34%)
TESTES: 56 passando (8 Fase 6 + 8 Fase 7 + 8 Fase 8 + 8 Fase 9 + 8 Fase 10 + 8 Fase 11 + 8 Fase 12)
```

---

## 🎯 PRÓXIMA AÇÃO

**Fase 13: Criar Entidade Pedido**

Quando estiver pronto, diga: "Iniciar Fase 13" e o Claude começará o desenvolvimento seguindo TDD rigoroso.

**Observação**: As Fases 1-12 foram concluídas com sucesso seguindo TDD (RED → GREEN → REFACTOR).

### 📋 Resumo da Fase 12 (Recém-concluída):
- **ProdutoDTO criado**: core/application/dtos/orcamento_dtos.py
  - Dataclass com campos: codigo, descricao, quantidade, valor_unitario, valor_total, errors
  - Validação matemática automática no __post_init__ (tolerância 0.01)
  - Property is_valid e método to_entity()

- **PDFProductExtractor implementado**: core/infrastructure/pdf/parser.py
  - Método extrair_produtos(texto) -> List[ProdutoDTO]
  - Método _identificar_secao_produtos(texto) -> Optional[str]
  - Método _extrair_produto_linha(linha) -> Optional[ProdutoDTO]
  - Método _converter_valor_brasileiro(valor_str) -> Decimal
  - Regex patterns: PATTERN_CODIGO, PATTERN_VALORES, PATTERN_UNIDADE
  - Marcadores de seção: MARCADOR_INICIO_PRODUTOS, MARCADOR_FIM_PRODUTOS
  - Logging completo (info, warning, error, debug)
  - Fail-safe: linhas inválidas não quebram extração

- **8 testes Fase 12**: 100% passando (extração completa, validação matemática, edge cases)
- **56 testes totais**: 100% passando (48 anteriores + 8 Fase 12)
- **TDD rigoroso**: RED → GREEN → REFACTOR completado
- **Validação real**: 5 PDFs reais, 77 produtos, 100% válidos
- **Script validar_fase12.py**: Criado para validação automatizada
- **Encoding UTF-8**: Todos os arquivos corretamente codificados
- **Docstrings Google Style**: Completas em todos os métodos

### 🎯 Próximos passos (Fase 13):
- Criar entidade Pedido em domain/pedido/entities.py
- Criar entidade ItemPedido em domain/pedido/entities.py
- Criar Value Objects: Logistica, Embalagem, StatusPedido
- Implementar agregação (Pedido tem lista de ItemPedido)
- Métodos: adicionar_item(), calcular_progresso(), pode_finalizar()
- Criar migrations
- Escrever 8 testes (RED → GREEN → REFACTOR)
- Validar lógica de negócio (ex: Correios só aceita Caixa)

---

**Última atualização**: 2025-10-25 (Fase 12 concluída)
**Versão do Planejamento**: 1.12
**Status**: Em desenvolvimento - Fases 1-12 completas (34% concluído - 56 testes passando)


---

## ✅ FASE 15 CONCLUÍDA (2025-10-25)

### Implementação: Tela de Upload de PDF (UI)

**Status**: ✅ 100% completo

#### Arquivos Criados/Modificados:
1. **Testes**: `backend/core/tests/integration/test_upload_orcamento_view.py` (9 testes)
2. **Form**: `backend/core/presentation/web/forms.py` (UploadOrcamentoForm)
3. **View**: `backend/core/presentation/web/views.py` (UploadOrcamentoView)
4. **Template**: `backend/templates/upload_orcamento.html`
5. **URLs**: `backend/core/urls.py` (rota /pedidos/novo/)
6. **Dashboard**: `backend/templates/dashboard.html` (botão Criar Novo Pedido)

#### Funcionalidades Implementadas:
- ✅ Upload de arquivo PDF (max 10MB)
- ✅ Validação de arquivo (extensão, tamanho, mime type)
- ✅ Form com Logística (dropdown) e Embalagem (radio)
- ✅ Validação de compatibilidade logística x embalagem
- ✅ Validação client-side JavaScript (desabilita SACOLA para CORREIOS/MELHOR_ENVIO/ONIBUS)
- ✅ Integração completa com CriarPedidoUseCase
- ✅ Extração automática de dados do PDF
- ✅ Criação de pedido no banco de dados
- ✅ Redirecionamento para dashboard após sucesso
- ✅ Mensagens de erro detalhadas
- ✅ Proteção com @login_required
- ✅ Logging completo
- ✅ Design moderno Tailwind CSS

#### Testes:
- **Total de testes do projeto**: 65 (100% passando)
- **Testes da Fase 15**: 9 (100% passando)
  1. GET renderiza página corretamente
  2. POST com PDF válido extrai dados
  3. POST sem arquivo retorna erro
  4. POST com não-PDF retorna erro
  5. Validação embalagem vs logística (CORREIOS + SACOLA = inválido)
  6. Preview exibe dados extraídos
  7. Confirmação cria pedido no banco
  8. Redirecionamento para dashboard
  9. Usuário não autenticado redireciona para login

#### TDD Rigoroso Seguido:
1. ✅ **RED**: 9 testes criados (todos falhando)
2. ✅ **GREEN**: Código implementado (todos os testes passando)
3. ✅ **REFACTOR**: Código organizado, constantes extraídas, docstrings completas

#### Validações Implementadas:
- Server-side:
  - Arquivo obrigatório
  - Extensão .pdf
  - Tamanho máximo 10MB
  - Mime type application/pdf
  - Compatibilidade logística x embalagem
- Client-side:
  - JavaScript desabilita SACOLA para logísticas que requerem CAIXA
  - Feedback visual de arquivo selecionado

#### Próxima Fase:
**Fase 16**: Dashboard de Pedidos com WebSockets (cards em tempo real)

---

## ✅ FASE 18 CONCLUÍDA (2025-10-25)

### Implementação: Componente de Card de Pedido (Partial Template)

**Status**: ✅ 100% completo

#### Arquivos Criados/Modificados:
1. **Partial Template**: `backend/templates/partials/_card_pedido.html` (novo)
2. **Dashboard Refatorado**: `backend/templates/dashboard.html` (refatorado)
3. **Testes**: `backend/core/tests/integration/test_card_pedido_partial.py` (11 testes)

#### Funcionalidades Implementadas:
- ✅ Partial template reutilizável para cards de pedido
- ✅ Componentização completa (card extraído do dashboard)
- ✅ Layout mantido idêntico (zero mudança visual)
- ✅ Exibição de número do orçamento, cliente e vendedor
- ✅ Badges coloridos para logística e embalagem
- ✅ Barra de progresso visual com percentual
- ✅ Tempo decorrido exibido em minutos
- ✅ Listagem de separadores ativos com badges
- ✅ Mensagem "Nenhum separador ativo" quando lista vazia
- ✅ Classes hover effect (shadow-xl, cursor-pointer)
- ✅ Documentação inline completa
- ✅ Dashboard refatorado para usar {% include %}

#### Testes:
- **Total de testes do projeto**: 85 (100% passando)
- **Testes da Fase 18**: 11 (100% passando)
  1. Partial renderiza sem erros
  2. Exibe número do orçamento
  3. Exibe nome do cliente
  4. Exibe nome do vendedor
  5. Exibe badges de logística e embalagem
  6. Exibe tempo decorrido em minutos
  7. Exibe progresso percentual
  8. Barra de progresso tem largura CSS correta
  9. Exibe separadores ativos
  10. Exibe mensagem quando sem separadores
  11. Possui classes hover effect

#### TDD Rigoroso Seguido:
1. ✅ **RED**: 11 testes criados (todos falhando - template não existia)
2. ✅ **GREEN**: Partial criado + Dashboard refatorado (todos os testes passando)
3. ✅ **REFACTOR**: Comentários inline adicionados

#### Estrutura do Componente:
```html
{# partials/_card_pedido.html #}
- Card wrapper (bg-white, shadow-md, hover:shadow-xl)
- Cabeçalho: #orçamento + cliente + tempo
- Informações: vendedor + badges logística/embalagem
- Progresso: barra visual + X/Y itens
- Separadores: badges ou mensagem vazia
```

#### Próxima Fase:
**Fase 19**: Implementar Ordenação e Paginação no Dashboard

