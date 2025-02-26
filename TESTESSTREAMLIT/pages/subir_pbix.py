import streamlit as st
from utils.database import SessionLocal
from utils.database import Empresa  # Importe os modelos necessários

def subir_pbix():
    st.title("Subir Arquivo PBIX no Power BI")

    # Input para autenticação
    client_id = st.text_input("Client ID", key="upload_pbix_client_id")
    client_secret = st.text_input("Client Secret", type="password", key="upload_pbix_client_secret")
    tenant_id = st.text_input("Tenant ID", key="upload_pbix_tenant_id")
    
    # Input para seleção do Workspace
    workspace_id = st.text_input("Workspace ID", key="upload_pbix_workspace_id")
    
    # Upload do arquivo PBIX
    st.subheader("Selecione o arquivo PBIX")
    pbix_file = st.file_uploader("Escolha o arquivo PBIX", type=["pbix"], key="upload_pbix_file")
    
    # Nome do Relatório
    report_name = st.text_input("Nome do Relatório")

    if st.button("Subir PBIX"):
        if not all([client_id, client_secret, tenant_id, workspace_id, pbix_file, report_name]):
            st.error("Todos os campos devem ser preenchidos!")
            return

        try:
            # Obter token de autenticação
            token = get_power_bi_token(client_id, client_secret, tenant_id)
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "multipart/form-data"
            }

            # Upload do PBIX para o Workspace
            url = f"https://api.powerbi.com/v1.0/myorg/groups/{workspace_id}/imports?datasetDisplayName={report_name}"
            files = {"file": (pbix_file.name, pbix_file, "application/octet-stream")}

            response = requests.post(url, headers=headers, files=files)

            if response.status_code in (200, 201):  # Sucesso
                import_data = response.json()
                st.success(f"Arquivo PBIX '{report_name}' enviado com sucesso!")
                st.write(f"**Report ID:** `{import_data['id']}`")
                st.markdown(f"[Abrir Relatório no Power BI](https://app.powerbi.com/groups/{workspace_id}/reports/{import_data['id']})", unsafe_allow_html=True)
            else:
                st.error(f"Erro ao enviar arquivo: {response.json()}")

        except Exception as e:
            st.error(f"Erro: {e}")
subir_pbix()