
import streamlit as st
from utils.database import SessionLocal
from utils.database import Empresa  # Importe os modelos necessários
def criar_workspace():
    st.title("Criar Workspace no Power BI")

    # Input para os dados necessários
    client_id = st.text_input("Client ID", key="create_workspace_client_id")
    client_secret = st.text_input("Client Secret", type="password", key="create_workspace_client_secret")
    tenant_id = st.text_input("Tenant ID", key="create_workspace_tenant_id")
    nome_workspace = st.text_input("Nome do Workspace")

    if st.button("Criar Workspace"):
        if not all([client_id, client_secret, tenant_id, nome_workspace]):
            st.error("Todos os campos devem ser preenchidos!")
            return

        # Obter token de autenticação do Azure
        try:
            token = get_power_bi_token(client_id, client_secret, tenant_id)
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }

            # Enviar solicitação para criar o Workspace
            url = "https://api.powerbi.com/v1.0/myorg/groups"
            payload = {"name": nome_workspace}
            response = requests.post(url, headers=headers, json=payload)

            if response.status_code == 201:  # Status 201 significa sucesso
                workspace_id = response.json().get("id")
                st.success(f"Workspace '{nome_workspace}' criado com sucesso!")
                st.write(f"Workspace ID: `{workspace_id}`")
                st.markdown(f"[Abrir Workspace no Power BI](https://app.powerbi.com/groups/{workspace_id})", unsafe_allow_html=True)
            else:
                st.error(f"Erro ao criar Workspace: {response.json()}")

        except Exception as e:
            st.error(f"Erro: {e}")
criar_workspace()            