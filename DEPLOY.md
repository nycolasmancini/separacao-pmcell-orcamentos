# Guia de Deploy - Web App Separação de Pedidos PMCELL

Este guia mostra como fazer deploy do webapp no Railway.

## Pré-requisitos

1. Conta no Railway: https://railway.app/ (pode usar conta GitHub)
2. Railway CLI instalado (opcional, mas recomendado):
   ```bash
   npm install -g @railway/cli
   ```
3. Git configurado no projeto

## Estrutura do Projeto

O projeto já está preparado para deploy com os seguintes arquivos:

- `railway.json` - Configuração do Railway
- `nixpacks.toml` - Configuração do build
- `Procfile` - Comando de start
- `runtime.txt` - Versão do Python
- `backend/requirements.txt` - Dependências Python
- `backend/.env.example` - Exemplo de variáveis de ambiente

## Passo a Passo - Deploy no Railway

### 1. Inicializar Repositório Git (se ainda não fez)

```bash
cd /Users/nycolasmancini/Desktop/separacao-pmcell/orcamentos-modelo

# Inicializar git (se necessário)
git init

# Adicionar arquivos
git add .

# Fazer commit
git commit -m "Preparar projeto para deploy no Railway"
```

### 2. Criar Projeto no Railway

**Opção A: Via Railway CLI (Recomendado)**

```bash
# Login no Railway
railway login

# Criar novo projeto
railway init

# Link com o projeto
railway link
```

**Opção B: Via Web Interface**

1. Acesse https://railway.app/
2. Clique em "New Project"
3. Escolha "Deploy from GitHub repo"
4. Conecte sua conta GitHub e selecione o repositório
   - OU escolha "Empty Project" e conecte depois

### 3. Adicionar Serviços no Railway

Você precisa de 3 serviços:

#### A. PostgreSQL

1. No dashboard do Railway, clique em "New"
2. Selecione "Database" → "PostgreSQL"
3. O Railway criará automaticamente a variável `DATABASE_URL`

#### B. Redis

1. No dashboard do Railway, clique em "New"
2. Selecione "Database" → "Redis"
3. O Railway criará automaticamente a variável `REDIS_URL`

#### C. Web Application (Django)

1. No dashboard do Railway, clique em "New"
2. Selecione "GitHub Repo" (se ainda não conectou)
3. OU clique em "Deploy from GitHub repo" e selecione o repositório

### 4. Configurar Variáveis de Ambiente

No serviço da aplicação Django, vá em "Variables" e adicione:

```bash
# Django Core (OBRIGATÓRIO)
SECRET_KEY=<gere-uma-chave-secreta-aleatoria-aqui>
DEBUG=False
ALLOWED_HOSTS=.railway.app

# URLs dos serviços (já fornecidas automaticamente pelo Railway)
DATABASE_URL=${{Postgres.DATABASE_URL}}
REDIS_URL=${{Redis.REDIS_URL}}

# Security
CSRF_TRUSTED_ORIGINS=https://${{RAILWAY_PUBLIC_DOMAIN}}

# Application Settings
LANGUAGE_CODE=pt-br
TIME_ZONE=America/Sao_Paulo
SESSION_COOKIE_AGE=28800
CACHE_TIMEOUT=300
```

**Como gerar SECRET_KEY:**

