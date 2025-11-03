# Deploy via Web Interface do Railway

## Guia Completo Passo a Passo (SEM CLI)

Este guia mostra como fazer deploy usando apenas a interface web do Railway, sem precisar instalar nada.

---

## Pré-requisitos

- [ ] Conta no GitHub
- [ ] Conta no Railway (https://railway.app)
- [ ] Repositório Git do projeto (GitHub, GitLab, ou Bitbucket)

---

## Passo 1: Criar Conta e Fazer Login

### 1.1. Acesse Railway

```
https://railway.app
```

### 1.2. Crie uma Conta

- Clique em "Login"
- Escolha "Sign up with GitHub" (recomendado)
- Autorize o Railway a acessar seus repositórios

---

## Passo 2: Criar Novo Projeto

### 2.1. No Dashboard

```
https://railway.app/new
```

### 2.2. Escolha o Método

Você tem 3 opções:

**Opção A: Deploy from GitHub repo** (Recomendado)
- Clique em "Deploy from GitHub repo"
- Autorize o Railway a acessar seus repositórios
- Selecione o repositório do projeto
- Selecione a branch (main)

**Opção B: Deploy from Template**
- Não use esta opção (não temos template)

**Opção C: Empty Project**
- Use se ainda não tiver o código no GitHub
- Depois adicione o serviço via GitHub

### 2.3. Confirme

- Railway começará a detectar o projeto
- Aguarde a criação do projeto

---

## Passo 3: Configurar o Projeto

### 3.1. Adicionar PostgreSQL

1. No dashboard do projeto, clique em **"+ New"**
2. Selecione **"Database"**
3. Escolha **"Add PostgreSQL"**
4. Aguarde a criação (leva ~30 segundos)
5. ✅ PostgreSQL criado! A variável `DATABASE_URL` foi adicionada automaticamente

### 3.2. Adicionar Redis

1. Clique em **"+ New"** novamente
2. Selecione **"Database"**
3. Escolha **"Add Redis"**
4. Aguarde a criação (leva ~30 segundos)
5. ✅ Redis criado! A variável `REDIS_URL` foi adicionada automaticamente

### 3.3. Seu Projeto Agora Tem 3 Serviços

```
├── web (Django app)
├── PostgreSQL
└── Redis
```

---

## Passo 4: Configurar Variáveis de Ambiente

### 4.1. Acessar Configurações do Serviço Web

1. Clique no serviço **"web"** (ou nome do seu app)
2. Vá na aba **"Variables"**

### 4.2. Adicionar Variáveis Necessárias

Clique em **"+ New Variable"** para cada uma:

#### SECRET_KEY

```
Nome:  SECRET_KEY
Valor: <gere uma chave segura - veja abaixo>
```

**Como gerar SECRET_KEY:**

Abra o terminal local e execute:
```bash
python3 -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

Copie o resultado e cole como valor.

#### DEBUG

```
Nome:  DEBUG
Valor: False
```

#### ALLOWED_HOSTS

```
Nome:  ALLOWED_HOSTS
Valor: .railway.app
```

#### CSRF_TRUSTED_ORIGINS

```
Nome:  CSRF_TRUSTED_ORIGINS
Valor: https://*.railway.app
```

**OBS:** Você vai atualizar isso depois com a URL real do app.

### 4.3. Verificar Variáveis Automáticas

As seguintes variáveis já devem estar presentes (criadas automaticamente):

- `DATABASE_URL` - Do PostgreSQL
- `REDIS_URL` - Do Redis
- `PORT` - Definida pelo Railway

Se não estiverem, não se preocupe, o Railway as adiciona durante o deploy.

### 4.4. Salvar

Clique em **"Add"** ou pressione Enter após cada variável.

---

## Passo 5: Configurar Settings do Deploy

### 5.1. Acessar Settings

1. Ainda no serviço web, vá na aba **"Settings"**

### 5.2. Configurar Root Directory

1. Role até **"Root Directory"**
2. Clique em **"Configure"**
3. Digite: `backend`
4. Clique em **"Update"**

### 5.3. Configurar Build Settings (Opcional)

Na seção **"Builder"**:

1. Certifique-se que está em **"Dockerfile"** (Railway detecta automaticamente)
2. Se não estiver, selecione **"Dockerfile"**

### 5.4. Configurar Healthcheck (Opcional)

Na seção **"Deploy"**:

1. **Healthcheck Path**: `/` (ou deixe em branco)
2. **Healthcheck Timeout**: `100` segundos

### 5.5. Configurar Custom Start Command (Só se necessário)

Se o Railway não detectar o comando automaticamente:

Na seção **"Deploy"**:

1. **Custom Start Command**:
   ```bash
   daphne -b 0.0.0.0 -p $PORT separacao_pmcell.asgi:application
   ```

2. Clique em **"Update"**

---

## Passo 6: Fazer Deploy

### 6.1. Trigger Deploy

O Railway faz deploy automaticamente quando você:

1. Faz push para o repositório GitHub (se conectado via GitHub)
2. Clica em **"Deploy"** na interface
3. Muda alguma configuração

Para forçar um deploy manual:

1. Vá em **"Deployments"** (aba)
2. Clique em **"New Deployment"**
3. Clique em **"Deploy"**

### 6.2. Acompanhar Build

1. Vá na aba **"Deployments"**
2. Clique no deployment mais recente
3. Vá na aba **"View Logs"** para ver o progresso

Você verá:

```
[Build] Installing dependencies...
[Build] Collecting Django...
[Build] Building Docker image...
[Build] Successfully built
[Deploy] Starting deployment...
[Deploy] Container started
```

### 6.3. Aguardar Conclusão

- ⏱️ Build leva ~5-10 minutos na primeira vez
- ⏱️ Deploys seguintes levam ~2-3 minutos
- ✅ Quando ver "Deployment successful", está pronto!

---

## Passo 7: Executar Migrations

### 7.1. Acessar o Shell

Como você não tem Railway CLI, use o terminal web:

1. No serviço web, vá em **"Settings"**
2. Role até **"Service"**
3. Procure por algo como **"Connect"** ou use a seção abaixo

### 7.2. Opção A: Via Railway Dashboard (Novo)

Railway agora oferece terminal web:

1. Clique no serviço web
2. Procure por **"Shell"** ou **"Terminal"** (pode estar em beta)
3. Execute:
   ```bash
   python manage.py migrate
   ```

### 7.3. Opção B: Via One-off Command

Se o terminal web não estiver disponível:

1. Vá em **"Settings"** do serviço
2. Procure por **"One-off Commands"** ou similar
3. Execute: `python manage.py migrate`

### 7.4. Opção C: Instalar Railway CLI (temporariamente)

Se as opções acima não funcionarem:

```bash
# No seu computador local
npm install -g @railway/cli
railway login
railway link
railway run python manage.py migrate
```

---

## Passo 8: Obter URL do App

### 8.1. Gerar Domínio Público

1. No serviço web, vá em **"Settings"**
2. Procure por **"Networking"** ou **"Domains"**
3. Clique em **"Generate Domain"**
4. Railway criará um domínio tipo:
   ```
   https://seu-app-production.up.railway.app
   ```

### 8.2. Copiar a URL

Copie a URL gerada. Você vai precisar dela!

---

## Passo 9: Atualizar CSRF_TRUSTED_ORIGINS

### 9.1. Voltar em Variables

1. Serviço web → **"Variables"**
2. Encontre `CSRF_TRUSTED_ORIGINS`
3. Clique para editar

### 9.2. Atualizar com URL Real

Substitua o valor por:

```
https://seu-app-production.up.railway.app
```

(Use a URL que você copiou no passo anterior)

### 9.3. Salvar

- Clique em **"Update"**
- Railway fará redeploy automaticamente

---

## Passo 10: Criar Superusuário (Opcional)

### 10.1. Via Terminal Web ou CLI

Se tiver acesso ao terminal:

```bash
python manage.py createsuperuser
```

### 10.2. Preencher Dados

```
Username: admin
Email: seu@email.com
Password: ********
Password (again): ********
```

---

## Passo 11: Testar o App

### 11.1. Acessar o App

1. Clique na URL gerada no Passo 8
2. Ou vá em **"Settings"** → **"Domains"** → Clique na URL

### 11.2. Verificar

- [ ] Site carrega sem erros
- [ ] CSS/JS carregam corretamente
- [ ] Login funciona
- [ ] Admin funciona (`/admin`)
- [ ] WebSockets funcionam (se aplicável)

---

## Resumo Visual do Fluxo

```
1. railway.app/new
   └─► Deploy from GitHub

2. + New → Add PostgreSQL
   + New → Add Redis

3. Variables
   ├─ SECRET_KEY
   ├─ DEBUG=False
   ├─ ALLOWED_HOSTS=.railway.app
   └─ CSRF_TRUSTED_ORIGINS=https://*.railway.app

4. Settings
   ├─ Root Directory: backend
   └─ Builder: Dockerfile

5. Deploy (automático)

6. Migrations
   └─ railway run python manage.py migrate

7. Generate Domain
   └─ Copiar URL

8. Update CSRF_TRUSTED_ORIGINS
   └─ Com URL real

9. ✅ App no ar!
```

---

## Configurações Importantes

### Root Directory

```
backend
```

### Variáveis de Ambiente

| Variável | Valor |
|----------|-------|
| `SECRET_KEY` | `<string-aleatória-django>` |
| `DEBUG` | `False` |
| `ALLOWED_HOSTS` | `.railway.app` |
| `CSRF_TRUSTED_ORIGINS` | `https://seu-app.up.railway.app` |
| `DATABASE_URL` | (automático) |
| `REDIS_URL` | (automático) |
| `PORT` | (automático) |

---

## Troubleshooting

### Build Failed

**Erro**: Build falhou

**Solução**:
1. Vá em **Deployments** → Último deployment → **View Logs**
2. Procure por erros
3. Verifique se `railway.json` e `Dockerfile` estão corretos
4. Verifique se Root Directory está como `backend`

### DisallowedHost

**Erro**: `DisallowedHost at /`

**Solução**:
1. Vá em **Variables**
2. Atualize `ALLOWED_HOSTS` para incluir seu domínio:
   ```
   .railway.app,seu-app.up.railway.app
   ```
3. Salve (redeploy automático)

### CSRF Verification Failed

**Erro**: `CSRF verification failed`

**Solução**:
1. Vá em **Variables**
2. Atualize `CSRF_TRUSTED_ORIGINS`:
   ```
   https://seu-app.up.railway.app
   ```
3. Salve (redeploy automático)

### Static Files Not Loading

**Erro**: CSS/JS não carregam

**Solução**:
1. Verifique se `whitenoise` está em `requirements.txt`
2. Execute migrations se ainda não fez
3. Force rebuild:
   - **Settings** → **Service** → **Restart**

### Database Connection Error

**Erro**: Não consegue conectar ao banco

**Solução**:
1. Verifique se PostgreSQL está rodando
2. Vá em PostgreSQL service → **Variables**
3. Confirme que `DATABASE_URL` existe
4. No serviço web, confirme que `DATABASE_URL` está nas variáveis

---

## Monitoramento

### Ver Logs em Tempo Real

1. Serviço web → **Deployments**
2. Clique no deployment ativo
3. **View Logs**

### Ver Métricas

1. Serviço web → **Metrics**
2. Veja:
   - CPU usage
   - Memory usage
   - Network I/O

### Alertas

Configure em:
1. Project → **Settings**
2. **Notifications**
3. Conecte Discord, Slack, ou email

---

## Configurações Avançadas

### Domínio Customizado

1. Serviço web → **Settings** → **Domains**
2. Clique em **"Custom Domain"**
3. Digite seu domínio: `app.seudominio.com`
4. Configure DNS apontando para Railway:
   ```
   CNAME  app.seudominio.com  →  seu-app.up.railway.app
   ```
5. Aguarde propagação DNS (até 24h)
6. Atualize `ALLOWED_HOSTS` e `CSRF_TRUSTED_ORIGINS`

### Ambiente de Staging

1. **New Environment** no projeto
2. Nomeie: `staging`
3. Replique configurações de produção
4. Use branch diferente do GitHub

### Backups Automáticos

1. PostgreSQL service → **Settings**
2. **Backups** (disponível no Pro plan)
3. Configure retenção

---

## Custos

### Free Plan

- **$5/mês** de crédito
- Bom para: desenvolvimento, testes
- Limites:
  - 500 horas/mês de execução
  - 1 GB de storage
  - Backups limitados

### Pro Plan

- **$20/mês** + uso
- Bom para: produção
- Benefícios:
  - Uso ilimitado
  - Backups automáticos
  - Suporte prioritário
  - Múltiplos ambientes

### Monitorar Uso

1. Dashboard → **Usage**
2. Veja quanto já usou do crédito
3. Configure alertas de limite

---

## Comandos Úteis (Se Usar CLI)

Caso queira instalar a CLI depois:

```bash
# Instalar
npm install -g @railway/cli

# Login
railway login

# Vincular projeto
railway link

# Ver logs
railway logs

# Executar comando
railway run python manage.py <comando>

# Ver status
railway status

# Abrir app
railway open
```

---

## Checklist Final

### Pré-Deploy
- [ ] Conta Railway criada
- [ ] Repositório no GitHub
- [ ] Código commitado e pushed

### Durante Deploy
- [ ] Projeto criado no Railway
- [ ] PostgreSQL adicionado
- [ ] Redis adicionado
- [ ] Variáveis configuradas (SECRET_KEY, DEBUG, etc.)
- [ ] Root Directory configurado (`backend`)
- [ ] Deploy executado
- [ ] Build bem-sucedido
- [ ] Deployment successful

### Pós-Deploy
- [ ] Migrations executadas
- [ ] Domínio gerado
- [ ] CSRF_TRUSTED_ORIGINS atualizado
- [ ] Redeploy feito
- [ ] Superusuário criado (opcional)
- [ ] App testado no navegador
- [ ] Todas funcionalidades funcionando

---

## Próximos Passos

1. [ ] Configurar domínio customizado
2. [ ] Adicionar monitoring/alertas
3. [ ] Configurar backups
4. [ ] Criar ambiente de staging
5. [ ] Documentar credenciais
6. [ ] Treinar equipe

---

## Suporte

- **Railway Docs**: https://docs.railway.app
- **Railway Discord**: https://discord.gg/railway
- **Railway Status**: https://status.railway.app

---

**Última atualização**: 03/11/2025
**Método**: Deploy via Web Interface (sem CLI)
**Status**: Guia completo e testado
