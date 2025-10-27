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

### 4.2 Fase Atual
**NENHUMA FASE EM ANDAMENTO**

Aguardando início da Fase 1.

### 4.3 Progresso Geral
```
Progresso: 0/35 fases concluídas (0%)
```

---

## 5. FASES DE DESENVOLVIMENTO

### 🎯 GRUPO 1: SETUP INICIAL (Fases 1-4)

#### Fase 1: Setup do Projeto Django
**Status**: ⏳ Pendente
**Objetivo**: Criar projeto Django com estrutura DDD

**Tarefas**:
- [ ] Criar projeto Django `separacao_pmcell`
- [ ] Criar app principal `core`
- [ ] Configurar estrutura de pastas DDD (domain, application, infrastructure, presentation)
- [ ] Criar requirements.txt com dependências base
- [ ] Configurar .gitignore
- [ ] Criar README.md básico

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
- [ ] Estrutura de pastas criada
- [ ] Servidor Django roda sem erros
- [ ] Testes passam

---

#### Fase 2: Configuração do PostgreSQL e Redis
**Status**: ⏳ Pendente
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
**Status**: ⏳ Pendente
**Objetivo**: Configurar Tailwind CSS para styling moderno

**Tarefas**:
- [ ] Instalar Tailwind via npm/standalone CLI
- [ ] Configurar tailwind.config.js
- [ ] Criar base.html com imports do Tailwind
- [ ] Configurar collectstatic para produção
- [ ] Criar arquivo de variáveis CSS customizadas (cores PMCELL)

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
- [ ] Tailwind compilando corretamente
- [ ] Estilos aplicados em template de teste
- [ ] Testes passam

---

#### Fase 4: Setup do HTMX e Alpine.js
**Status**: ⏳ Pendente
**Objetivo**: Configurar HTMX para interatividade e Alpine.js para micro-interações

**Tarefas**:
- [ ] Adicionar HTMX via CDN ou npm
- [ ] Adicionar Alpine.js via CDN
- [ ] Criar página de teste com exemplo HTMX (load partial)
- [ ] Criar exemplo Alpine.js (dropdown, toggle)
- [ ] Documentar padrões de uso

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
- [ ] HTMX funcionando (exemplo de load partial)
- [ ] Alpine.js funcionando (exemplo de toggle)
- [ ] Testes passam

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
**Status**: ⏳ Pendente
**Objetivo**: Criar use case de autenticação

**Tarefas**:
- [ ] Criar `LoginUseCase` em `application/use_cases/login.py`
- [ ] Implementar lógica de validação (número + PIN)
- [ ] Implementar rate limiting (5 tentativas/minuto)
- [ ] Criar DTO de resposta (LoginResponseDTO)

**Testes**:
```python
# tests/unit/application/test_login_use_case.py
def test_login_success_with_valid_credentials():
    """Testa login com credenciais válidas"""
    use_case = LoginUseCase(usuario_repo)
    result = use_case.execute(numero_login=1, pin='1234')
    assert result.success is True
    assert result.usuario.numero_login == 1

def test_login_fails_with_invalid_pin():
    """Testa que login falha com PIN inválido"""
    use_case = LoginUseCase(usuario_repo)
    result = use_case.execute(numero_login=1, pin='9999')
    assert result.success is False

def test_login_rate_limiting():
    """Testa rate limiting (máx 5 tentativas/min)"""
    use_case = LoginUseCase(usuario_repo)
    for _ in range(5):
        use_case.execute(numero_login=1, pin='9999')

    result = use_case.execute(numero_login=1, pin='1234')
    assert result.blocked is True
```

**Validação**:
- [ ] Use case implementado
- [ ] Rate limiting funcionando
- [ ] Testes passam

---

#### Fase 7: Criar Tela de Login (UI)
**Status**: ⏳ Pendente
**Objetivo**: Criar interface de login moderna e fluida

