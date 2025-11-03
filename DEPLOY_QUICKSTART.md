# Deploy Railway - Início Rápido

## Opção 1: Deploy Automatizado (Recomendado)

```bash
./deploy_railway.sh
```

O script fará tudo automaticamente!

---

## Opção 2: Deploy Manual (Passo a Passo)

### 1. Instalar Railway CLI

```bash
npm install -g @railway/cli
```

### 2. Login

```bash
railway login
```

### 3. Criar/Vincular Projeto

```bash
# Novo projeto
railway init

# OU vincular existente
railway link
```

### 4. Adicionar Bancos de Dados

```bash
# PostgreSQL
railway add --database postgres

# Redis
railway add --database redis
```

### 5. Configurar Variáveis de Ambiente

```bash
# Gerar SECRET_KEY
python3 -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"

# Configurar variáveis (substitua os valores!)
railway variables --set "SECRET_KEY=sua-chave-gerada-acima"
railway variables --set "DEBUG=False"
railway variables --set "ALLOWED_HOSTS=.railway.app"
```

### 6. Deploy

```bash
railway up
```

### 7. Migrações

```bash
railway run python manage.py migrate
railway run python manage.py createsuperuser
```

### 8. Configurar CSRF (APÓS obter URL)

```bash
# Obter URL do app
railway open

# Configurar CSRF com a URL obtida
railway variables --set "CSRF_TRUSTED_ORIGINS=https://seu-app.up.railway.app"

# Fazer redeploy
railway up
```

---

## Variáveis de Ambiente Necessárias

| Variável | Valor | Criada Por |
|----------|-------|------------|
| `SECRET_KEY` | Chave Django secreta | Você |
| `DEBUG` | False | Você |
| `ALLOWED_HOSTS` | .railway.app | Você |
| `CSRF_TRUSTED_ORIGINS` | https://seu-app.up.railway.app | Você (após deploy) |
| `DATABASE_URL` | postgresql://... | Railway (automático) |
| `REDIS_URL` | redis://... | Railway (automático) |
| `PORT` | 8000 (ou dinâmico) | Railway (automático) |

---

## Comandos Úteis

```bash
# Ver logs em tempo real
railway logs

# Ver status
railway status

# Abrir app no navegador
railway open

# Ver variáveis
railway variables

# Executar comando no servidor
railway run <comando>

# Shell interativo
railway shell
```

---

## Estrutura de Arquivos Configurados

```
orcamentos-modelo/
├── railway.json          ← Configuração Railway (raiz)
├── backend/
│   ├── Dockerfile        ← Build Docker
│   ├── .env.example      ← Template de variáveis
│   ├── requirements.txt  ← Dependências Python
│   └── ...
└── RAILWAY_DEPLOY_GUIDE.md  ← Guia completo
```

---

## Troubleshooting Rápido

### App não abre?
```bash
railway logs  # Ver erros
```

### DisallowedHost?
```bash
railway variables --set "ALLOWED_HOSTS=.railway.app,seu-dominio.com"
```

### CSRF error?
```bash
railway variables --set "CSRF_TRUSTED_ORIGINS=https://seu-app.up.railway.app"
railway up  # Redeploy
```

### Migrations não rodaram?
```bash
railway run python manage.py migrate
```

---

## Checklist Rápido

- [ ] Railway CLI instalado
- [ ] Login feito
- [ ] Projeto criado/vinculado
- [ ] PostgreSQL adicionado
- [ ] Redis adicionado
- [ ] SECRET_KEY configurada
- [ ] ALLOWED_HOSTS configurada
- [ ] Deploy feito (`railway up`)
- [ ] Migrations executadas
- [ ] URL obtida
- [ ] CSRF_TRUSTED_ORIGINS configurada
- [ ] Redeploy feito
- [ ] App testado

---

## Links Importantes

- **Dashboard Railway**: https://railway.app/dashboard
- **Documentação**: https://docs.railway.app
- **Seu Projeto**: Veja com `railway status`
- **Abrir App**: `railway open`

---

Para mais detalhes, veja `RAILWAY_DEPLOY_GUIDE.md`
