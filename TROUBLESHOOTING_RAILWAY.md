# Troubleshooting Railway - Erros Comuns

## ❌ Erro: "Dockerfile `Dockerfile` does not exist"

### Causa

Você configurou **Root Directory = backend** na interface do Railway, mas o railway.json estava configurado para procurar em `backend/Dockerfile`.

Quando Root Directory está configurado, o Railway procura o Dockerfile DENTRO do Root Directory.

### ✅ Solução (Escolha UMA das opções abaixo)

---

## Opção 1: Usar Root Directory (Recomendado) ✅

**Já corrigi o railway.json para você!** Agora faça:

### Passos:

1. **Commit e Push** as mudanças do railway.json:
   ```bash
   git add railway.json
   git commit -m "fix: Update railway.json for Root Directory"
   git push
   ```

2. **Na Interface do Railway:**
   - Vá em **Settings** → **Service**
   - Confirme que **Root Directory = backend**
   - O Railway fará redeploy automaticamente

3. **Aguarde o Build**
   - Vá em **Deployments**
   - Acompanhe os logs
   - Deve funcionar agora! ✅

---

## Opção 2: NÃO Usar Root Directory

Se preferir NÃO usar Root Directory:

### Passos:

1. **Na Interface do Railway:**
   - Vá em **Settings** → **Service**
   - Procure **"Root Directory"**
   - **DELETE/CLEAR** o valor (deixe em branco)
   - Clique **"Update"**

2. **Reverter railway.json:**

   Edite `railway.json` para:
   ```json
   {
     "$schema": "https://railway.app/railway.schema.json",
     "build": {
       "builder": "DOCKERFILE",
       "dockerfilePath": "backend/Dockerfile"
     },
     "deploy": {
       "startCommand": "cd backend && daphne -b 0.0.0.0 -p $PORT separacao_pmcell.asgi:application",
       "healthcheckPath": "/",
       "healthcheckTimeout": 100,
       "restartPolicyType": "ON_FAILURE",
       "restartPolicyMaxRetries": 10
     }
   }
   ```

3. **Commit e Push:**
   ```bash
   git add railway.json
   git commit -m "fix: Remove Root Directory from railway.json"
   git push
   ```

---

## Como o Railway Funciona com Root Directory

### Com Root Directory = "backend"

```
Projeto/
├── railway.json (dockerfilePath: "Dockerfile")
└── backend/         ← Railway trabalha AQUI
    ├── Dockerfile   ← Procura Dockerfile AQUI
    ├── manage.py
    └── ...
```

### Sem Root Directory

```
Projeto/
├── railway.json (dockerfilePath: "backend/Dockerfile")
├── backend/
│   ├── Dockerfile   ← Procura Dockerfile AQUI
│   ├── manage.py
│   └── ...
```

---

## ❌ Erro: "DisallowedHost at /"

### Causa

Django não reconhece o host do Railway.

### ✅ Solução

1. Vá em **Variables**
2. Atualize `ALLOWED_HOSTS`:
   ```
   .railway.app,seu-app-production.up.railway.app
   ```
3. Salve (redeploy automático)

---

## ❌ Erro: "CSRF verification failed"

### Causa

Django bloqueou a requisição por segurança CSRF.

### ✅ Solução

1. Vá em **Variables**
2. Atualize `CSRF_TRUSTED_ORIGINS` com a URL COMPLETA:
   ```
   https://seu-app-production.up.railway.app
   ```
   **IMPORTANTE:** Use `https://` no início!
3. Salve (redeploy automático)

---

## ❌ Erro: "relation does not exist" (Database)

### Causa

Migrations não foram executadas.

### ✅ Solução

**Opção A - Via Railway CLI:**
```bash
railway run python manage.py migrate
```

**Opção B - Via Interface Web:**
Se o Railway tiver terminal web:
1. Clique no serviço
2. Procure "Shell" ou "Terminal"
3. Execute: `python manage.py migrate`

---

## ❌ Erro: "ModuleNotFoundError: No module named 'X'"

