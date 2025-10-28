# 🚀 Guia de Deploy - Web App Separação de Pedidos PMCELL

Este guia contém instruções completas para fazer deploy da aplicação no Railway.app.

---

## 📋 Índice

1. [Pré-requisitos](#pré-requisitos)
2. [Preparação Local](#preparação-local)
3. [Deploy no Railway.app](#deploy-no-railwayapp)
4. [Configuração Pós-Deploy](#configuração-pós-deploy)
5. [Validação](#validação)
6. [Troubleshooting](#troubleshooting)
7. [Manutenção](#manutenção)

---

## 1. Pré-requisitos

### Ferramentas Necessárias
- ✅ Git instalado e configurado
- ✅ Conta no GitHub (repositório deve estar no GitHub)
- ✅ Conta no Railway.app (gratuita para começar)
- ✅ Python 3.9+ instalado localmente

### Validações Locais
Antes de fazer deploy, certifique-se de que:

```bash
# 1. Todos os testes passam
cd backend/
pytest

# 2. Collectstatic funciona
python manage.py collectstatic --noinput

# 3. Validação de configuração passa
python validar_fase35.py
```

---

## 2. Preparação Local

### 2.1 Gerar SECRET_KEY Segura

```python
# No terminal Python
from django.core.management.utils import get_random_secret_key
print(get_random_secret_key())
```

Copie a chave gerada - você vai precisar dela no Railway.

### 2.2 Commit e Push para GitHub

```bash
# Certifique-se de que todas as mudanças estão commitadas
git status
git add .
git commit -m "feat: Preparar aplicação para deploy (Fase 35)"
git push origin main
```

---

## 3. Deploy no Railway.app

### 3.1 Criar Projeto no Railway

1. Acesse https://railway.app/
2. Clique em **"New Project"**
3. Selecione **"Deploy from GitHub repo"**
4. Autorize o Railway a acessar seu repositório GitHub
5. Selecione o repositório `separacao-pmcell/orcamentos-modelo`
6. Railway detectará automaticamente que é um projeto Django

### 3.2 Adicionar PostgreSQL

1. No seu projeto Railway, clique em **"+ New"**
2. Selecione **"Database"** → **"PostgreSQL"**
3. Railway criará o banco e a variável `DATABASE_URL` automaticamente

### 3.3 Adicionar Redis

1. No seu projeto Railway, clique em **"+ New"**
2. Selecione **"Database"** → **"Redis"**
3. Railway criará o Redis e a variável `REDIS_URL` automaticamente

### 3.4 Configurar Variáveis de Ambiente

1. Clique no serviço da sua aplicação (não no PostgreSQL/Redis)
2. Vá para a aba **"Variables"**
3. Adicione as seguintes variáveis:

```bash
# Django Core
SECRET_KEY=<cole-a-chave-gerada-anteriormente>
DEBUG=False
ALLOWED_HOSTS=localhost,127.0.0.1,.railway.app

# Database (já configurado automaticamente pelo Railway)
# DATABASE_URL=postgresql://...  (não precisa adicionar)

# Redis (já configurado automaticamente pelo Railway)
# REDIS_URL=redis://...  (não precisa adicionar)

# Django Security (substitua pela URL do seu app)
CSRF_TRUSTED_ORIGINS=https://seu-app-nome.railway.app

# Localização (opcional - já tem defaults)
LANGUAGE_CODE=pt-br
TIME_ZONE=America/Sao_Paulo
```

**IMPORTANTE**: Após adicionar todas as variáveis, clique em **"Deploy"** ou espere o deploy automático.

### 3.5 Configurar Domínio

1. Na aba **"Settings"** do seu serviço
2. Vá em **"Networking"** → **"Public Networking"**
3. Clique em **"Generate Domain"**
4. Copie a URL gerada (ex: `https://seu-app-nome.railway.app`)
5. **IMPORTANTE**: Volte nas variáveis de ambiente e atualize `CSRF_TRUSTED_ORIGINS` com essa URL

---

## 4. Configuração Pós-Deploy

### 4.1 Verificar Logs

1. Na aba **"Deployments"**, clique no deploy mais recente
2. Verifique se não há erros nos logs
3. Procure por: `Starting server with Daphne...`

### 4.2 Rodar Migrations

As migrations já rodam automaticamente pelo `Procfile`, mas se precisar rodar manualmente:

1. Na aba do seu serviço, clique em **"..."** (três pontos)
2. Selecione **"Run a command"**
3. Execute:

```bash
python manage.py migrate
```

### 4.3 Criar Superusuário

1. No Railway, vá em **"..."** → **"Run a command"**
2. Execute:

```bash
python manage.py shell
```

3. No shell que abrir, execute:

```python
from core.domain.models import Usuario

# Criar admin
admin = Usuario.objects.create_user(
    login='999',  # Login numérico de 3 dígitos
    pin='1234',   # PIN de 4 dígitos
    nome='Administrador',
    tipo_usuario='admin'
)
print(f"Admin criado: {admin.nome}")
exit()
```

### 4.4 Criar Usuários de Teste

Execute no shell do Railway:

```python
from core.domain.models import Usuario

# Vendedor
vendedor = Usuario.objects.create_user(
    login='101',
    pin='1111',
    nome='Vendedor Teste',
    tipo_usuario='vendedor'
)

# Separador
separador = Usuario.objects.create_user(
    login='201',
    pin='2222',
    nome='Separador Teste',
    tipo_usuario='separador'
)

# Compradora
compradora = Usuario.objects.create_user(
    login='301',
    pin='3333',
    nome='Compradora Teste',
    tipo_usuario='compradora'
)

print("Usuários de teste criados com sucesso!")
exit()
```

---

## 5. Validação

### 5.1 Checklist Pós-Deploy

Acesse sua aplicação em `https://seu-app-nome.railway.app` e valide:

- [ ] **Login funciona**: Tente logar com um dos usuários criados
- [ ] **Upload de PDF funciona**: Tente fazer upload de um PDF de orçamento
- [ ] **Dashboard carrega**: Verifique se os pedidos aparecem
- [ ] **WebSockets funcionam**: Abra em duas abas e marque um item - deve atualizar em tempo real
- [ ] **Marcação de separação funciona**: Marque alguns itens como separados
- [ ] **Sistema de compras funciona**: Envie um item para compra e verifique no painel de compras
- [ ] **Métricas aparecem**: Verifique se o tempo médio está sendo calculado
- [ ] **Admin do Django funciona**: Acesse `/admin` e logue com o superusuário
- [ ] **Arquivos estáticos carregam**: CSS e JavaScript funcionam corretamente
- [ ] **HTTPS funciona**: URL deve começar com `https://`

### 5.2 Testar WebSockets

```bash
# No terminal local, teste a conexão WebSocket
pip install websocket-client

python -c "
from websocket import create_connection
ws = create_connection('wss://seu-app-nome.railway.app/ws/pedidos/')
print('WebSocket conectado com sucesso!')
ws.close()
"
```

---

## 6. Troubleshooting

### ❌ Erro: "DisallowedHost"

**Causa**: `ALLOWED_HOSTS` não configurado corretamente

**Solução**:
```bash
# Adicione sua URL do Railway em ALLOWED_HOSTS
ALLOWED_HOSTS=.railway.app,seu-app-nome.railway.app
```

### ❌ Erro: "CSRF verification failed"

**Causa**: `CSRF_TRUSTED_ORIGINS` não configurado

**Solução**:
```bash
# Configure com a URL completa (com https://)
CSRF_TRUSTED_ORIGINS=https://seu-app-nome.railway.app
```

### ❌ Erro: "No module named 'decouple'"

**Causa**: Dependências não instaladas

**Solução**:
```bash
# Verifique se requirements.txt está no diretório backend/
# Railway deve instalar automaticamente
# Se não, force rebuild do projeto
```

### ❌ Erro: "WebSocket connection failed"

**Causa**: Daphne não está rodando ou Redis não está configurado

**Solução**:
```bash
# 1. Verifique se REDIS_URL está configurado
# 2. Verifique os logs: procure por "Daphne"
# 3. Certifique-se de que o Procfile está usando Daphne:
#    web: daphne -b 0.0.0.0 -p $PORT separacao_pmcell.asgi:application
```

### ❌ Erro: "Static files não carregam"

**Causa**: Collectstatic não foi executado

**Solução**:
```bash
# O Procfile deve ter:
release: python manage.py migrate --noinput && python manage.py collectstatic --noinput

# Se não funcionar, execute manualmente:
python manage.py collectstatic --noinput
```

### ❌ Erro: "Application crashed"

**Solução**:
1. Verifique os logs no Railway
2. Procure por erros de importação ou configuração
3. Certifique-se de que `runtime.txt` tem `python-3.9.6`
4. Verifique se todas as variáveis de ambiente estão configuradas

---

## 7. Manutenção

### 7.1 Monitoramento

- **Logs**: Acesse Railway → Seu serviço → "Deployments" → Ver logs
- **Métricas**: Railway mostra CPU, RAM e Network usage
- **Uptime**: Configure alertas no Railway (Settings → Healthcheck)

### 7.2 Backup do Banco de Dados

```bash
# Railway CLI (instale com: npm i -g @railway/cli)
railway login
railway run pg_dump $DATABASE_URL > backup_$(date +%Y%m%d).sql
```

### 7.3 Rollback

Se algo der errado após um deploy:

1. No Railway, vá em **"Deployments"**
2. Encontre o deploy anterior que funcionava
3. Clique em **"..."** → **"Redeploy"**

### 7.4 Atualizar Código

```bash
# Local
git add .
git commit -m "feat: Nova funcionalidade"
git push origin main

# Railway fará deploy automático
```

### 7.5 Escalar Aplicação

Se precisar de mais recursos:

1. Railway → Seu projeto → **"Settings"**
2. Vá em **"Resources"**
3. Aumente CPU/RAM conforme necessário (plano pago)

---

## 8. Custos Estimados

### Railway.app - Plano Hobby (Recomendado)

- **Custo**: ~$5-10/mês (500 horas de execução incluídas)
- **PostgreSQL**: Incluído
- **Redis**: Incluído
- **Tráfego**: 100GB/mês incluído
- **Sleeps**: Não dorme (sempre ativo)

### Plano Developer (Gratuito)

- **Limitações**:
  - Aplicação dorme após inatividade
  - 500MB RAM
  - 5GB storage
  - Bom para testes, não recomendado para produção

---

## 9. Suporte

### Documentação
- Railway: https://docs.railway.app/
- Django: https://docs.djangoproject.com/
- Django Channels: https://channels.readthedocs.io/

### Logs do Projeto
```bash
# Ver todos os logs em tempo real
railway logs

# Ver logs de um serviço específico
railway logs --service seu-app-nome
```

---

## ✅ Deploy Concluído!

Após seguir todos os passos acima, sua aplicação estará rodando em produção com:

- ✅ HTTPS habilitado
- ✅ PostgreSQL configurado
- ✅ Redis funcionando (cache + WebSockets)
- ✅ Arquivos estáticos servidos pelo Whitenoise
- ✅ Daphne rodando (suporte a WebSockets)
- ✅ Migrations aplicadas
- ✅ Usuários criados
- ✅ Sistema 100% funcional

**URL de Produção**: `https://seu-app-nome.railway.app`

---

**Data**: 2025-10-27
**Fase**: 35 - Deploy para Produção
**Versão**: 1.0.0
