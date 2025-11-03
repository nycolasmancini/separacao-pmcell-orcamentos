#!/usr/bin/env python3
"""
Script para obter logs do deployment no Railway
"""
import requests
import json

# Configuração
RAILWAY_API = "https://backboard.railway.app/graphql/v2"
PROJECT_ID = "c347d71b-d1df-482a-b1ca-df2b6c4dda7d"
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
            print(f"Erro HTTP: {response.status_code}")
            print(response.text)
            return None

        data = response.json()
        if "errors" in data:
            print(f"Erros GraphQL: {json.dumps(data['errors'], indent=2)}")
            return None

        return data.get("data")
    except Exception as e:
        print(f"Exceção: {e}")
        return None

def get_deployment_logs():
    """Obtém os logs do deployment mais recente"""
    print("📋 Obtendo logs do deployment...\n")

    # Primeiro, pegar o ID do deployment mais recente
    query = """
    query Service($id: String!) {
      service(id: $id) {
        deployments(first: 1) {
          edges {
            node {
              id
              status
              createdAt
            }
          }
        }
      }
    }
    """

    result = graphql_query(query, {"id": SERVICE_ID})
    if not result or "service" not in result:
        print("❌ Não foi possível obter deployment")
        return

    deployments = result["service"]["deployments"]["edges"]
    if not deployments:
        print("❌ Nenhum deployment encontrado")
        return

    deployment = deployments[0]["node"]
    deployment_id = deployment["id"]
    status = deployment["status"]

    print(f"🔍 Deployment ID: {deployment_id}")
    print(f"📊 Status: {status}")
    print(f"⏰ Criado em: {deployment['createdAt'][:19].replace('T', ' ')}")
    print("\n" + "=" * 80)
    print("📝 LOGS DE BUILD")
    print("=" * 80 + "\n")

    # Obter logs do build
    logs_query = """
    query DeploymentLogs($deploymentId: String!) {
      deploymentLogs(deploymentId: $deploymentId, limit: 1000) {
        timestamp
        message
      }
    }
    """

    logs_result = graphql_query(logs_query, {"deploymentId": deployment_id})
    if not logs_result or "deploymentLogs" not in logs_result:
        print("❌ Não foi possível obter logs")
        print("\n💡 Verifique os logs no dashboard:")
        print(f"   https://railway.com/project/{PROJECT_ID}/service/{SERVICE_ID}")
        return

    logs = logs_result["deploymentLogs"]
    if not logs:
        print("⚠️  Nenhum log disponível ainda")
        return

    # Mostrar logs
    for log in logs:
        timestamp = log.get("timestamp", "")
        message = log.get("message", "")
        if timestamp:
            time_str = timestamp[:19].replace('T', ' ')
            print(f"[{time_str}] {message}")
        else:
            print(message)

    print("\n" + "=" * 80)

def main():
    """Função principal"""
    get_deployment_logs()

if __name__ == "__main__":
    main()
