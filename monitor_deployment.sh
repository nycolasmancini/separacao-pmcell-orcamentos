#!/bin/bash
# Monitor contínuo do deployment Railway

echo "🔍 Monitorando deployment Railway..."
echo "Pressione Ctrl+C para parar"
echo ""

while true; do
    clear
    echo "======================================"
    echo "   Railway Deployment Monitor"
    echo "======================================"
    echo ""
    date
    echo ""

    python3 check_deployment.py

    echo ""
    echo "Próxima verificação em 15 segundos..."
    sleep 15
done
