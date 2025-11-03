# Guia Completo de Deploy no Railway

## Pré-requisitos

- Conta no Railway (https://railway.app)
- Railway CLI instalado: `npm install -g @railway/cli`
- Git instalado e projeto em repositório

## Passo 1: Login no Railway

```bash
railway login
```

Isso abrirá o navegador para autenticação.

## Passo 2: Inicializar Projeto

Na raiz do projeto (`/Users/nycolasmancini/Desktop/separacao-pmcell/orcamentos-modelo`):

```bash
# Criar novo projeto
railway init

# OU vincular a um projeto existente
railway link
```

## Passo 3: Adicionar Serviços Necessários

### 3.1 Adicionar PostgreSQL

```bash
railway add --database postgres
```

Isso criará automaticamente a variável `DATABASE_URL`.

### 3.2 Adicionar Redis

```bash
railway add --database redis
```

Isso criará automaticamente a variável `REDIS_URL`.

## Passo 4: Configurar Variáveis de Ambiente

Configure no dashboard do Railway (https://railway.app/project/SEU_PROJETO/variables):

### Variáveis Obrigatórias:

```bash
SECRET_KEY=seu-secret-key-seguro-aqui
DEBUG=False
ALLOWED_HOSTS=.railway.app
CSRF_TRUSTED_ORIGINS=https://seu-app.up.railway.app
```

### Como gerar SECRET_KEY:

```bash
# Execute localmente para gerar uma chave segura:
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

### Variáveis Opcionais (já têm defaults):

```bash
LANGUAGE_CODE=pt-br
TIME_ZONE=America/Sao_Paulo
SESSION_COOKIE_AGE=28800
CACHE_TIMEOUT=300
```

### Variáveis Automáticas (Railway cria automaticamente):

- `DATABASE_URL` - Criada ao adicionar PostgreSQL
- `REDIS_URL` - Criada ao adicionar Redis
- `PORT` - Railway define automaticamente

## Passo 5: Configurar Root Directory

No dashboard do Railway, vá em Settings > Build e defina:

```
Root Directory: backend
```

Ou use o arquivo `railway.json` (já configurado na raiz do projeto).

## Passo 6: Deploy

```bash
# Deploy via CLI
railway up

# OU faça commit e push para o repositório Git vinculado
git add .
git commit -m "Configure Railway deployment"
git push
```

## Passo 7: Executar Migrações

Após o primeiro deploy, execute:

```bash
# Via Railway CLI
railway run python manage.py migrate

# Criar superusuário (opcional)
railway run python manage.py createsuperuser
```

## Passo 8: Verificar Logs

```bash
# Ver logs em tempo real
railway logs

# Ou no dashboard: https://railway.app/project/SEU_PROJETO/deployments
```

## Comandos Úteis

```bash
# Ver status do projeto
railway status

# Abrir o app no navegador
railway open

# Executar comandos no ambiente Railway
railway run python manage.py <comando>

# Ver variáveis de ambiente
railway variables

# Conectar ao shell do Railway
railway shell
```

## Estrutura de Serviços no Railway

Seu projeto terá 3 serviços:

1. **Web Service** (Django + Daphne)
   - Porta: $PORT (automática)
   - Comando: `daphne -b 0.0.0.0 -p $PORT separacao_pmcell.asgi:application`

2. **PostgreSQL Database**
   - Fornece: `DATABASE_URL`
   - Formato: `postgresql://user:password@host:port/database`

3. **Redis Database**
   - Fornece: `REDIS_URL`
   - Formato: `redis://host:port/0`

## Checklist de Deploy

- [ ] Railway CLI instalado e autenticado
- [ ] Projeto inicializado no Railway
- [ ] PostgreSQL adicionado
- [ ] Redis adicionado
- [ ] SECRET_KEY configurada
- [ ] ALLOWED_HOSTS configurada
- [ ] CSRF_TRUSTED_ORIGINS configurada
- [ ] Root Directory = backend (em Settings ou railway.json)
- [ ] Deploy realizado (`railway up` ou git push)
- [ ] Migrações executadas (`railway run python manage.py migrate`)
- [ ] Logs verificados (sem erros)
- [ ] App testado no navegador

## Solução de Problemas

### Erro: "DisallowedHost"
- Adicione o domínio do Railway em `ALLOWED_HOSTS`
- Exemplo: `ALLOWED_HOSTS=.railway.app,seu-app.up.railway.app`

### Erro: "CSRF verification failed"
- Configure `CSRF_TRUSTED_ORIGINS=https://seu-app.up.railway.app`

### Erro de conexão ao PostgreSQL
- Verifique se `DATABASE_URL` existe nas variáveis
- Execute: `railway variables` para conferir

### Erro de conexão ao Redis
- Verifique se `REDIS_URL` existe nas variáveis
- WebSockets podem não funcionar sem Redis

### Arquivos estáticos não carregam
- Execute: `railway run python manage.py collectstatic --noinput`
- Verifique se `whitenoise` está em `requirements.txt`

### App não inicia
- Verifique logs: `railway logs`
- Confirme que `PORT` está sendo usado corretamente no Dockerfile

## URLs do Projeto

Após deploy, seu app estará disponível em:

```
https://seu-app.up.railway.app
```

Dashboard do Railway:
```
https://railway.app/project/SEU_PROJETO_ID
```

## Próximos Passos

1. Configurar domínio customizado (opcional)
2. Configurar backups do PostgreSQL
3. Monitorar uso de recursos
4. Configurar alertas de erro
5. Adicionar CI/CD (GitHub Actions)

## Custos

Railway oferece:
- **Free Plan**: $5 de crédito/mês (bom para testes)
- **Pro Plan**: $20/mês + uso adicional

Monitore o uso no dashboard para evitar surpresas.

## Contato e Suporte

- Railway Docs: https://docs.railway.app
- Railway Discord: https://discord.gg/railway
- GitHub Issues: Seu repositório

---

**Última atualização:** 03/11/2025
