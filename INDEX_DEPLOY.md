# Índice Completo - Deploy Railway

## Arquivos Criados/Atualizados

### Arquivos Principais (Novos)

1. **railway.json** (raiz)
   - Configuração principal do Railway
   - Define builder, Dockerfile path e start command

2. **backend/Dockerfile** (atualizado)
   - Build otimizado para Railway
   - Suporte a PostgreSQL e variável $PORT

### Documentação Completa

3. **README_DEPLOY.md** ⭐ **COMECE AQUI**
   - Sumário executivo
   - Visão geral completa
   - Checklist de deploy

4. **DEPLOY_WEB_SIMPLES.md** ⭐ **DEPLOY VIA WEB (10 MIN)**
   - Guia super simplificado
   - Deploy via interface web (sem CLI)
   - Passo a passo visual

5. **DEPLOY_WEB_RAILWAY.md**
   - Guia completo via web
   - Deploy sem instalar nada
   - Todas as configurações detalhadas

6. **DEPLOY_QUICKSTART.md**
   - Guia rápido via CLI
   - Comandos essenciais
   - Troubleshooting rápido

7. **RAILWAY_DEPLOY_GUIDE.md**
   - Guia detalhado via CLI
   - Explicação de cada comando
   - Solução de problemas completa

8. **ARCHITECTURE.md**
   - Diagramas de arquitetura
   - Explicação técnica detalhada
   - Fluxo de requests
   - Security e networking

### Scripts Automatizados

7. **deploy_railway.sh** ⭐ **DEPLOY AUTOMATIZADO**
   - Script completo de deploy
   - Valida tudo automaticamente
   - Configuração interativa

8. **check_deploy_ready.py**
   - Validação pré-deploy
   - Verifica todos os requisitos
   - Output colorido e claro

---

## Como Usar Este Projeto

### Opção 1: Deploy via Web (SEM CLI) ⭐ RECOMENDADO

```
Siga: DEPLOY_WEB_SIMPLES.md
Tempo: 10 minutos
Requisitos: Apenas conta Railway + GitHub
```

### Opção 2: Deploy Automatizado (CLI)

```bash
# Passo 1: Validar ambiente
python3 check_deploy_ready.py

# Passo 2: Deploy automatizado
./deploy_railway.sh

# Passo 3: Acessar app
railway open
```

### Opção 3: Deploy Manual (CLI)

Siga o guia: **DEPLOY_QUICKSTART.md**

### Opção 4: Estudo Detalhado

Leia nesta ordem:
1. README_DEPLOY.md (overview)
2. DEPLOY_WEB_SIMPLES.md (web deploy)
3. ARCHITECTURE.md (arquitetura)
4. RAILWAY_DEPLOY_GUIDE.md (detalhes CLI)

---

## Estrutura de Documentação

```
INDEX_DEPLOY.md (você está aqui)
    │
    ├─► README_DEPLOY.md ⭐ (overview geral)
    │   ├─ Sumário executivo
    │   ├─ Checklist completo
    │   └─ Links para outros docs
    │
    ├─► DEPLOY_WEB_SIMPLES.md ⭐ (guia web rápido - 10 min)
    │   ├─ Deploy via interface web
    │   ├─ Sem instalar nada
    │   └─ Passo a passo visual
    │
    ├─► DEPLOY_WEB_RAILWAY.md (guia web completo)
    │   ├─ Deploy detalhado via web
    │   ├─ Todas as configurações
    │   └─ Troubleshooting completo
    │
    ├─► DEPLOY_QUICKSTART.md (guia CLI rápido)
    │   ├─ Comandos principais
    │   ├─ Variáveis necessárias
    │   └─ Troubleshooting básico
    │
    ├─► RAILWAY_DEPLOY_GUIDE.md (guia CLI detalhado)
    │   ├─ Passo a passo completo
    │   ├─ Explicação de cada etapa
    │   └─ Solução de problemas
    │
    └─► ARCHITECTURE.md (arquitetura técnica)
        ├─ Diagramas do sistema
        ├─ Fluxo de dados
        ├─ Security & networking
        └─ Scaling & performance
```

---

## Fluxo Recomendado de Deploy

### Fase 1: Preparação (5 minutos)

```bash
# 1. Validar projeto
python3 check_deploy_ready.py

# 2. Instalar Railway CLI (se necessário)
npm install -g @railway/cli

# 3. Fazer login
railway login
```

### Fase 2: Setup (5 minutos)

Opção A - Automatizado:
```bash
./deploy_railway.sh
```

Opção B - Manual:
```bash
railway init
railway add --database postgres
railway add --database redis
```

### Fase 3: Configuração (5 minutos)

```bash
# Gerar SECRET_KEY
python3 -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"

# Configurar variáveis
railway variables --set "SECRET_KEY=<chave-gerada>"
railway variables --set "DEBUG=False"
railway variables --set "ALLOWED_HOSTS=.railway.app"
```

### Fase 4: Deploy (10 minutos)

```bash
# Fazer deploy
railway up

# Ver logs
railway logs

# Executar migrations
railway run python manage.py migrate
```

### Fase 5: Finalização (5 minutos)

```bash
# Obter URL
railway open

# Configurar CSRF
railway variables --set "CSRF_TRUSTED_ORIGINS=https://seu-app.up.railway.app"

# Redeploy
railway up

# Criar superusuário (opcional)
railway run python manage.py createsuperuser
```

**Tempo Total: ~30 minutos**

---

## Comandos Rápidos de Referência

### Deploy & Build

```bash
railway up                          # Deploy
railway up --detach                 # Deploy em background
railway logs                        # Ver logs
railway logs -f                     # Follow logs
railway status                      # Ver status
```

### Variáveis de Ambiente

