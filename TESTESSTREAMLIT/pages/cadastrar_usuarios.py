import streamlit as st
from utils.database import SessionLocal
from utils.database import Empresa, Relatorio  # Importe os modelos necessários
from utils.powerbi  import get_power_bi_token
# Função para listar dashboards no workspace
def listar_dashboards_no_workspace(empresa):
    token = get_power_bi_token(empresa.client_id, empresa.client_secret, empresa.tenant_id)
    headers = {"Authorization": f"Bearer {token}"}
    url = f"https://api.powerbi.com/v1.0/myorg/groups/{empresa.workspace_id}/dashboards"
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json().get("value", [])
    else:
        raise Exception(f"Erro ao listar dashboards: {response.json()}")

def cadastrar_usuarios():
    st.title("Cadastrar Usuários para Acesso")

    # Conectar ao banco de dados
    session = SessionLocal()
    empresas = session.query(Empresa).all()

    if not empresas:
        st.warning("Nenhuma empresa cadastrada. Cadastre uma empresa primeiro.")
        return

    # Selecionar Empresa
    empresa_id = st.selectbox("Selecione uma empresa:", [
        (empresa.id, empresa.nome) for empresa in empresas
    ], format_func=lambda x: x[1])

    if empresa_id:
        empresa_selecionada = session.query(Empresa).get(empresa_id[0])

        # Listar Workspaces da Empresa
        st.subheader(f"Empresa Selecionada: {empresa_selecionada.nome}")
        workspace_id = empresa_selecionada.workspace_id
        st.write(f"**Workspace ID:** {workspace_id}")

        # Selecionar Dashboard
        st.subheader("Selecionar Dashboard")
        session.close()
        dashboards = listar_dashboards_no_workspace(empresa_selecionada)  # Função auxiliar para buscar dashboards
        dashboard_id = st.selectbox(
            "Selecione um Dashboard:",
            [(dashboard["id"], dashboard["displayName"]) for dashboard in dashboards],
            format_func=lambda x: x[1] if x else "Nenhum dashboard encontrado"
        )

        # Cadastrar usuário
        st.subheader("Cadastrar Usuário")
        email = st.text_input("E-mail do Usuário")
        permissao = st.selectbox("Permissão do Usuário", ["Viewer", "Contributor", "Member", "Admin"])
        if st.button("Adicionar Usuário"):
            if not all([email, permissao]):
                st.error("Todos os campos devem ser preenchidos!")
                return

            try:
                # Adicionar usuário ao Dashboard
                adicionar_usuario_no_dashboard(
                    empresa_selecionada.client_id,
                    empresa_selecionada.client_secret,
                    empresa_selecionada.tenant_id,
                    workspace_id,
                    dashboard_id[0],  # ID do Dashboard
                    email,
                    permissao
                )
                st.success(f"Usuário {email} adicionado com permissão {permissao}!")
            except Exception as e:
                st.error(f"Erro ao adicionar usuário: {e}")
# Função para adicionar usuário ao dashboard
def adicionar_usuario_no_dashboard(client_id, client_secret, tenant_id, workspace_id, dashboard_id, email, permissao):
    token = get_power_bi_token(client_id, client_secret, tenant_id)
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    url = f"https://api.powerbi.com/v1.0/myorg/groups/{workspace_id}/dashboards/{dashboard_id}/users"
    data = {
        "identifier": email,
        "groupUserAccessRight": permissao,
        "principalType": "User"
    }
    response = requests.post(url, headers=headers, json=data)
    if response.status_code not in (200, 201):
        raise Exception(f"Erro ao adicionar usuário: {response.json()}")  
 
cadastrar_usuarios()    