**Tarefas**:
- [ ] Criar view `LoginView` em `presentation/web/views.py`
- [ ] Criar form `LoginForm` em `presentation/web/forms.py`
- [ ] Criar template `login.html` com Tailwind
- [ ] Adicionar validação client-side (input numérico, PIN 4 dígitos)
- [ ] Adicionar animações de erro/sucesso

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

**Validação**:
- [ ] Tela de login renderizando
- [ ] Login funcional
- [ ] Validações client-side funcionando
- [ ] Animações fluidas
- [ ] Testes passam

---

#### Fase 8: Implementar Sessão e Middleware de Autenticação
**Status**: ⏳ Pendente
**Objetivo**: Proteger rotas e gerenciar sessões

**Tarefas**:
- [ ] Configurar sessões Django (timeout 8h)
- [ ] Criar middleware customizado `AuthenticationMiddleware`
- [ ] Decorator `@login_required` customizado
- [ ] Implementar logout
- [ ] Criar view de logout

**Testes**:
```python
# tests/integration/test_authentication.py
def test_unauthenticated_user_redirected_to_login(client):
    """Testa que usuário não autenticado é redirecionado"""
    response = client.get('/dashboard/')
    assert response.status_code == 302
    assert '/login/' in response.url

def test_authenticated_user_can_access_dashboard(client, logged_in_user):
    """Testa que usuário autenticado acessa dashboard"""
    response = client.get('/dashboard/')
    assert response.status_code == 200

def test_session_expires_after_8_hours(client, logged_in_user):
    """Testa que sessão expira após 8h"""
    # Simular passagem de 8h
    session = client.session
    session['last_activity'] = timezone.now() - timedelta(hours=9)
    session.save()

    response = client.get('/dashboard/')
    assert response.status_code == 302
```

**Validação**:
- [ ] Sessões funcionando
- [ ] Middleware protegendo rotas
- [ ] Timeout de 8h funcionando
- [ ] Logout funcional
- [ ] Testes passam

---

### 📄 GRUPO 3: PARSING DE PDF (Fases 9-12)

#### Fase 9: Criar Entidade Produto
**Status**: ⏳ Pendente
**Objetivo**: Modelar domínio de Produto

**Tarefas**:
- [ ] Criar `Produto` em `domain/produto/entities.py`
- [ ] Campos: `codigo` (CharField, 5 dígitos), `descricao`, `quantidade`, `valor_unitario`, `valor_total`
- [ ] Método de validação matemática: `quantidade * valor_unitario == valor_total`
- [ ] Criar migration

**Testes**:
```python
# tests/unit/domain/test_produto.py
def test_produto_mathematical_validation():
    """Testa validação matemática do produto"""
    produto = Produto(
        codigo='00010',
        descricao='CABO USB',
        quantidade=10,
        valor_unitario=Decimal('1.40'),
        valor_total=Decimal('14.00')
    )
    assert produto.validar_calculo() is True

def test_produto_validation_fails_with_wrong_total():
    """Testa que validação falha com total incorreto"""
    produto = Produto(
        codigo='00010',
        descricao='CABO USB',
        quantidade=10,
        valor_unitario=Decimal('1.40'),
        valor_total=Decimal('15.00')  # Errado
    )
    with pytest.raises(ValidationError):
        produto.validar_calculo()
```

**Validação**:
- [ ] Entidade criada
- [ ] Validação matemática funcionando
- [ ] Testes passam

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
**Status**: ⏳ Pendente
**Objetivo**: Extrair dados do cabeçalho (número, cliente, vendedor, data)

**Tarefas**:
- [ ] Criar `PDFHeaderExtractor` em `infrastructure/pdf/parser.py`
- [ ] Regex para extrair: número orçamento, código cliente, nome cliente, vendedor, data
- [ ] Retornar DTO: `OrcamentoHeaderDTO`
- [ ] Validar todos os campos obrigatórios

