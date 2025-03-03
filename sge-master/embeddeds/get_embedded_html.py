import requests
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from embeddeds.models import Embedded
from django.conf import settings
import logging

logging.basicConfig(level=logging.INFO)
'''
def get_powerbi_embed_token(client_id, client_secret, tenant_id, report_id, workspace_id, dataset_id, email):
    """
    Gera um token de embed para o Power BI com RLS, filtrando pelo e-mail do usuário.
    """
    authority = f"https://login.microsoftonline.com/{tenant_id}"
    scope = ["https://analysis.windows.net/powerbi/api/.default"]

    
    # Autenticação com a Microsoft
    app = ConfidentialClientApplication(client_id, client_secret, authority)
    token_response = app.acquire_token_for_client(scopes=scope)

    if "access_token" not in token_response:
        error_message = token_response.get("error_description") or json.dumps(token_response)
        return None, error_message

    access_token = token_response["access_token"]

    # Criar o corpo da requisição para o token de embed com RLS
    url = f"https://api.powerbi.com/v1.0/myorg/groups/{workspace_id}/reports/{report_id}/GenerateToken"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {access_token}"
    }
    body = {
        "accessLevel": "View" 
    }

    response = requests.post(url, headers=headers, json=body)
    response_data = response.json()

    return response_data.get("token"), response_data.get("error", "Erro desconhecido")
'''
# URLS do Azure AD e Power BI

def get_access_token(client_id, client_secret, tenant_id):
    
    """Obtém o token de acesso do Azure AD."""
    payload = {
        "grant_type": "client_credentials",
        "client_id": client_id,
        "client_secret": client_secret,
        "resource": "https://analysis.windows.net/powerbi/api",
    }
    token_url = f"https://login.microsoftonline.com/{tenant_id}/oauth2/token"
    
    headers = {
        "Content-Type": "application/x-www-form-urlencoded"  # 🔹 Boa prática: informa o tipo de dados
    }

    response = requests.post(token_url, headers=headers, data=payload)

    if response.status_code != 200:
        print(f"Erro ao obter token: {response.status_code} - {response.text}")
        return None  # Retorna None se a autenticação falhar

    return response.json().get("access_token")



def get_embed_token(client_id, client_secret, tenant_id, report_id, workspace_id, dataset_id, email):
    """Gera o token de embed com RLS para o usuário específico."""
    try:
        access_token = get_access_token(client_id, client_secret, tenant_id)

        if not access_token:
            logging.error("Erro: Token de acesso não foi obtido.")
            return None, "Falha na autenticação"

        embed_url = f"https://api.powerbi.com/v1.0/myorg/groups/{workspace_id}/reports/{report_id}/GenerateToken"
        headers = {"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"}
        body = {
            "accessLevel": "View",
            "identities": [
                {
                    "username": email,  # 🔥 Aqui aplicamos o filtro de RLS pelo ID do gerente
                    "roles": ["rls_cliente"],  # 🔥 Nome da Role configurada no Power BI
                    "datasets": [dataset_id]
                }
            ]            
        }

        response = requests.post(embed_url, headers=headers, json=body)

        logging.info(f"Status Code: {response.status_code}")
        logging.debug(f"Response Headers: {response.headers}")
        logging.debug(f"Response Content: {response.text}")

        if response.status_code != 200:
            return None, f"Erro ao gerar embed token: {response.status_code} - {response.text}"

        response_data = response.json()
        return response_data.get("token"), None
    except requests.exceptions.RequestException as e:
        logging.error(f"Erro de requisição: {e}")
        return None, f"Erro de requisição: {e}"
    except requests.exceptions.JSONDecodeError:
        logging.error("Erro ao processar resposta da API")
        return None, "Erro ao processar resposta da API"


