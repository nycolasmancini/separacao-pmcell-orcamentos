# Deploy via Railway Web Interface (RECOMENDADO)

✅ Código já foi enviado para o GitHub!
✅ Repositório: https://github.com/nycolasmancini/separacao-pmcell-orcamentos

## Passo a Passo Visual (5-10 minutos)

### 1. Acessar o Railway

Abra no navegador: **https://railway.app/**

### 2. Criar Conta / Login

- Clique em **"Login"** (canto superior direito)
- Escolha **"Login with GitHub"** (recomendado)
- Autorize o Railway a acessar sua conta GitHub

### 3. Criar Novo Projeto

- No dashboard, clique em **"New Project"**
- Selecione **"Deploy from GitHub repo"**
- Procure e selecione: **`nycolasmancini/separacao-pmcell-orcamentos`**
- Clique em **"Deploy Now"**

### 4. ⚠️ PASSO CRÍTICO: Configurar Root Directory

**IMPORTANTE:** Antes de continuar, você DEVE configurar o Root Directory, senão o deploy falhará com erro "pip: command not found".

1. Clique no serviço criado (o card da sua aplicação)
2. Vá na aba **"Settings"**
3. Procure a seção **"Build"** ou **"Source"**
4. Em **"Root Directory"**, digite: `/backend`
5. Clique em **"Save"** ou aguarde o auto-save

✅ Isso faz o Railway usar o diretório `/backend` como raiz, onde estão todas as configurações corretas.

🎉 O Railway começará o deploy automaticamente (ou reiniciará após salvar o Root Directory)!

### 5. Adicionar PostgreSQL

Enquanto o deploy acontece:

- No dashboard do projeto, clique em **"+ New"**
- Selecione **"Database"**
- Escolha **"Add PostgreSQL"**
- Aguarde a criação (leva ~30 segundos)

### 6. Adicionar Redis

- Novamente, clique em **"+ New"**
- Selecione **"Database"**
- Escolha **"Add Redis"**
- Aguarde a criação

### 7. Configurar Variáveis de Ambiente

Clique no **serviço da sua aplicação** (não nos bancos de dados), depois:

- Vá na aba **"Variables"**
- Clique em **"+ New Variable"** ou **"Raw Editor"**
- Cole as seguintes variáveis:

```env
SECRET_KEY=nr@_196)0i2gppt)cyv-0$1-7_m@=$p@8-bvolsxrr-ca2_nu%
DEBUG=False
ALLOWED_HOSTS=.railway.app
LANGUAGE_CODE=pt-br
TIME_ZONE=America/Sao_Paulo
SESSION_COOKIE_AGE=28800
CACHE_TIMEOUT=300
```

**IMPORTANTE:** O Railway automaticamente cria as variáveis `DATABASE_URL` e `REDIS_URL` - você NÃO precisa configurá-las manualmente!

### 8. Gerar Domínio Público

No serviço da aplicação:

- Vá na aba **"Settings"**
- Role até **"Networking"**
- Clique em **"Generate Domain"**
- Copie a URL gerada (ex: `https://separacao-pmcell-production-xxxx.up.railway.app`)

### 9. Configurar CSRF_TRUSTED_ORIGINS

Volte em **"Variables"** e adicione:

```env
CSRF_TRUSTED_ORIGINS=https://separacao-pmcell-production-xxxx.up.railway.app
```

Substitua pela URL que você copiou no passo 8!

### 10. Fazer Redeploy (se necessário)

Se o primeiro deploy já terminou antes de adicionar todas as variáveis:

- Vá em **"Deployments"**
- Clique nos **três pontinhos** do último deploy
- Selecione **"Redeploy"**

### 11. Migrar Banco de Dados

Após o deploy estar **"Success"** (com checkmark verde):

**Via Railway Web:**
- No serviço da aplicação, vá em **"Deployments"**
- Clique nos **três pontinhos** do deploy ativo
- Selecione **"View Logs"**
- No canto superior direito, clique no ícone de **">"** (Terminal/Shell)
- Execute os comandos:

```bash
cd backend && python manage.py migrate
cd backend && python manage.py createsuperuser
```

**Via Railway CLI (se você fez login no terminal):**

```bash
railway run python backend/manage.py migrate
railway run python backend/manage.py createsuperuser
```

Siga as instruções para criar o primeiro usuário admin:
- Username: (escolha um)
- Email: (seu email)
- Password: (senha forte)

### 11. Acessar a Aplicação 🚀

Clique no domínio gerado ou abra no navegador a URL do passo 7!

Faça login com o usuário criado no passo 11.

---