```bash
railway variables                   # Listar todas
railway variables --set "KEY=VAL"   # Definir
railway variables --unset KEY       # Remover
```

### Database

```bash
railway run python manage.py migrate           # Migrations
railway run python manage.py createsuperuser   # Criar admin
railway run python manage.py shell             # Django shell
railway run psql $DATABASE_URL                 # PostgreSQL shell
railway run redis-cli                          # Redis CLI
```

### Management

```bash
railway open                        # Abrir app no browser
railway link                        # Vincular projeto
railway unlink                      # Desvincular
railway projects                    # Listar projetos
railway service                     # Info do serviço
```

---

## Variáveis de Ambiente - Referência Rápida

| Variável | Valor | Quem Define |
|----------|-------|-------------|
| `SECRET_KEY` | String aleatória Django | Você |
| `DEBUG` | `False` | Você |
| `ALLOWED_HOSTS` | `.railway.app` | Você |
| `CSRF_TRUSTED_ORIGINS` | `https://seu-app.up.railway.app` | Você |
| `DATABASE_URL` | `postgresql://...` | Railway |
| `REDIS_URL` | `redis://...` | Railway |
| `PORT` | `8000` ou dinâmica | Railway |

---

## Checklist Rápido

### Pré-Deploy
- [ ] Python 3.11+ instalado
- [ ] Node.js instalado (para Railway CLI)
- [ ] Conta Railway criada
- [ ] Projeto validado (`python3 check_deploy_ready.py`)

### Durante Deploy
- [ ] Railway CLI instalada
- [ ] Login realizado
- [ ] Projeto criado/vinculado
- [ ] PostgreSQL adicionado
- [ ] Redis adicionado
- [ ] Variáveis configuradas (SECRET_KEY, DEBUG, ALLOWED_HOSTS)
- [ ] Deploy realizado
- [ ] Logs verificados (sem erros)

### Pós-Deploy
- [ ] Migrations executadas
- [ ] URL do app obtida
- [ ] CSRF_TRUSTED_ORIGINS configurado
- [ ] Redeploy realizado
- [ ] App testado no navegador
- [ ] Superusuário criado (opcional)
- [ ] Funcionalidades testadas

---

## Troubleshooting Rápido

### DisallowedHost
```bash
railway variables --set "ALLOWED_HOSTS=.railway.app,outro-dominio.com"
railway up
```

### CSRF Error
```bash
railway variables --set "CSRF_TRUSTED_ORIGINS=https://seu-app.up.railway.app"
railway up
```

### Build Failed
```bash
railway logs --build  # Ver logs do build
# Verificar Dockerfile e requirements.txt
```

### App Crashed
```bash
railway logs  # Ver logs de erro
railway run python manage.py check  # Verificar configuração
```

### Migrations Não Executadas
```bash
railway run python manage.py migrate
railway run python manage.py showmigrations
```

---

## Links Úteis

### Railway
- Dashboard: https://railway.app/dashboard
- Docs: https://docs.railway.app
- Discord: https://discord.gg/railway
- Status: https://status.railway.app

### Django
- Docs: https://docs.djangoproject.com
- Deployment Checklist: https://docs.djangoproject.com/en/4.2/howto/deployment/checklist/

### PostgreSQL
- Docs: https://www.postgresql.org/docs/

### Redis
- Docs: https://redis.io/docs/

---

## Suporte

### Ordem de Troubleshooting

1. Execute `python3 check_deploy_ready.py`
2. Verifique `railway logs`
3. Consulte **RAILWAY_DEPLOY_GUIDE.md**
4. Leia **ARCHITECTURE.md** (entenda o sistema)
5. Pesquise em https://docs.railway.app
6. Pergunte no Discord do Railway

---

## Manutenção e Updates

### Deploy de Novas Versões

```bash
# 1. Fazer mudanças no código
# 2. Commit (opcional, se usando Git)
git add .
git commit -m "Nova feature"

# 3. Deploy
railway up

# 4. Ver logs
railway logs -f
```

### Rollback

```bash
# Via dashboard: Railway Dashboard > Deployments > Previous > Rollback

# Via CLI: não tem comando direto, mas pode redeployar commit anterior
railway up --service web
```

### Backups

```bash
# PostgreSQL
railway run pg_dump $DATABASE_URL > backup-$(date +%Y%m%d).sql

# Restaurar
railway run psql $DATABASE_URL < backup-20251103.sql
```

---

## Custos Estimados

### Free Tier
- **$5/mês de crédito**
- ~500 horas de execução
- Bom para: dev, testes, demos, projetos pessoais

### Pro Tier
- **$20/mês + uso**
- Ilimitado
- Bom para: produção, apps comerciais
- Inclui: backups, monitoring, suporte

### Calculadora
Use: https://railway.app/pricing

---

## Próximos Passos

Após deploy bem-sucedido:

1. [ ] Configurar domínio customizado
2. [ ] Configurar monitoramento
3. [ ] Configurar alertas de erro
4. [ ] Implementar CI/CD
5. [ ] Adicionar testes automatizados
6. [ ] Configurar staging environment
7. [ ] Documentar credenciais
8. [ ] Treinar equipe

---

## Informações do Projeto

- **Nome**: Separação PMCELL
- **Tipo**: Web App Django com WebSockets
- **Stack**: Django 4.2+, PostgreSQL, Redis, Daphne
- **Deploy**: Railway.app
- **Documentação**: Completa e atualizada
- **Scripts**: Automatizados e testados
- **Status**: ✅ Pronto para produção

---

**Última atualização**: 03/11/2025
**Versão dos Scripts**: 1.0
**Status**: Testado e validado

**Criado por**: Claude Code
**Validado**: ✅ check_deploy_ready.py passou em todos os testes
