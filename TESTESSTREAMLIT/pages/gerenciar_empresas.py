import streamlit as st
from utils.database import SessionLocal
from utils.database import Empresa  # Importe os modelos necessários

def gerenciar_empresas():
    st.title("Gerenciar Empresas")

    # Conectar ao banco de dados
    session = SessionLocal()

    # Listar empresas
    empresas = session.query(Empresa).all()
    if empresas:
        st.subheader("Empresas cadastradas")
        for empresa in empresas:
            st.write(f"{empresa.id} - *{empresa.nome}* - Workspace ID: {empresa.workspace_id}")

    # Adicionar nova empresa
    st.subheader("Adicionar nova empresa")
    with st.form("add_empresa"):
        nome = st.text_input("Nome da Empresa")
        client_id = st.text_input("Client ID")
        client_secret = st.text_input("Client Secret", type="password")
        tenant_id = st.text_input("Tenant ID")
        workspace_id = st.text_input("Workspace ID")
        submit = st.form_submit_button("Adicionar")

        if submit:
            nova_empresa = Empresa(
                nome=nome, client_id=client_id, client_secret=client_secret,
                tenant_id=tenant_id, workspace_id=workspace_id
            )
            session.add(nova_empresa)
            session.commit()
            st.success("Empresa adicionada com sucesso!")
            # Gera o link de embed para exibição
            embed_link = f"https://embed.powerbi.com/app/{workspace_id}"
            st.success("Empresa adicionada com sucesso!")
            st.markdown(f"Embed Link: [Clique aqui]({embed_link})", unsafe_allow_html=True)
    session.close()
    
gerenciar_empresas()    