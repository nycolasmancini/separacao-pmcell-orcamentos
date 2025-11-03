# Deploy Rápido via Railway CLI

⚠️ **IMPORTANTE:** Este projeto requer configurar o Root Directory para `/backend` no Railway. Se você fizer deploy via CLI e encontrar erro "pip: command not found", configure o Root Directory na interface web conforme explicado abaixo.

Tudo já está preparado! Siga estes passos no seu terminal:

## 1. Login no Railway (Interativo)

```bash
cd /Users/nycolasmancini/Desktop/separacao-pmcell/orcamentos-modelo
railway login
```

Isso abrirá uma página no navegador para você fazer login com GitHub ou email.

## 2. Criar e Inicializar Projeto

```bash
# Criar novo projeto (escolha um nome quando solicitado)
railway init

# Isso criará um projeto vazio no Railway
```

## 3. Adicionar PostgreSQL

```bash
railway add --database postgres
```

## 4. Adicionar Redis

```bash
railway add --database redis
```

## 5. Configurar Variáveis de Ambiente

```bash
# Gerar SECRET_KEY
export SECRET_KEY=$(python3 -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())")

# Configurar variáveis (pode fazer tudo de uma vez)
railway variables --set "SECRET_KEY=$SECRET_KEY" \
  --set "DEBUG=False" \
  --set "ALLOWED_HOSTS=.railway.app" \
  --set "LANGUAGE_CODE=pt-br" \
  --set "TIME_ZONE=America/Sao_Paulo" \
  --set "SESSION_COOKIE_AGE=28800" \
  --set "CACHE_TIMEOUT=300"

# OU configure uma por vez:
railway variables --set "SECRET_KEY=$SECRET_KEY"
railway variables --set "DEBUG=False"
railway variables --set "ALLOWED_HOSTS=.railway.app"
railway variables --set "LANGUAGE_CODE=pt-br"
railway variables --set "TIME_ZONE=America/Sao_Paulo"
railway variables --set "SESSION_COOKIE_AGE=28800"
railway variables --set "CACHE_TIMEOUT=300"
```

## 6. Deploy!

```bash
railway up
```

Isso fará o upload do código e iniciará o deploy. Aguarde alguns minutos.

## 7. Configurar Domínio

```bash
# Gerar domínio público
railway domain

# Isso criará um domínio como: seu-app-123456.up.railway.app
```

## 8. Configurar CSRF_TRUSTED_ORIGINS

Após obter o domínio, configure:

```bash
railway variables --set "CSRF_TRUSTED_ORIGINS=https://seu-app-123456.up.railway.app"
```

## 9. Migrar Banco de Dados

```bash
railway run python backend/manage.py migrate
railway run python backend/manage.py createsuperuser
```

Siga as instruções para criar o primeiro usuário admin.

## 10. Acessar a Aplicação

```bash
railway open
```

Ou acesse manualmente o domínio gerado no passo 7.

---

## Comandos Úteis

```bash
# Ver logs em tempo real
railway logs

# Ver status
railway status

# Ver variáveis configuradas
railway variables

# Abrir dashboard web
railway open

# Reconectar após reiniciar terminal
railway link
```

## Configurar Root Directory (CRÍTICO)

Após criar o projeto via CLI, você DEVE configurar o Root Directory via interface web:

1. Acesse https://railway.app e abra seu projeto
2. Clique no serviço da aplicação
3. Vá em **Settings** → **Build** ou **Source**
4. Em **Root Directory**, digite: `/backend`
5. Salve e aguarde o redeploy

**Por que isso é necessário?**
O Railway CLI não permite configurar o Root Directory. Sem isso, o deploy falhará com "pip: command not found" porque o Railway tentará rodar comandos antes do Python estar disponível.

## Solução de Problemas

### ❌ Erro: "pip: command not found" ou "Build failed"

**Causa:** Root Directory não foi configurado para `/backend`

**Solução:**
1. Acesse https://railway.app
2. Abra seu projeto e clique no serviço
3. Vá em Settings → Root Directory
4. Digite `/backend` e salve
5. Aguarde o redeploy automático

### Erro: "Application failed to respond"

1. Verifique os logs: `railway logs`
2. Certifique-se de que as variáveis estão configuradas
3. Rode as migrações novamente

### Erro: "Could not connect to Redis"

```bash
# Verificar se Redis foi adicionado
railway status

# Se não, adicione:
railway add --database redis
```

### Erro 400 Bad Request

Configure o CSRF_TRUSTED_ORIGINS com o domínio correto (passo 8).

---

## Alternativamente: Deploy via GitHub

Se preferir deploy automático:

1. Faça push para um repositório GitHub:
   ```bash
   git remote add origin https://github.com/seu-usuario/seu-repo.git
   git push -u origin main
   ```

2. No Railway Dashboard (https://railway.app/):
   - New Project → Deploy from GitHub repo
   - Selecione seu repositório
   - Adicione PostgreSQL e Redis como acima
   - Configure as variáveis de ambiente no dashboard web

Deploy está pronto! 🚀