```bash
python3 -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

### 5. Configurar Deploy Settings

No serviço da aplicação:

1. Vá em "Settings"
2. Em "Build Command", certifique-se de que está vazio (usaremos railway.json)
3. Em "Start Command", certifique-se de que está vazio (usaremos Procfile)
4. Em "Root Directory", deixe vazio (ou configure se necessário)

### 6. Deploy

**Via Railway Web:**
- O deploy começará automaticamente após conectar o repositório
- Acompanhe os logs em tempo real no dashboard

**Via Railway CLI:**
```bash
railway up
```

### 7. Migrar o Banco de Dados

Após o primeiro deploy bem-sucedido, você precisa rodar as migrações:

**Via Railway CLI:**
```bash
railway run python backend/manage.py migrate
railway run python backend/manage.py createsuperuser
```

**Via Railway Web:**
1. Vá no serviço da aplicação
2. Clique em "Deploy Logs"
3. No canto superior direito, clique nos três pontinhos
4. Selecione "Run Command"
5. Execute:
   ```bash
   cd backend && python manage.py migrate
   cd backend && python manage.py createsuperuser
   ```

### 8. Coletar Arquivos Estáticos

O comando `collectstatic` já roda automaticamente no build (veja `railway.json`), mas você pode rodar manualmente:

```bash
railway run python backend/manage.py collectstatic --noinput
```

### 9. Acessar a Aplicação

1. No dashboard do Railway, clique no serviço da aplicação
2. Você verá a URL pública (ex: `https://seu-app.up.railway.app`)
3. Acesse a URL no navegador
4. Faça login com o superuser criado

### 10. Monitoramento

No Railway dashboard você pode:
- Ver logs em tempo real
- Monitorar uso de recursos (CPU, RAM, Network)
- Ver métricas de performance
- Configurar alertas

## Solução de Problemas

### Erro: "Application failed to respond"

1. Verifique se todas as variáveis de ambiente estão configuradas
2. Verifique os logs de deploy
3. Certifique-se de que as migrações foram executadas

### Erro: "Could not connect to Redis"

1. Verifique se o serviço Redis está rodando
2. Verifique se a variável `REDIS_URL` está configurada corretamente
3. No Railway, certifique-se de que os serviços estão na mesma região

### Erro: "Could not connect to Database"

1. Verifique se o serviço PostgreSQL está rodando
2. Verifique se a variável `DATABASE_URL` está configurada corretamente
3. Execute as migrações novamente

### Erro 400 Bad Request

1. Verifique `ALLOWED_HOSTS` nas variáveis de ambiente
2. Verifique `CSRF_TRUSTED_ORIGINS` nas variáveis de ambiente
3. Use o formato correto: `https://seu-app.up.railway.app`

## Comandos Úteis do Railway CLI

```bash
# Ver logs em tempo real
railway logs

# Rodar comandos no ambiente de produção
railway run <comando>

# Abrir shell no ambiente de produção
railway shell

# Ver status dos serviços
railway status

# Ver variáveis de ambiente
railway variables

# Deletar o projeto
railway delete
```

## Backup e Manutenção

### Backup do Banco de Dados

```bash
# Fazer backup
railway run pg_dump $DATABASE_URL > backup.sql

# Restaurar backup
railway run psql $DATABASE_URL < backup.sql
```

### Limpar Cache Redis

```bash
railway run python backend/manage.py shell
>>> from django.core.cache import cache
>>> cache.clear()
>>> exit()
```

## Custos

Railway oferece:
- **Free Tier**: $5 de crédito por mês (suficiente para testes)
- **Hobby Plan**: $5/mês por serviço (para produção)
- **Pro Plan**: $20/mês com mais recursos

Monitore seu uso no dashboard para evitar cobranças inesperadas.

## Próximos Passos

1. Configurar domínio customizado (opcional)
2. Configurar SSL (já incluído no Railway)
3. Configurar backups automáticos
4. Configurar monitoramento de erros (Sentry)
5. Configurar CI/CD para deploys automáticos

## Suporte

- Documentação Railway: https://docs.railway.app/
- Discord Railway: https://discord.gg/railway
- Documentação Django: https://docs.djangoproject.com/

---

Deploy preparado na Fase 35 do projeto. Sistema já configurado com:
- PostgreSQL para banco de dados
- Redis para cache e WebSockets
- Whitenoise para arquivos estáticos
- Daphne (ASGI) para servir a aplicação
- Django Channels para WebSockets
