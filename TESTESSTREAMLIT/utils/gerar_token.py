import streamlit as st
import requests
import json

# Configurações do Power BI (preencha com seus dados)
TENANT_ID = "SEU_TENANT_ID"
CLIENT_ID = "SEU_CLIENT_ID"
CLIENT_SECRET = "SEU_CLIENT_SECRET"
WORKSPACE_ID = "SEU_WORKSPACE_ID"
REPORT_ID = "SEU_REPORT_ID"
DATASET_ID = "SEU_DATASET_ID"

# URLS do Azure AD e Power BI
TOKEN_URL = f"https://login.microsoftonline.com/{TENANT_ID}/oauth2/v2.0/token"
EMBED_URL = f"https://api.powerbi.com/v1.0/myorg/groups/{WORKSPACE_ID}/reports/{REPORT_ID}/GenerateToken"

def get_access_token():
    """Obtém o token de acesso do Azure AD."""
    payload = {
        "grant_type": "client_credentials",
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "scope": "https://graph.microsoft.com/.default",
    }
    response = requests.post(TOKEN_URL, data=payload)
    return response.json().get("access_token")

def get_embed_token(user_email):
    """Gera o token de embed com RLS para o usuário específico."""
    access_token = get_access_token()
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {access_token}"}
    
    body = {
        "accessLevel": "View",
        "identities": [
            {
                "username": user_email,
                "roles": ["ClienteFiltro"],  # Nome da função RLS no Power BI
                "datasets": [DATASET_ID]
            }
        ]
    }
    
    response = requests.post(EMBED_URL, headers=headers, json=body)
    return response.json().get("token")

def generate_html(embed_token):
    """Gera um HTML contendo o Power BI Embedded com o token gerado."""
    return f"""
    <html>
    <head>
        <script src='https://cdnjs.cloudflare.com/ajax/libs/powerbi-client/2.19.1/powerbi.min.js'></script>
    </head>
    <body>
        <div id='reportContainer' style='width:100%; height:600px;'></div>
        <script>
            var embedConfiguration = {{
                type: 'report',
                id: '{REPORT_ID}',
                embedUrl: 'https://app.powerbi.com/reportEmbed?reportId={REPORT_ID}&groupId={WORKSPACE_ID}',
                accessToken: '{embed_token}',
                tokenType: 1
            }};
            
            var reportContainer = document.getElementById('reportContainer');
            var powerbi = window.powerbi;
            var report = powerbi.embed(reportContainer, embedConfiguration);
        </script>
    </body>
    </html>
    """

# Interface Streamlit
st.title("Power BI Embedded com Streamlit")
user_email = st.text_input("Digite seu e-mail (para RLS)", "cliente1@empresa.com")

if st.button("Gerar Embed e Exibir Relatório"):
    embed_token = get_embed_token(user_email)
    if embed_token:
        st.success("Token de embed gerado com sucesso!")
        st.markdown("### Relatório Embutido:")
        st.components.v1.html(generate_html(embed_token), height=600)
    else:
        st.error("Erro ao gerar o token de embed")

if st.button("Gerar HTML para Embeber"):
    embed_token = get_embed_token(user_email)
    if embed_token:
        html_code = generate_html(embed_token)
        st.download_button("Baixar HTML", html_code, file_name="powerbi_embedded.html")
