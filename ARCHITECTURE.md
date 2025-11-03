# Arquitetura do Deploy no Railway

## Visão Geral

```
┌─────────────────────────────────────────────────────────────────┐
│                        RAILWAY PROJECT                          │
│                     (separacao-pmcell)                          │
└─────────────────────────────────────────────────────────────────┘
                                │
        ┌───────────────────────┼───────────────────────┐
        │                       │                       │
        ▼                       ▼                       ▼
┌───────────────┐      ┌────────────────┐      ┌──────────────┐
│  WEB SERVICE  │      │   POSTGRESQL   │      │    REDIS     │
│               │      │                │      │              │
│  Django +     │◄────►│   DATABASE     │      │  Cache +     │
│  Daphne       │      │                │      │  WebSockets  │
│  (Port $PORT) │◄────►│                │      │              │
│               │      └────────────────┘      └──────────────┘
└───────────────┘              │                       │
        │                      │                       │
        │              ┌───────┴──────────────────────┘
        │              │
        ▼              ▼
┌─────────────────────────────────────┐
│     VARIÁVEIS DE AMBIENTE           │
│                                     │
│  DATABASE_URL  (auto)               │
│  REDIS_URL     (auto)               │
│  PORT          (auto)               │
│  SECRET_KEY    (você configura)     │
│  DEBUG         (você configura)     │
│  ALLOWED_HOSTS (você configura)     │
│  CSRF_TRUSTED_ORIGINS (você config) │
└─────────────────────────────────────┘
```

---

## Componentes Detalhados

### 1. Web Service (Django Application)

**Tecnologia**: Django 4.2+ com Django Channels

**Servidor**: Daphne (ASGI Server)

**Responsabilidades**:
- Servir aplicação web
- APIs REST
- WebSockets (para atualizações em tempo real)
- Servir arquivos estáticos (via Whitenoise)

**Build**:
```dockerfile
FROM python:3.11-slim
WORKDIR /app
# Instalar dependências PostgreSQL
# Instalar requirements.txt
# Copiar código
# Collectstatic
# Rodar Daphne
```

**Comando de Start**:
```bash
daphne -b 0.0.0.0 -p $PORT separacao_pmcell.asgi:application
```

**Porta**: Dinâmica (Railway define via `$PORT`)

**Healthcheck**: `GET /` (timeout: 100s)

---

### 2. PostgreSQL Database

**Versão**: PostgreSQL 14+

**Responsabilidades**:
- Armazenar dados da aplicação
- Usuários, pedidos, produtos, etc.
- Relações e constraints

**Conexão**:
```
DATABASE_URL=postgresql://user:pass@host:port/db
```

**Railway fornece automaticamente**:
- Host
- Port
- User
- Password
- Database name

**Backups**: Gerenciados pelo Railway

---

### 3. Redis Database

**Versão**: Redis 7+

**Responsabilidades**:
- Cache da aplicação (Django Cache Framework)
- Channel Layer (Django Channels - WebSockets)
- Sessões (opcional)

**Conexão**:
```
REDIS_URL=redis://host:port/0
```

**Uso no Código**:
```python
# Cache
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': REDIS_URL,
    }
}

# Channel Layer (WebSockets)
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            "hosts": [(redis_host, redis_port)],
        },
    },
}
```

---

## Fluxo de Request

### Request HTTP Normal

```
User Browser
    │
    │ HTTPS
    ▼
Railway Load Balancer
    │
    │ HTTP
    ▼
Django/Daphne (Port $PORT)
    │
    ├─► Django Views/URLs
    │       │
    │       ├─► PostgreSQL (queries)
    │       │
    │       └─► Redis (cache)
    │
    └─► Response (HTML/JSON)
```

### WebSocket Connection

```
User Browser
    │
    │ WSS (WebSocket Secure)
    ▼
Railway Load Balancer
    │
    │ WS
    ▼
Daphne ASGI Server
    │
    ▼
Django Channels Consumer
    │
    ├─► Redis Channel Layer
    │   (pub/sub for real-time)
    │
    └─► PostgreSQL
        (persist messages/data)
```

---

## Variáveis de Ambiente

### Automáticas (Railway)

Railway cria e gerencia automaticamente:

| Variável | Origem | Formato |
|----------|--------|---------|
| `DATABASE_URL` | PostgreSQL Service | `postgresql://user:pass@host:port/db` |
| `REDIS_URL` | Redis Service | `redis://host:port/0` |
| `PORT` | Railway Platform | `8000` (ou outro) |
| `RAILWAY_ENVIRONMENT` | Railway Platform | `production` |
| `RAILWAY_SERVICE_NAME` | Railway Platform | `web` |

### Manuais (Você Configura)

Você precisa configurar via Railway dashboard ou CLI:

| Variável | Valor Exemplo | Propósito |
|----------|---------------|-----------|
| `SECRET_KEY` | `django-insecure-abc123...` | Criptografia Django |
| `DEBUG` | `False` | Modo de produção |
| `ALLOWED_HOSTS` | `.railway.app` | Hosts permitidos |
| `CSRF_TRUSTED_ORIGINS` | `https://app.railway.app` | Proteção CSRF |

---

## Processo de Deploy

### Build Phase

```
1. Railway recebe o código (git push ou railway up)
2. Detecta railway.json
3. Usa builder: DOCKERFILE
4. Localiza backend/Dockerfile
5. Executa docker build:
   ├─ Instala Python 3.11
   ├─ Instala dependências do sistema (gcc, libpq)
   ├─ Instala requirements.txt (pip)
   ├─ Copia código para /app
   ├─ Executa collectstatic
   └─ Define CMD
6. Cria imagem Docker
7. Publica imagem no registry Railway
```

