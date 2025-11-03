# Deploy Web Railway - Guia Simplificado

## 🚀 Deploy em 10 Minutos (Via Web)

---

## ✅ Pré-requisitos

- Conta no GitHub (com seu projeto lá)
- Conta no Railway (crie em https://railway.app)

---

## 📝 Passo a Passo

### 1️⃣ Criar Projeto (2 min)

1. Acesse: https://railway.app/new
2. Clique em **"Deploy from GitHub repo"**
3. Autorize o Railway
4. Selecione seu repositório
5. Selecione branch: `main`

---

### 2️⃣ Adicionar Bancos (1 min)

**PostgreSQL:**
1. Clique **"+ New"** → **"Database"** → **"Add PostgreSQL"**
2. Aguarde criação (30s)

**Redis:**
1. Clique **"+ New"** → **"Database"** → **"Add Redis"**
2. Aguarde criação (30s)

✅ Agora você tem 3 serviços: web, PostgreSQL, Redis

---

### 3️⃣ Gerar SECRET_KEY (1 min)

No seu computador local, execute:

```bash
python3 -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

Copie o resultado (algo como: `django-insecure-abc123...`)

---

### 4️⃣ Configurar Variáveis (2 min)

1. Clique no serviço **web**
2. Vá em **"Variables"**
3. Adicione cada variável clicando **"+ New Variable"**:

```
SECRET_KEY = <cole-a-chave-gerada-acima>
DEBUG = False
ALLOWED_HOSTS = .railway.app
CSRF_TRUSTED_ORIGINS = https://*.railway.app
```

---

### 5️⃣ Configurar Root Directory (1 min)

1. Ainda no serviço web, vá em **"Settings"**
2. Procure **"Root Directory"**
3. Configure: `backend`
4. Clique **"Update"**

**OBS:** Se você já fez o push do código com `railway.json`, o Railway detectará automaticamente. Caso contrário, configure manualmente.

---

### 6️⃣ Fazer Deploy (3 min)

O Railway já começou o deploy automaticamente!

1. Vá em **"Deployments"**
2. Clique no deployment em andamento
3. Clique em **"View Logs"**
4. Aguarde até ver: **"Deployment successful"**

---

### 7️⃣ Executar Migrations (1 min)

**Opção A: Se tiver Railway CLI instalada:**
```bash
npm install -g @railway/cli
railway login
railway link
railway run python manage.py migrate
```

**Opção B: Via terminal web do Railway** (se disponível):
1. Clique no serviço web
2. Procure por **"Shell"** ou **"Terminal"**
3. Execute: `python manage.py migrate`

---

### 8️⃣ Gerar URL do App (1 min)

1. Serviço web → **"Settings"**
2. Procure **"Networking"** ou **"Domains"**
3. Clique **"Generate Domain"**
4. Copie a URL gerada (ex: `https://seu-app.up.railway.app`)

---

### 9️⃣ Atualizar CSRF (1 min)

1. Serviço web → **"Variables"**
2. Clique em `CSRF_TRUSTED_ORIGINS`
3. Mude para: `https://seu-app.up.railway.app` (URL do passo anterior)
4. Clique **"Update"**

Railway fará redeploy automático (aguarde 2-3 min)

---

### 🔟 Testar! (1 min)

Clique na URL gerada e teste seu app!

---

## 🎯 Resumo Visual

```
railway.app/new
    ↓
Deploy from GitHub
    ↓
+ PostgreSQL + Redis
    ↓
Variables (SECRET_KEY, DEBUG, etc.)
    ↓
Settings → Root Directory: backend
    ↓
Deploy (automático)
    ↓
Migrations: railway run python manage.py migrate
    ↓
Generate Domain
    ↓
Update CSRF_TRUSTED_ORIGINS
    ↓
✅ PRONTO!
```

---

## 📋 Variáveis Necessárias

| Variável | Valor |
|----------|-------|
| `SECRET_KEY` | Gerado pelo comando Python |
| `DEBUG` | `False` |
| `ALLOWED_HOSTS` | `.railway.app` |
| `CSRF_TRUSTED_ORIGINS` | URL do seu app |

As outras (`DATABASE_URL`, `REDIS_URL`, `PORT`) são criadas automaticamente!

---

## 🔧 Problemas Comuns

### DisallowedHost?
Variables → `ALLOWED_HOSTS` → adicione sua URL completa

### CSRF Error?
Variables → `CSRF_TRUSTED_ORIGINS` → use URL completa com `https://`

### Build Failed?
Deployments → View Logs → veja o erro
- Geralmente é: Root Directory incorreto ou Dockerfile com problema

---

## 💰 Custos

**Grátis**: $5/mês de crédito (suficiente para desenvolvimento)

---

## 📚 Documentação Completa

- **Guia Detalhado**: `DEPLOY_WEB_RAILWAY.md`
- **Arquitetura**: `ARCHITECTURE.md`
- **Troubleshooting**: `RAILWAY_DEPLOY_GUIDE.md`

---

## ✅ Checklist Rápido

- [ ] Projeto criado no Railway
- [ ] PostgreSQL adicionado
- [ ] Redis adicionado
- [ ] SECRET_KEY configurada
- [ ] Outras variáveis configuradas
- [ ] Root Directory = `backend`
- [ ] Deploy concluído com sucesso
- [ ] Migrations executadas
- [ ] URL gerada
- [ ] CSRF_TRUSTED_ORIGINS atualizada
- [ ] App testado e funcionando

---

Pronto! Em 10 minutos seu app está no ar! 🎉
