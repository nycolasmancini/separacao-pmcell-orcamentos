#!/usr/bin/env python3
"""
Script para corrigir Root Directory no Railway
Muda de "/backend" para "backend" (sem barra inicial)
"""
import requests
import json

# Configuração
RAILWAY_API = "https://backboard.railway.app/graphql/v2"
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
            print(f"❌ Erro HTTP: {response.status_code}")
            print(response.text)
            return None

        data = response.json()
        if "errors" in data:
            print(f"❌ Erros GraphQL:")
            for error in data["errors"]:
                print(f"   {error.get('message', 'Unknown error')}")
            return None

        return data.get("data")
    except Exception as e:
        print(f"❌ Exceção: {e}")
        return None

def fix_root_directory():
    """Corrige o Root Directory removendo a barra inicial"""
    print("🔧 Corrigindo Root Directory...\n")
    print("  Mudando de: /backend")
    print("  Para:       backend\n")

    mutation = """
    mutation ServiceUpdate($id: String!, $input: ServiceUpdateInput!) {
      serviceUpdate(id: $id, input: $input)
    }
    """

    input_data = {
        "rootDirectory": "backend"
    }

    result = graphql_query(mutation, {"id": SERVICE_ID, "input": input_data})

    if result:
        print("✅ Root Directory corrigido com sucesso!")
        print("\n📦 Railway deve fazer redeploy automaticamente em alguns segundos...")
        return True
    else:
        print("❌ Falha ao corrigir Root Directory")
        print("\n💡 Tente corrigir manualmente no dashboard:")
        print("   1. Acesse Settings do serviço backend")
        print("   2. Mude Root Directory de '/backend' para 'backend'")
        print("   3. Salve as alterações")
        return False

def main():
    """Função principal"""
    print("🚀 Railway Root Directory Fix\n")
    print("=" * 60)
    print()

    success = fix_root_directory()

    print("\n" + "=" * 60)

    if success:
        print("\n✅ CORREÇÃO APLICADA!")
        print("\n📊 Próximos passos:")
        print("   1. Aguarde o redeploy automático (2-5 minutos)")
        print("   2. Monitore o status com: python3 check_deployment.py")
        print("   3. Se build for bem-sucedido, execute as migrações")
    else:
        print("\n⚠️  CORREÇÃO MANUAL NECESSÁRIA")
        print("\nAcesse o dashboard e faça a correção manualmente.")

if __name__ == "__main__":
    main()
