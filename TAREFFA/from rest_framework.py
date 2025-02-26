from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.urls import path
import requests

# Configurações do Power BI (preencha com seus dados)
TENANT_ID = "SEU_TENANT_ID"
CLIENT_ID = "SEU_CLIENT_ID"
CLIENT_SECRET = "SEU_CLIENT_SECRET"
WORKSPACE_ID = "SEU_WORKSPACE_ID"
REPORT_ID = "SEU_REPORT_ID"
DATASET_ID = "SEU_DATASET_ID"

# URLs do Azure AD e Power BI
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
                "roles": ["RLS_Clientes"],  # Nome da função RLS no Power BI
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

class GenerateEmbedView(APIView):
    def post(self, request):
        user_email = request.data.get("email")
        
        if not user_email:
            return Response({"error": "Email do usuário é obrigatório"}, status=status.HTTP_400_BAD_REQUEST)
        
        embed_token = get_embed_token(user_email)
        if embed_token:
            html_code = generate_html(embed_token)
            return Response({"html": html_code}, status=status.HTTP_200_OK)
        else:
            return Response({"error": "Erro ao gerar o token de embed"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

urlpatterns = [
    path("generate-embed/", GenerateEmbedView.as_view(), name="generate-embed"),
]
