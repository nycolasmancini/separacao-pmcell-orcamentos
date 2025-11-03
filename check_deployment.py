#!/usr/bin/env python3
"""
Script para verificar status do deployment no Railway
"""
import requests
import json
import time

# Configuração
RAILWAY_API = "https://backboard.railway.app/graphql/v2"
PROJECT_ID = "c347d71b-d1df-482a-b1ca-df2b6c4dda7d"
ENVIRONMENT_ID = "70cf3d4a-ddb4-4979-a878-df1c74af8409"
SERVICE_ID = "d038a5e7-79d7-4f17-b4f2-433df33a75b7"
TOKEN = "rw_Fe26.2**c8de04de6540baa1b855eb39d571f2919d7e6be00640dab3d9172ae99c17c3e2*9W-FZdB4nLTffjkbSbC4Ow*Ww2uROO4XUHsbAu0nP6zG8XxVoZfVxjA6usgEqkvw4NsHY34TXIpJRwiWk1Lu9Rt2xxXAYPoogi0Czf8YxZvcg*1764762370156*6c3f6f3febbaa0a83ffc33d5941fc3b91ee332331991a75fc5b7c2c4e5684e69*sNI0oKUILhQBflqh5TAzP7wblRiHxlo8G3xou94iCuY"

headers = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json",
}

def graphql_query(query, variables=None):
    """Executa uma query GraphQL na API do Railway"""
    payload = {"query": query}
    if variables:
        payload["variables"] = variables

    try:
        response = requests.post(RAILWAY_API, json=payload, headers=headers, timeout=10)
        if response.status_code != 200:
            return None

        data = response.json()
        if "errors" in data:
            return None

        return data.get("data")
    except Exception as e:
        print(f"Erro: {e}")
        return None

def check_deployments():
    """Verifica os deployments do serviço"""
    print("🔍 Verificando deployments...\n")

    query = """
    query Service($id: String!) {
      service(id: $id) {
        name
        deployments(first: 5) {
          edges {
            node {
              id
              status
              createdAt
              url
              meta
            }
          }
        }
      }
    }
    """

    result = graphql_query(query, {"id": SERVICE_ID})
    if not result or "service" not in result:
        print("❌ Não foi possível obter informações dos deployments")
        return False

    service = result["service"]
    print(f"📦 Serviço: {service['name']}\n")

    deployments = service["deployments"]["edges"]
    if not deployments:
        print("⏳ Nenhum deployment encontrado ainda...")
        print("   O build pode estar iniciando. Isso é normal!")
        print("   Aguarde alguns momentos...\n")
        return False

    print(f"📋 Total de deployments: {len(deployments)}\n")

    for i, edge in enumerate(deployments, 1):
        deployment = edge["node"]
        status = deployment["status"]
        created = deployment["createdAt"]
        url = deployment.get("url", "N/A")

        status_emoji = {
            "BUILDING": "🔨",
            "DEPLOYING": "🚀",
            "SUCCESS": "✅",
            "FAILED": "❌",
            "CRASHED": "💥",
            "INITIALIZING": "⏳",
            "REMOVING": "🗑️"
        }.get(status, "❓")

        print(f"{i}. {status_emoji} Status: {status}")
        print(f"   URL: {url}")
        print(f"   Criado: {created[:19].replace('T', ' ')}")
        print()

        if status == "SUCCESS" and url != "N/A":
            print(f"🎉 Deploy bem-sucedido!")
            print(f"🌐 Acesse: {url}")
            return True
        elif status == "FAILED" or status == "CRASHED":
            print(f"❌ Deploy falhou. Verifique os logs no dashboard.")
            return False

    return False

def get_service_url():
    """Obtém a URL pública do serviço"""
    query = """
    query Service($id: String!) {
      service(id: $id) {
        name
        serviceInstances {
          domains {
            domain
          }
        }
      }
    }
    """

    result = graphql_query(query, {"id": SERVICE_ID})
    if result and "service" in result:
        instances = result["service"].get("serviceInstances", [])
        if instances:
            for instance in instances:
                domains = instance.get("domains", [])
                if domains:
                    return domains[0].get("domain")
    return None

def main():
    """Função principal"""
    print("🚀 Railway Deployment Monitor\n")
    print("=" * 50)
    print()

    success = check_deployments()

    if success:
        print("\n" + "=" * 50)
        print("✅ DEPLOY CONCLUÍDO COM SUCESSO!")
        print("=" * 50)

        url = get_service_url()
        if url:
            print(f"\n🌐 URL da Aplicação: https://{url}")
    else:
        print("\n" + "=" * 50)
        print("📊 Status do Deploy")
        print("=" * 50)
        print("\n💡 Dica: Você pode acompanhar em tempo real no dashboard:")
        print(f"   https://railway.com/project/{PROJECT_ID}/service/{SERVICE_ID}")
        print("\n⏰ O build pode levar de 3-10 minutos dependendo do tamanho do projeto.")

if __name__ == "__main__":
    main()