def get_embedded_html(request):
    """
    Retorna um HTML com o iframe para embutir um relatório do Power BI,
    gerando um token de embed com RLS filtrando pelo e-mail do usuário.
    """
    if "email" not in request.GET:
        return JsonResponse({"error": "O parâmetro 'email' é obrigatório"}, status=400)

    email = request.GET["email"]

    # Buscar o relatório correto no banco de dados 
    report = get_object_or_404(Embedded)
    print(email)
    # Pega as credenciais do banco de dados
    client_id =report.CLIENT_ID
    client_secret = report.CLIENT_SECRET
    tenant_id = report.TENANT_ID
    workspace_id = report.WORKSPACE_ID
    report_id = report.REPORT_ID
    dataset_id = report.DATASET_ID
    # Gera o token de embed com RLS
    #embed_token = "H4sIAAAAAAAEAB3Sta7tBgBE0X-5rSOZKdIrfMzM2JnxmDnKv-cq_a7WzD8_VvoMU1r8_P0jvpL-jGNYzGr95Qb09aZIG2I2Q9KylDaM4JX2jqs-2oaW19APgFYPmE9DcxTBehOCQ8z-PJLSjl9taNNXd5guQtz9RTstFH9ECX9E8Tw54eFkiRKnFLKOs2WCCwOp8kGqfrM_UiQspU2eo_EMRNucekDoq__wHYLfosmJk-h0IYo9l3F-EQgJkfMTqmxuSQK5H3NCsXPur9T41IoQSaY7GobEeOr5sByoQ5ALli22Shw8AsXCSfhQpadnRPik4EKt8APWBPuz7a3RYCoK98N0cmVyuJ0a092OqNqQ7FZn5mkyWnsIM63zPXzJB5IKssl6RgmUqbYesxLz0I3-7kmoqUMZ6dIA38IRzhQAaWxcrowNV60lv2n8SD0kf76vYwro-LnkZAox1glol2MEJKaDjPedvCtAo4W998kMZ8ByoADJXVGcyjob3E6M2HAe51EbAl6-GaWhV5ySV0nPCw1SUegpbk-F0wiX_qLSDs9HlvB8-ZzIkwtdXUxwzw1uLe3yMh3oV_US7OyLqh35oAsmufnE62TyJbjCVewCjyo_Nu-OmtzkGg43rNQgjTe682I5bYRV4CvvzZ5NFGSZb5OFZSjldyzL5U0Uv6TiPNyoT5e0osg7D853tB-Y7VU9l_N3pI05OVDK4c048vDqzI6Xfudno702gqCVM9VwNUWzCnTE_lBtj11DStpSLHNl04WwIEN-TZS56EM3nJNGoE8ZiEZg_zouePSckE2KGH8OSrcw7M_PXz_s-sz7pJbP7_WXBd8JFz2D6ob8aB5aQeO6LnY63BXXIZuOUy0w_vR_SXrUvDQ4nKB5JUW72JVoOtXDvIfRSJfhGnCIXIorJLcI93jTmlVNE3ebVp_LwU_kG0xZI4-U6kk24cq0c8Yvil3WKcaYfvPV_nEGg3cVxjbHTnk-xu3mw_qVvEfYjEaxAikDsVZkj5bhFY2qdR2F7ymsqbbK50gltlLOYOTAhAFD_cYsgUQFv_7uE764SPES6y5AVTcqhi682NE1s6EyL6Hm2iZdCFKl4hrkmgGGTnCi0MIxSt87S-4IHMTLXBFxAmCNsTFW2Za7-naJOES-56rhztI51LqGXuuZNvXsSZmyUP_5n_mZm3KVg1_lWY02qoZHpZAq93LaIHkd8fq_ctt6TPdjLX8zhcnDuRTF-hOWO0LPNAycb7Yv5OduT-87NfXZ7gKTpH5YVazTxydWzvXQv_uVPTk9rneX9nxHhjRpdCFUHWmxpx69JC6EQ3c9ACX79qF4x7lPyRDqoMUWLfLESnHb6_GAboA91QQik4xRFXb-rcKQy6thQOat5zOdE_y58vxEwqrFZNrYDEwu7QPHpFUq3f1ZPIJguApdbrIGcBwKntoEpDHw0-aMEKj0w6WNlt20ZZ6IK1KljaD4eWGfELLRmjrqy9zXcZaEp5bWeHagEbTfEF-MFjsFFunY8EXMumBvWhdMES5xyJcyhn57NKVXwoA-r0oFma8PsePqWqcCPKwDO8D8Mv_7H_1t__3uBQAA.eyJjbHVzdGVyVXJsIjoiaHR0cHM6Ly9XQUJJLUJSQVpJTC1TT1VUSC1CLVBSSU1BUlktcmVkaXJlY3QuYW5hbHlzaXMud2luZG93cy5uZXQiLCJleHAiOjE3NDA1MTM0MjEsImFsbG93QWNjZXNzT3ZlclB1YmxpY0ludGVybmV0Ijp0cnVlfQ=="
    embed_token, error =  get_embed_token(client_id, client_secret, tenant_id, report_id, workspace_id, dataset_id, email)
    if not embed_token:
        return JsonResponse({"error": error}, status=400)

    
    embed_url = f"https://app.powerbi.com/reportEmbed?reportId={report_id}&groupId={workspace_id}"
    # 🔹 Criando o HTML corretamente formatado
    # 🔹 HTML formatado para ser embutido sem escapes errados
    html_content = f"""
    <div>
        <h1>Relatório da Empresa</h1>
        <div id="reportContainer" style="width: 100%; height: 600px;"></div>

        <script src="https://cdnjs.cloudflare.com/ajax/libs/powerbi-client/2.19.0/powerbi.min.js"></script>
        <script>
            document.addEventListener("DOMContentLoaded", function() {{
                if (typeof powerbi === "undefined") {{
                    console.error("Power BI SDK não carregado corretamente.");
                    return;
                }}

                var models = window['powerbi-client'].models;
                var embedConfiguration = {{
                    type: 'report',
                    id: '{report_id}',
                    embedUrl: '{embed_url}',
                    accessToken: '{embed_token}',
                    tokenType: models.TokenType.Embed,
                    settings: {{
                        filterPaneEnabled: false,
                        navContentPaneEnabled: true
                    }}
                }};

                var reportContainer = document.getElementById("reportContainer");
                powerbi.embed(reportContainer, embedConfiguration);
            }});
        </script>
    </div>
    """

    # 🔹 Retornando JSON sem escapes errados
    return JsonResponse({"html": html_content}, json_dumps_params={'ensure_ascii': False, 'indent': 0}, safe=False)
    