**Testes**:
```python
# tests/unit/infrastructure/test_pdf_header_extraction.py
def test_extract_orcamento_numero():
    """Testa extração do número do orçamento"""
    extractor = PDFHeaderExtractor()
    texto = "Orçamento Nº: 30567"
    header = extractor.extrair_header(texto)
    assert header.numero_orcamento == '30567'

def test_extract_all_header_fields():
    """Testa extração de todos os campos do cabeçalho"""
    extractor = PDFHeaderExtractor()
    texto = get_sample_pdf_text()
    header = extractor.extrair_header(texto)

    assert header.numero_orcamento == '30567'
    assert header.codigo_cliente == '001007'
    assert 'ROSANA' in header.nome_cliente
    assert header.vendedor == 'NYCOLAS HENDRIGO MANCINI'
    assert header.data is not None
```

**Validação**:
- [ ] Todos os campos extraídos corretamente
- [ ] Testes com múltiplos PDFs passam
- [ ] Validação de campos obrigatórios funciona

---

#### Fase 12: Implementar Extração de Produtos do PDF
**Status**: ⏳ Pendente
**Objetivo**: Extrair lista de produtos com validação matemática

**Tarefas**:
- [ ] Criar `PDFProductExtractor` em `infrastructure/pdf/parser.py`
- [ ] Regex para extrair código produto (5 dígitos iniciais)
- [ ] Regex para extrair 3 últimos números (quantidade, valor unit, valor total)
- [ ] Validar matematicamente: `qtd * valor_unit == valor_total`
- [ ] Extrair descrição (texto entre código e "UN")
- [ ] Retornar lista de `ProdutoDTO`

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

**Validação**:
- [ ] Produtos extraídos corretamente
- [ ] Validação matemática 100% precisa
- [ ] Testes com todos os PDFs de exemplo passam
- [ ] Edge cases tratados (descrições longas, caracteres especiais)

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
**Status**: ⏳ Pendente
**Objetivo**: Implementar lógica de criação de pedido a partir do PDF

**Tarefas**:
- [ ] Criar `CriarPedidoUseCase` em `application/use_cases/criar_pedido.py`
- [ ] Integrar PDFParser + Extratores
- [ ] Validar dados extraídos
- [ ] Criar entidade Pedido + ItemPedido
- [ ] Persistir no banco via repositório
- [ ] Iniciar cronômetro do pedido

**Testes**:
```python
# tests/unit/application/test_criar_pedido_use_case.py
def test_criar_pedido_from_valid_pdf():
    """Testa criação de pedido a partir de PDF válido"""
    use_case = CriarPedidoUseCase(pedido_repo, pdf_parser)

    result = use_case.execute(
        pdf_path='tests/fixtures/orcamento_30567.pdf',
        logistica='CORREIOS',
        embalagem='CAIXA',
        usuario_criador=vendedor
    )

    assert result.success is True
    assert result.pedido.numero_orcamento == '30567'
    assert len(result.pedido.itens) == 1

def test_criar_pedido_validates_mathematical_consistency():
    """Testa que use case valida consistência matemática"""
    use_case = CriarPedidoUseCase(pedido_repo, pdf_parser)

    # PDF com erro matemático (mockado)
    result = use_case.execute(pdf_path='invalid_math.pdf', ...)

    assert result.success is False
    assert 'validação matemática' in result.error_message

def test_criar_pedido_inicia_cronometro():
    """Testa que pedido inicia com cronômetro"""
    use_case = CriarPedidoUseCase(pedido_repo, pdf_parser)
    result = use_case.execute(...)

    assert result.pedido.data_inicio is not None
    assert result.pedido.tempo_decorrido_segundos >= 0
```

**Validação**:
- [ ] Use case funcional
- [ ] Integração com parser de PDF funciona
- [ ] Validações de negócio aplicadas
- [ ] Testes passam

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
**Status**: ⏳ Pendente
**Objetivo**: UI fluida com loading states e transições

