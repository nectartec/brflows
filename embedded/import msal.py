import msal
import requests
import json

# Configurações do Power BI (substituir pelos seus valores)
CLIENT_ID = "SEU_CLIENT_ID"
CLIENT_SECRET = "SEU_CLIENT_SECRET"
TENANT_ID = "SEU_TENANT_ID"
WORKSPACE_ID = "SEU_WORKSPACE_ID"
REPORT_ID = "SEU_REPORT_ID"
DATASET_ID = "SEU_DATASET_ID"

# URL do Azure para autenticação
AUTHORITY_URL = f"https://login.microsoftonline.com/{TENANT_ID}"
SCOPE = ["https://graph.microsoft.com/.default"]

def get_access_token():
    """ Obtém o token de acesso do Azure AD para autenticação no Power BI """
    app = msal.ConfidentialClientApplication(CLIENT_ID, CLIENT_SECRET, authority=AUTHORITY_URL)
    token_response = app.acquire_token_for_client(scopes=SCOPE)

    if "access_token" not in token_response:
        raise Exception("Erro ao obter token de acesso: " + json.dumps(token_response, indent=4))

    return token_response["access_token"]

def generate_embed_token(user_email):
    """ Gera um token de embed para o usuário, aplicando RLS """
    access_token = get_access_token()

    url = f"https://api.powerbi.com/v1.0/myorg/reports/{REPORT_ID}/GenerateToken"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    # Definição do RLS usando EffectiveIdentity
    body = {
        "accessLevel": "View",
        "identities": [
            {
                "username": user_email,  # Passa o e-mail do usuário
                "roles": ["ClienteFiltro"],  # Nome da função RLS configurada no Power BI
                "datasets": [DATASET_ID]
            }
        ]
    }

    response = requests.post(url, headers=headers, json=body)
    if response.status_code != 200:
        raise Exception(f"Erro ao gerar token de embed: {response.text}")

    return response.json().get("token")

# Teste: Gerar um token para um usuário específico
if __name__ == "__main__":
    user_email = "cliente@empresa.com"  # E-mail do cliente logado
    embed_token = generate_embed_token(user_email)
    print("Token de Embed Gerado:", embed_token)