### Deploy Phase

```
1. Railway cria container da imagem
2. Injeta variáveis de ambiente:
   - DATABASE_URL (do PostgreSQL)
   - REDIS_URL (do Redis)
   - PORT (dinâmico)
   - Suas variáveis customizadas
3. Executa startCommand:
   cd backend && daphne -b 0.0.0.0 -p $PORT separacao_pmcell.asgi:application
4. Aguarda healthcheck: GET /
5. Se OK (200): deployment success
6. Se FAIL: rollback automático
7. Roteia tráfego para novo container
```

---

## Network & Security

### Networking

```
┌─────────────────────────────────────────────────────┐
│                    INTERNET                         │
└────────────────────┬────────────────────────────────┘
                     │ HTTPS (443)
                     ▼
┌─────────────────────────────────────────────────────┐
│           Railway Load Balancer + CDN               │
│         (Automatic SSL/TLS Certificate)             │
└────────────────────┬────────────────────────────────┘
                     │ HTTP (internal)
                     ▼
┌─────────────────────────────────────────────────────┐
│              Your Web Service Container             │
│            (Private Railway Network)                │
│                                                     │
│   ┌──────────────┐     ┌────────────────────────┐  │
│   │  Daphne      │────►│  PostgreSQL (Private)  │  │
│   │  Port: $PORT │     │  Internal DNS          │  │
│   └──────────────┘     └────────────────────────┘  │
│          │                                          │
│          │             ┌────────────────────────┐  │
│          └────────────►│  Redis (Private)       │  │
│                        │  Internal DNS          │  │
│                        └────────────────────────┘  │
└─────────────────────────────────────────────────────┘
```

### Security Features

1. **SSL/TLS**: Automático para `*.railway.app`
2. **Private Networking**: DB e Redis não expostos publicamente
3. **Environment Variables**: Criptografadas em rest
4. **Django Security**:
   - CSRF Protection
   - XSS Protection
   - SQL Injection Protection (ORM)
   - Secure cookies
   - HTTPS redirect

---

## Scaling & Performance

### Horizontal Scaling

Railway permite escalar horizontalmente:

```
┌─────────────────┐
│  Load Balancer  │
└────────┬────────┘
         │
    ┌────┼────┬────────┐
    │    │    │        │
    ▼    ▼    ▼        ▼
┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐
│Web 1│ │Web 2│ │Web 3│ │Web N│
└──┬──┘ └──┬──┘ └──┬──┘ └──┬──┘
   │       │       │       │
   └───────┴───┬───┴───────┘
               │
        ┌──────┴──────┐
        │             │
        ▼             ▼
   ┌────────┐    ┌────────┐
   │  PG DB │    │  Redis │
   └────────┘    └────────┘
```

### Resource Limits

**Free Plan**:
- CPU: Shared
- RAM: 512 MB
- Storage: 1 GB

**Pro Plan**:
- CPU: 8 vCPU
- RAM: 8 GB
- Storage: 100 GB

---

## Monitoring & Logs

### Available Logs

```bash
# Application logs
railway logs

# Deploy logs
railway logs --deployment

# Build logs
railway logs --build

# Follow logs
railway logs -f
```

### Metrics Dashboard

Railway fornece:
- CPU usage
- Memory usage
- Network I/O
- Request rate
- Error rate
- Build time
- Deploy time

---

## Backup & Disaster Recovery

### Database Backups

PostgreSQL no Railway:
- Backups automáticos diários
- Retenção: 7 dias (Free), 30 dias (Pro)
- Point-in-time recovery (Pro)

### Manual Backup

```bash
# Exportar banco
railway run pg_dump $DATABASE_URL > backup.sql

# Restaurar banco
railway run psql $DATABASE_URL < backup.sql
```

### Redis Persistence

Redis no Railway:
- RDB snapshots
- AOF (Append Only File)
- Auto-recovery

---

## Cost Optimization

### Free Tier Strategy

```
Uso Estimado (Free $5/mês):

Web Service:  $3.00/mês  (500h × $0.006/h)
PostgreSQL:   $1.50/mês  (100 MB storage)
Redis:        $0.50/mês  (50 MB storage)
──────────────────────────────────────────
TOTAL:        $5.00/mês  ✅ Dentro do free
```

### Production Strategy

```
Uso Estimado (Pro $20/mês + uso):

Base:         $20.00/mês  (Pro plan)
Web Service:  $10.00/mês  (scaled instances)
PostgreSQL:   $5.00/mês   (5 GB storage)
Redis:        $2.00/mês   (500 MB storage)
──────────────────────────────────────────
TOTAL:        $37.00/mês
```

---

## CI/CD Pipeline (Opcional)

### GitHub Actions Integration

```yaml
# .github/workflows/deploy.yml
name: Deploy to Railway

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Install Railway
        run: npm i -g @railway/cli
      - name: Deploy
        run: railway up
        env:
          RAILWAY_TOKEN: ${{ secrets.RAILWAY_TOKEN }}
```

---

## Conclusão

Este é um setup de produção completo e escalável, com:

- ✅ Build automatizado com Docker
- ✅ Deploy zero-downtime
- ✅ SSL/TLS automático
- ✅ Backups automáticos
- ✅ Monitoring integrado
- ✅ WebSockets support
- ✅ Horizontal scaling ready

Pronto para produção! 🚀