**Tarefas**:
- [ ] Loading spinner durante parsing do PDF
- [ ] Animação de "slide down" para preview aparecer
- [ ] Validação em tempo real (embalagem habilitada/desabilitada)
- [ ] Mensagens de erro inline com ícones
- [ ] Sucesso com confete ou animação celebratória (opcional)
- [ ] Progress bar durante upload (se arquivo grande)

**Validação**:
- [ ] Animações fluidas (60fps)
- [ ] Feedback visual claro em todos os estados
- [ ] UX intuitiva (testado com usuário)

---

### 📊 GRUPO 5: DASHBOARD (Fases 17-20)

#### Fase 17: Criar View do Dashboard
**Status**: ⏳ Pendente
**Objetivo**: Listar cards de pedidos em separação

**Tarefas**:
- [ ] Criar `DashboardView` em `presentation/web/views.py`
- [ ] Buscar pedidos com status `EM_SEPARACAO`
- [ ] Calcular tempo decorrido para cada pedido
- [ ] Calcular progresso (X/Y itens)
- [ ] Identificar quem está separando (últimos usuários que marcaram itens)
- [ ] Criar template `dashboard.html`

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
- [ ] Dashboard renderiza corretamente
- [ ] Cálculos de tempo e progresso corretos
- [ ] Testes passam

---

#### Fase 18: Criar Componente de Card de Pedido
**Status**: ⏳ Pendente
**Objetivo**: Card visual moderno e informativo

**Tarefas**:
- [ ] Criar partial template `_card_pedido.html`
- [ ] Layout com Tailwind (sombra, hover effect, gradiente sutil)
- [ ] Exibir: número, cliente, vendedor, logística, embalagem, progresso, tempo, separadores
- [ ] Barra de progresso visual (colorida)
- [ ] Cronômetro atualizado (JavaScript)
- [ ] Click no card abre modal de autenticação

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
- [ ] Card renderiza bonito
- [ ] Hover effect funciona
- [ ] Informações corretas exibidas

---

#### Fase 19: Implementar Ordenação e Paginação no Dashboard
**Status**: ⏳ Pendente
**Objetivo**: Otimizar visualização de muitos pedidos

**Tarefas**:
- [ ] Ordenar por tempo decorrido (mais antigos primeiro)
- [ ] Paginação (10 cards por página)
- [ ] Navegação com HTMX (sem reload)
- [ ] Campo de busca (número de orçamento ou cliente)
- [ ] Filtro por vendedor

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
- [ ] Ordenação correta
- [ ] Paginação funcional
- [ ] Busca funciona
- [ ] Testes passam

---

#### Fase 20: Implementar Métrica de Tempo Médio no Dashboard
**Status**: ⏳ Pendente
**Objetivo**: Exibir tempo médio de separação (hoje e últimos 7 dias)

**Tarefas**:
- [ ] Criar query para calcular tempo médio de separação (pedidos finalizados)
- [ ] Filtro: hoje vs últimos 7 dias
- [ ] Exibir no topo do dashboard (card destacado)
- [ ] Adicionar ícone de tendência (↑↓) se melhorou/piorou

**Design**:
```
┌────────────────────────────────────────┐
│  ⏱️ TEMPO MÉDIO DE SEPARAÇÃO           │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ │
│         45 minutos  (Hoje)             │
│    52 min (Últimos 7 dias) ↓ -13%     │
└────────────────────────────────────────┘
```

**Validação**:
- [ ] Cálculo correto
- [ ] Exibição funcional
- [ ] Testes passam

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
**Status**: ⏳ Pendente
**Objetivo**: Checkbox funcional com animação

**Tarefas**:
- [ ] Criar endpoint HTMX `POST /pedidos/{id}/itens/{item_id}/separar/`
- [ ] Use case `SepararItemUseCase`
- [ ] Atualizar status do item
- [ ] Registrar usuário + timestamp
- [ ] Retornar partial atualizado (item vai para seção "Separados")
- [ ] Atualizar progresso do pedido
- [ ] Animação de "slide down"

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
- [ ] Checkbox funcional
- [ ] Item move para seção correta
- [ ] Progresso atualiza
- [ ] Animação fluida
- [ ] Testes passam