### Causa

Dependência faltando em requirements.txt.

### ✅ Solução

1. Adicione a dependência em `backend/requirements.txt`:
   ```
   nome-do-pacote>=versao
   ```

2. Commit e push:
   ```bash
   git add backend/requirements.txt
   git commit -m "Add missing dependency"
   git push
   ```

---

## ❌ Erro: Build demora muito / Timeout

### Causa

Build muito lento ou timeout.

### ✅ Solução

1. Verifique se `requirements.txt` não tem pacotes pesados desnecessários
2. Aumente timeout em **Settings** → **Deploy**:
   - Build Timeout: 10+ minutos
   - Healthcheck Timeout: 100+ segundos

---

## ❌ Erro: "WebSocket connection failed"

### Causa

Redis não está configurado ou REDIS_URL incorreto.

### ✅ Solução

1. Verifique se Redis está adicionado:
   - Dashboard → Veja se tem serviço Redis

2. Se não tiver, adicione:
   - **+ New** → **Database** → **Add Redis**

3. Verifique variáveis:
   - Vá em **Variables**
   - Confirme que `REDIS_URL` existe
   - Formato: `redis://host:port/0`

4. Redeploy

---

## ❌ Erro: "Static files not loading" (CSS/JS)

### Causa

Whitenoise não configurado ou collectstatic não executado.

### ✅ Solução

1. Verifique `backend/requirements.txt`:
   ```
   whitenoise>=6.6.0
   ```

2. Verifique `settings.py`:
   ```python
   MIDDLEWARE = [
       'django.middleware.security.SecurityMiddleware',
       'whitenoise.middleware.WhiteNoiseMiddleware',  # Deve estar aqui
       ...
   ]
   ```

3. Force collectstatic via Railway CLI:
   ```bash
   railway run python manage.py collectstatic --noinput
   ```

---

## 🔍 Como Debugar Erros

### 1. Ver Logs de Build

```
Deployments → Último deployment → View Logs → Build
```

Procure por:
- `ERROR:`
- `FAILED`
- `not found`

### 2. Ver Logs de Runtime

```
Deployments → Último deployment → View Logs → Deploy
```

Procure por:
- Python tracebacks
- Django errors
- Connection errors

### 3. Ver Logs em Tempo Real

```
Deployments → Último deployment → View Logs → Enable Auto-scroll
```

### 4. Verificar Variáveis

```
Service → Variables → Verifique se todas estão corretas
```

---

## 📋 Checklist de Verificação

Quando algo der errado, verifique:

- [ ] Root Directory configurado corretamente (ou vazio)
- [ ] railway.json com dockerfilePath correto
- [ ] Dockerfile existe no caminho especificado
- [ ] requirements.txt completo
- [ ] Todas variáveis de ambiente configuradas
- [ ] PostgreSQL e Redis adicionados
- [ ] Migrations executadas
- [ ] ALLOWED_HOSTS e CSRF_TRUSTED_ORIGINS corretos

---

## 🆘 Ainda com Problemas?

### Opções:

1. **Execute o validador:**
   ```bash
   python3 check_deploy_ready.py
   ```

2. **Consulte os logs:**
   - Deployments → View Logs
   - Procure pelo erro específico

3. **Railway Docs:**
   - https://docs.railway.app

4. **Railway Discord:**
   - https://discord.gg/railway
   - Canal #help

5. **Me chame de volta:**
   - Copie o erro completo dos logs
   - Me mostre

---

## 📝 Comandos Úteis para Debug

### Verificar Configuração

```bash
# Ver todas as variáveis
railway variables

# Ver status do serviço
railway status

# Ver logs
railway logs

# Ver logs de build
railway logs --build
```

### Executar Comandos

```bash
# Django check
railway run python manage.py check

# Ver migrations
railway run python manage.py showmigrations

# Django shell
railway run python manage.py shell

# Collectstatic
railway run python manage.py collectstatic --noinput
```

---

**Última atualização**: 03/11/2025
**Baseado em**: Erros reais durante deploy
