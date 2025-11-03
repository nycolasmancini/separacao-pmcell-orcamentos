#!/bin/bash

# Script de Deploy Automatizado para Railway
# Projeto: Separação PMCELL
# Versão: 1.0

set -e  # Exit on error

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}================================================${NC}"
echo -e "${BLUE}   Deploy Automatizado - Railway.app${NC}"
echo -e "${BLUE}   Projeto: Separação PMCELL${NC}"
echo -e "${BLUE}================================================${NC}\n"

# Função para verificar se comando existe
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# 1. Verificar Railway CLI
echo -e "${YELLOW}[1/8] Verificando Railway CLI...${NC}"
if ! command_exists railway; then
    echo -e "${RED}❌ Railway CLI não encontrada!${NC}"
    echo -e "${YELLOW}Instalando Railway CLI...${NC}"
    npm install -g @railway/cli
    echo -e "${GREEN}✅ Railway CLI instalada!${NC}\n"
else
    echo -e "${GREEN}✅ Railway CLI encontrada!${NC}\n"
fi

# 2. Verificar autenticação
echo -e "${YELLOW}[2/8] Verificando autenticação...${NC}"
if ! railway whoami >/dev/null 2>&1; then
    echo -e "${RED}❌ Não autenticado no Railway!${NC}"
    echo -e "${YELLOW}Fazendo login...${NC}"
    railway login
    echo -e "${GREEN}✅ Login realizado!${NC}\n"
else
    RAILWAY_USER=$(railway whoami)
    echo -e "${GREEN}✅ Autenticado como: $RAILWAY_USER${NC}\n"
fi

# 3. Verificar projeto Railway
echo -e "${YELLOW}[3/8] Verificando projeto Railway...${NC}"
if ! railway status >/dev/null 2>&1; then
    echo -e "${RED}❌ Projeto não vinculado!${NC}"
    echo -e "${YELLOW}Escolha uma opção:${NC}"
    echo "1) Criar novo projeto"
    echo "2) Vincular a projeto existente"
    read -p "Opção: " option

    case $option in
        1)
            read -p "Nome do projeto: " project_name
            railway init --name "$project_name"
            ;;
        2)
            railway link
            ;;
        *)
            echo -e "${RED}Opção inválida!${NC}"
            exit 1
            ;;
    esac
    echo -e "${GREEN}✅ Projeto configurado!${NC}\n"
else
    echo -e "${GREEN}✅ Projeto já vinculado!${NC}\n"
fi

# 4. Adicionar PostgreSQL
echo -e "${YELLOW}[4/8] Configurando PostgreSQL...${NC}"
if railway variables | grep -q "DATABASE_URL"; then
    echo -e "${GREEN}✅ PostgreSQL já configurado!${NC}\n"
else
    echo -e "${YELLOW}Adicionando PostgreSQL...${NC}"
    railway add --database postgres
    echo -e "${GREEN}✅ PostgreSQL adicionado!${NC}\n"
fi

# 5. Adicionar Redis
echo -e "${YELLOW}[5/8] Configurando Redis...${NC}"
if railway variables | grep -q "REDIS_URL"; then
    echo -e "${GREEN}✅ Redis já configurado!${NC}\n"
else
    echo -e "${YELLOW}Adicionando Redis...${NC}"
    railway add --database redis
    echo -e "${GREEN}✅ Redis adicionado!${NC}\n"
fi

# 6. Configurar variáveis de ambiente
echo -e "${YELLOW}[6/8] Configurando variáveis de ambiente...${NC}"

# Verificar SECRET_KEY
if ! railway variables | grep -q "SECRET_KEY"; then
    echo -e "${YELLOW}Gerando SECRET_KEY...${NC}"
    SECRET_KEY=$(python3 -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())")
    railway variables --set "SECRET_KEY=$SECRET_KEY"
    echo -e "${GREEN}✅ SECRET_KEY configurada!${NC}"
fi

# Verificar DEBUG
if ! railway variables | grep -q "DEBUG="; then
    railway variables --set "DEBUG=False"
    echo -e "${GREEN}✅ DEBUG configurado!${NC}"
fi

# Verificar ALLOWED_HOSTS
if ! railway variables | grep -q "ALLOWED_HOSTS"; then
    railway variables --set "ALLOWED_HOSTS=.railway.app"
    echo -e "${GREEN}✅ ALLOWED_HOSTS configurado!${NC}"
fi

echo -e "${YELLOW}⚠️  IMPORTANTE: Configure CSRF_TRUSTED_ORIGINS após obter a URL do app!${NC}"
echo -e "${YELLOW}   Exemplo: railway variables --set 'CSRF_TRUSTED_ORIGINS=https://seu-app.up.railway.app'${NC}\n"

# 7. Deploy
echo -e "${YELLOW}[7/8] Iniciando deploy...${NC}"
railway up --detach

echo -e "${GREEN}✅ Deploy iniciado!${NC}"
echo -e "${YELLOW}Aguardando deploy...${NC}"
sleep 5

# Mostrar logs
echo -e "\n${BLUE}Últimos logs:${NC}"
railway logs --tail 20

# 8. Executar migrações
echo -e "\n${YELLOW}[8/8] Executando migrações...${NC}"
read -p "Deseja executar migrações agora? (s/n): " run_migrations

if [ "$run_migrations" = "s" ] || [ "$run_migrations" = "S" ]; then
    echo -e "${YELLOW}Executando migrate...${NC}"
    railway run python manage.py migrate
    echo -e "${GREEN}✅ Migrações executadas!${NC}"

    read -p "Deseja criar superusuário? (s/n): " create_super
    if [ "$create_super" = "s" ] || [ "$create_super" = "S" ]; then
        railway run python manage.py createsuperuser
    fi
fi

# Finalização
echo -e "\n${BLUE}================================================${NC}"
echo -e "${GREEN}✅ Deploy Concluído!${NC}"
echo -e "${BLUE}================================================${NC}\n"

echo -e "${YELLOW}📋 Próximos Passos:${NC}"
echo -e "1. Obter URL do app: ${BLUE}railway open${NC}"
echo -e "2. Ver logs: ${BLUE}railway logs${NC}"
echo -e "3. Ver status: ${BLUE}railway status${NC}"
echo -e "4. Configurar CSRF_TRUSTED_ORIGINS com a URL obtida"
echo -e "5. Acessar dashboard: ${BLUE}https://railway.app/project${NC}\n"

echo -e "${YELLOW}⚠️  Não esqueça de configurar CSRF_TRUSTED_ORIGINS!${NC}"
echo -e "${YELLOW}   railway variables --set 'CSRF_TRUSTED_ORIGINS=https://seu-app.up.railway.app'${NC}\n"

# Abrir app no navegador
read -p "Deseja abrir o app no navegador? (s/n): " open_browser
if [ "$open_browser" = "s" ] || [ "$open_browser" = "S" ]; then
    railway open
fi

echo -e "${GREEN}Tudo pronto! 🚀${NC}\n"