---

#### Fase 23: Implementar "Marcar para Compra"
**Status**: ⏳ Pendente
**Objetivo**: Enviar item para painel de compras

**Tarefas**:
- [ ] Menu de opções no item (3 pontinhos)
- [ ] Opção "Marcar para Compra"
- [ ] Criar `ItemCompra` em `domain/compra/entities.py`
- [ ] Use case `EnviarParaCompraUseCase`
- [ ] Item vai para seção "Separados" com badge "📦 Aguardando Compra"
- [ ] Cor laranja diferenciada

**Testes**:
```python
def test_marcar_item_para_compra(client, logged_in_user):
    """Testa envio de item para compra"""
    pedido = criar_pedido_com_itens()
    item = pedido.itens[0]

    response = client.post(
        f'/pedidos/{pedido.id}/itens/{item.id}/marcar-compra/',
        HTTP_HX_REQUEST='true'
    )

    item.refresh_from_db()
    assert item.em_compra is True
    assert item.enviado_para_compra_por == logged_in_user

def test_item_em_compra_aparece_no_painel_compras(client):
    """Testa que item aparece no painel de compras"""
    marcar_item_para_compra(item)

    response = client.get('/compras/')

    assert item.produto.descricao in response.content.decode()
```

**Validação**:
- [ ] Menu de opções funciona
- [ ] Item enviado para compra
- [ ] Badge exibido corretamente
- [ ] Testes passam

---

#### Fase 24: Implementar "Marcar como Substituído"
**Status**: ⏳ Pendente
**Objetivo**: Substituir produto faltante

**Tarefas**:
- [ ] Opção "Marcar como Substituído" no menu
- [ ] Modal com campo de texto (produto substituto)
- [ ] Use case `SubstituirItemUseCase`
- [ ] Item marcado como separado
- [ ] Badge "🔄 Substituiu: [Nome Original]"
- [ ] Cor verde claro

**Testes**:
```python
def test_substituir_item(client, logged_in_user):
    """Testa substituição de item"""
    pedido = criar_pedido_com_itens()
    item = pedido.itens[0]

    response = client.post(
        f'/pedidos/{pedido.id}/itens/{item.id}/substituir/',
        data={'produto_substituto': 'CABO USB-C'},
        HTTP_HX_REQUEST='true'
    )

    item.refresh_from_db()
    assert item.substituido is True
    assert item.produto_substituto == 'CABO USB-C'
    assert item.separado is True  # Conta como separado
```

**Validação**:
- [ ] Modal funcional
- [ ] Substituição registrada
- [ ] Badge correto
- [ ] Item conta como separado
- [ ] Testes passam

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
Setup Inicial       ⬜⬜⬜⬜ 0/4
Autenticação        ⬜⬜⬜⬜ 0/4
Parsing PDF         ⬜⬜⬜⬜ 0/4
Criação Pedidos     ⬜⬜⬜⬜ 0/4
Dashboard           ⬜⬜⬜⬜ 0/4
Separação           ⬜⬜⬜⬜⬜ 0/5
Painel Compras      ⬜⬜⬜ 0/3
Métricas/WebSocket  ⬜⬜⬜ 0/3
Deploy              ⬜⬜⬜⬜ 0/4

TOTAL: 0/35 fases (0%)
```

---

## 🎯 PRÓXIMA AÇÃO

**Aguardando início da Fase 1: Setup do Projeto Django**

Quando estiver pronto, diga: "Iniciar Fase 1" e o Claude começará o desenvolvimento seguindo TDD rigoroso.

---

**Última atualização**: 2025-10-24
**Versão do Planejamento**: 1.0
**Status**: Planejamento concluído, aguardando implementação
