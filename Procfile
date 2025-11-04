# Procfile para Railway.app
# Usa Daphne (ASGI) para suportar WebSockets + HTTP

# Migrar banco de dados antes de iniciar
release: cd backend && python manage.py migrate --noinput && python manage.py collectstatic --noinput

# Servidor ASGI (Daphne) para WebSockets + HTTP
web: cd backend && daphne -b 0.0.0.0 -p $PORT separacao_pmcell.asgi:application
