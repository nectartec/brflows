import streamlit as st
from utils.database import SessionLocal 
from utils.database import Empresa  # Importe os modelos necessários

def listar_workspaces():
    st.title("Listar Workspaces no Power BI")

    # Input para autenticação
    client_id = st.text_input("Client ID", key="list_workspaces_client_id")
    client_secret = st.text_input("Client Secret", type="password", key="list_workspaces_client_secret")
    tenant_id = st.text_input("Tenant ID", key="list_workspaces_tenant_id")

    if st.button("Listar Workspaces"):
        if not all([client_id, client_secret, tenant_id]):
            st.error("Todos os campos devem ser preenchidos!")
            return

        # Obter token de autenticação
        try:
            token = get_power_bi_token(client_id, client_secret, tenant_id)
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }

            # Enviar solicitação para listar os Workspaces
            url = "https://api.powerbi.com/v1.0/myorg/groups"
            response = requests.get(url, headers=headers)

            if response.status_code == 200:  # Status 200 significa sucesso
                workspaces = response.json().get("value", [])
                if workspaces:
                    st.success(f"Encontrados {len(workspaces)} Workspaces.")
                    for workspace in workspaces:
                        st.write(f"**Nome:** {workspace['name']}")
                        st.write(f"**Workspace ID:** `{workspace['id']}`")
                        st.markdown(f"[Abrir no Power BI](https://app.powerbi.com/groups/{workspace['id']})", unsafe_allow_html=True)
                        st.divider()
                else:
                    st.info("Nenhum Workspace encontrado.")

            else:
                st.error(f"Erro ao listar Workspaces: {response.json()}")

        except Exception as e:
            st.error(f"Erro: {e}") 
            
listar_workspaces()