## Monitoramento e Logs

### Ver Logs em Tempo Real

1. Clique no serviço da aplicação
2. Vá em **"Deployments"**
3. Clique no deploy ativo
4. Veja os logs scrolling em tempo real

### Métricas de Uso

1. Clique no serviço
2. Vá em **"Metrics"**
3. Veja CPU, RAM, Network, etc.

### Custos

No menu lateral esquerdo:
- Clique em **"Usage"**
- Veja quanto do seu crédito gratuito ($5/mês) foi usado

---

## Solução de Problemas

### ❌ Erro "pip: command not found" ou "Build failed"

**Causa:** Root Directory não foi configurado para `/backend`

**Solução:**
1. Vá em **Settings** do serviço
2. Procure **"Root Directory"** na seção Build/Source
3. Digite: `/backend`
4. Salve e aguarde o redeploy automático

Este é o erro mais comum e é causado pelo Railway tentando rodar comandos antes do Python estar disponível!

### ❌ Deploy Falhou

**Erro: "Application failed to respond"**

1. Verifique se todas as variáveis de ambiente foram configuradas
2. Certifique-se de que PostgreSQL e Redis foram adicionados
3. Veja os logs de deploy para detalhes do erro

**Erro: "Build failed"**

1. Verifique os logs de build
2. Geralmente é problema com `requirements.txt`
3. Tente fazer redeploy

### ❌ Erro 400 Bad Request

Configure `CSRF_TRUSTED_ORIGINS` com o domínio correto (passo 8)

### ❌ Erro 500 Internal Server Error

1. Veja os logs da aplicação
2. Provavelmente as migrações não foram executadas (passo 10)
3. Execute: `railway run python backend/manage.py migrate`

### ❌ "Could not connect to database"

1. Verifique se PostgreSQL foi adicionado
2. Certifique-se de que os serviços estão na mesma região
3. O Railway cria automaticamente a variável `DATABASE_URL`

### ❌ "Could not connect to Redis"

1. Verifique se Redis foi adicionado
2. O Railway cria automaticamente a variável `REDIS_URL`

---

## Configurações Avançadas (Opcional)

### Domínio Customizado

1. No serviço da aplicação, vá em **"Settings"**
2. Em **"Networking"**, clique em **"Custom Domain"**
3. Adicione seu domínio (ex: `app.meusite.com`)
4. Configure o DNS do seu domínio conforme instruções

### Variáveis de Ambiente Adicionais

Se precisar adicionar mais variáveis no futuro:
- Vá em **"Variables"**
- Adicione as novas variáveis
- Faça redeploy (ou espere o próximo deploy automático via push)

### Deploy Automático

Por padrão, o Railway faz deploy automático quando você faz push para o GitHub!

Para testar:
1. Faça uma mudança no código
2. Commit e push para `main`
3. O Railway detectará e fará deploy automaticamente

### Desabilitar Deploy Automático

1. Vá em **"Settings"**
2. Em **"Deploy Triggers"**
3. Desative **"Automatic Deploys"**

---

## Comandos Úteis via Terminal (Opcional)

Se você fez login no Railway CLI localmente:

```bash
# Ver logs
railway logs

# Ver status
railway status

# Executar comandos
railway run python backend/manage.py <comando>

# Abrir shell Python/Django
railway run python backend/manage.py shell

# Abrir aplicação no navegador
railway open

# Ver variáveis
railway variables
```

---

## Backup do Banco de Dados

### Via Railway CLI

```bash
# Backup
railway run pg_dump $DATABASE_URL > backup_$(date +%Y%m%d).sql

# Restaurar
railway run psql $DATABASE_URL < backup_20250103.sql
```

### Via Interface Web

O Railway faz backups automáticos do PostgreSQL. Para restaurar:
1. Clique no serviço PostgreSQL
2. Vá em **"Backups"** (se disponível no seu plano)
3. Escolha o backup e restaure

---

## Próximos Passos

✅ Aplicação está no ar!
✅ Banco de dados PostgreSQL funcionando
✅ Redis funcionando para cache e WebSockets
✅ HTTPS configurado automaticamente
✅ Deploy automático configurado

### Melhorias Futuras

1. Configurar monitoramento de erros (Sentry)
2. Adicionar domínio customizado
3. Configurar backups automáticos programados
4. Adicionar mais workers se necessário
5. Configurar alertas de uso

---

## Suporte

- **Documentação Railway:** https://docs.railway.app/
- **Discord Railway:** https://discord.gg/railway
- **Status Railway:** https://status.railway.app/

🎉 **Seu webapp está pronto para uso em produção!**
