#!/usr/bin/env python3
"""
Script para deploy automatizado no Railway via API GraphQL
"""
import requests
import json
import sys

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

    response = requests.post(RAILWAY_API, json=payload, headers=headers)
    if response.status_code != 200:
        print(f"❌ Erro na API: {response.status_code}")
        print(response.text)
        return None

    data = response.json()
    if "errors" in data:
        print(f"❌ Erros GraphQL: {json.dumps(data['errors'], indent=2)}")
        return None

    return data.get("data")

def set_variables():
    """Configura as variáveis de ambiente"""
    print("🔧 Configurando variáveis de ambiente...")

    variables_to_set = {
        "SECRET_KEY": "sa85%ck0zp!3-w#ptuw!8n(b=g7x*e2ysou-*@%dtb2zg+f6*w",
        "DEBUG": "False",
        "ALLOWED_HOSTS": ".railway.app",
    }

    for key, value in variables_to_set.items():
        mutation = """
        mutation VariableUpsert($input: VariableUpsertInput!) {
          variableUpsert(input: $input)
        }
        """

        input_data = {
            "projectId": PROJECT_ID,
            "environmentId": ENVIRONMENT_ID,
            "serviceId": SERVICE_ID,
            "name": key,
            "value": value
        }

        result = graphql_query(mutation, {"input": input_data})
        if result:
            print(f"  ✅ {key} configurado")
        else:
            print(f"  ❌ Falha ao configurar {key}")

def get_services():
    """Lista todos os serviços do projeto"""
    print("📋 Listando serviços...")

    query = """
    query Project($id: String!) {
      project(id: $id) {
        services {
          edges {
            node {
              id
              name
            }
          }
        }
      }
    }
    """

    result = graphql_query(query, {"id": PROJECT_ID})
    if result and "project" in result:
        services = result["project"]["services"]["edges"]
        print(f"  Serviços encontrados: {len(services)}")
        for edge in services:
            service = edge["node"]
            print(f"    - {service['name']} (ID: {service['id']})")
        return services
    return []

def connect_database_references():
    """Conecta as referências do PostgreSQL e Redis"""
    print("🔗 Conectando referências de bancos de dados...")

    # Primeiro, precisamos encontrar os IDs dos serviços Postgres e Redis
    services = get_services()

    postgres_id = None
    redis_id = None

    for edge in services:
        service = edge["node"]
        name = service["name"].lower()
        if "postgres" in name:
            postgres_id = service["id"]
            print(f"  📊 PostgreSQL encontrado: {postgres_id}")
        elif "redis" in name:
            redis_id = service["id"]
            print(f"  📊 Redis encontrado: {redis_id}")

    # Criar referências de variáveis
    if postgres_id:
        print("  🔗 Conectando DATABASE_URL...")
        mutation = """
        mutation VariableUpsert($input: VariableUpsertInput!) {
          variableUpsert(input: $input)
        }
        """
        input_data = {
            "projectId": PROJECT_ID,
            "environmentId": ENVIRONMENT_ID,
            "serviceId": SERVICE_ID,
            "name": "DATABASE_URL",
            "referenceVariableId": f"${{{{Postgres.DATABASE_URL}}}}"
        }
        result = graphql_query(mutation, {"input": input_data})
        if result:
            print("    ✅ DATABASE_URL conectado")

    if redis_id:
        print("  🔗 Conectando REDIS_URL...")
        mutation = """
        mutation VariableUpsert($input: VariableUpsertInput!) {
          variableUpsert(input: $input)
        }
        """
        input_data = {
            "projectId": PROJECT_ID,
            "environmentId": ENVIRONMENT_ID,
            "serviceId": SERVICE_ID,
            "name": "REDIS_URL",
            "referenceVariableId": f"${{{{Redis.REDIS_URL}}}}"
        }
        result = graphql_query(mutation, {"input": input_data})
        if result:
            print("    ✅ REDIS_URL conectado")

def set_root_directory():
    """Configura o Root Directory do serviço"""
    print("📁 Configurando Root Directory...")

    mutation = """
    mutation ServiceUpdate($id: String!, $input: ServiceUpdateInput!) {
      serviceUpdate(id: $id, input: $input)
    }
    """

    input_data = {
        "rootDirectory": "/backend"
    }

    result = graphql_query(mutation, {"id": SERVICE_ID, "input": input_data})
    if result:
        print("  ✅ Root Directory configurado para /backend")
    else:
        print("  ❌ Falha ao configurar Root Directory")

def main():
    """Função principal"""
    print("🚀 Iniciando configuração do Railway...\n")

    # 1. Listar serviços
    get_services()
    print()

    # 2. Configurar Root Directory
    set_root_directory()
    print()

    # 3. Configurar variáveis de ambiente
    set_variables()
    print()

    # 4. Conectar bancos de dados
    connect_database_references()
    print()

    print("✅ Configuração concluída!")
    print("\n📌 Próximo passo: Execute 'railway up' para fazer o deploy")

if __name__ == "__main__":
    main()
