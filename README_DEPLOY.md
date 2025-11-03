# Deploy no Railway - Sumário Executivo

## Status: ✅ PRONTO PARA DEPLOY

Seu projeto passou em todas as validações e está pronto para ser deployed no Railway!

---

## Arquivos Criados

Foram criados os seguintes arquivos para facilitar o deploy:

1. **railway.json** - Configuração do Railway (raiz do projeto)
2. **RAILWAY_DEPLOY_GUIDE.md** - Guia completo e detalhado
3. **DEPLOY_QUICKSTART.md** - Guia rápido com comandos essenciais
4. **deploy_railway.sh** - Script automatizado de deploy
5. **check_deploy_ready.py** - Script de validação pré-deploy
6. **README_DEPLOY.md** - Este arquivo (resumo executivo)

---

## Início Rápido (3 minutos)

### Opção 1: Deploy Automatizado (Recomendado)

```bash
./deploy_railway.sh
```

### Opção 2: Deploy Manual

```bash
# 1. Instalar e fazer login
npm install -g @railway/cli
railway login

# 2. Criar projeto
railway init

# 3. Adicionar serviços
railway add --database postgres
railway add --database redis

# 4. Configurar variáveis
python3 -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
railway variables --set "SECRET_KEY=<chave-gerada-acima>"
railway variables --set "DEBUG=False"
railway variables --set "ALLOWED_HOSTS=.railway.app"

# 5. Deploy
railway up

# 6. Migrações
railway run python manage.py migrate

# 7. Obter URL e configurar CSRF
railway open
railway variables --set "CSRF_TRUSTED_ORIGINS=https://seu-app.up.railway.app"
railway up
```

---

## Variáveis de Ambiente

### Você Precisa Configurar:

| Variável | Como Obter | Quando |
|----------|------------|--------|
| `SECRET_KEY` | `python3 -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"` | Antes do deploy |
| `DEBUG` | `False` | Antes do deploy |
| `ALLOWED_HOSTS` | `.railway.app` | Antes do deploy |
| `CSRF_TRUSTED_ORIGINS` | `https://seu-app.up.railway.app` | Após primeiro deploy |

### Railway Configura Automaticamente:

- `DATABASE_URL` (PostgreSQL)
- `REDIS_URL` (Redis)
- `PORT` (porta do servidor)

---

## Serviços Necessários

Seu app precisa de 3 serviços no Railway:

1. **Web Service** (Django com Daphne)
2. **PostgreSQL** (banco de dados)
3. **Redis** (cache + WebSockets)

---

## Checklist

- [ ] Railway CLI instalado
- [ ] Login feito no Railway
- [ ] Projeto criado/vinculado
- [ ] PostgreSQL adicionado
- [ ] Redis adicionado
- [ ] SECRET_KEY configurada
- [ ] ALLOWED_HOSTS configurada
- [ ] Deploy inicial feito
- [ ] Migrations executadas
- [ ] URL do app obtida
- [ ] CSRF_TRUSTED_ORIGINS configurada
- [ ] Redeploy feito
- [ ] App testado e funcionando

---

## Comandos Úteis

```bash
# Ver logs
railway logs

# Ver status
railway status

# Abrir app
railway open

# Ver variáveis
railway variables

# Executar comando
railway run <comando>

# Shell
railway shell
```

---

## Estrutura do Projeto

```
orcamentos-modelo/
├── railway.json                  ← Config Railway
├── deploy_railway.sh             ← Deploy automatizado
├── check_deploy_ready.py         ← Validação pré-deploy
├── RAILWAY_DEPLOY_GUIDE.md       ← Guia completo
├── DEPLOY_QUICKSTART.md          ← Guia rápido
├── README_DEPLOY.md              ← Este arquivo
│
└── backend/
    ├── Dockerfile                ← Build Docker
    ├── .env.example              ← Template variáveis
    ├── requirements.txt          ← Dependências
    ├── manage.py                 ← Django CLI
    ├── separacao_pmcell/
    │   ├── settings.py           ← Configuração Django
    │   ├── asgi.py               ← ASGI app (WebSockets)
    │   └── ...
    ├── core/                     ← App principal
    ├── static/                   ← Arquivos estáticos
    └── templates/                ← Templates HTML
```

---

## Tecnologias Usadas

- **Backend**: Django 4.2+ com Channels (WebSockets)
- **Servidor**: Daphne (ASGI)
- **Banco de Dados**: PostgreSQL
- **Cache/WebSockets**: Redis
- **Static Files**: Whitenoise
- **Deploy**: Railway + Docker

---

## Custos Estimados (Railway)

- **Free Plan**: $5 crédito/mês
  - Bom para: desenvolvimento, testes, demos
  - Limite: ~500 horas/mês

- **Pro Plan**: $20/mês + uso adicional
  - Bom para: produção, apps comerciais
  - Sem limite de horas

**Dica**: Comece com Free Plan e monitore o uso no dashboard.

---

## Troubleshooting

### Problema: DisallowedHost
**Solução**:
```bash
railway variables --set "ALLOWED_HOSTS=.railway.app,seu-dominio.com"
railway up
```

### Problema: CSRF verification failed
**Solução**:
```bash
railway variables --set "CSRF_TRUSTED_ORIGINS=https://seu-app.up.railway.app"
railway up
```

### Problema: WebSockets não funcionam
**Solução**:
```bash
# Verificar se Redis está funcionando
railway run redis-cli ping
# Deve retornar: PONG
```

### Problema: Migrations não executadas
**Solução**:
```bash
railway run python manage.py migrate
railway run python manage.py showmigrations
```

### Problema: Static files não carregam
**Solução**:
```bash
railway run python manage.py collectstatic --noinput
```

---

## Links Importantes

- **Railway Dashboard**: https://railway.app/dashboard
- **Railway Docs**: https://docs.railway.app
- **Railway Discord**: https://discord.gg/railway

---

## Suporte

Se encontrar problemas:

1. Execute: `python3 check_deploy_ready.py`
2. Veja os logs: `railway logs`
3. Consulte: `RAILWAY_DEPLOY_GUIDE.md`
4. Verifique: https://docs.railway.app

---

## Próximos Passos Após Deploy

1. [ ] Testar todas as funcionalidades do app
2. [ ] Criar superusuário: `railway run python manage.py createsuperuser`
3. [ ] Configurar domínio customizado (opcional)
4. [ ] Configurar backups do PostgreSQL
5. [ ] Adicionar monitoramento/alertas
6. [ ] Configurar CI/CD (GitHub Actions)
7. [ ] Documentar URLs e credenciais

---

**Última atualização**: 03/11/2025
**Versão**: 1.0
**Status**: Validado e pronto para deploy
