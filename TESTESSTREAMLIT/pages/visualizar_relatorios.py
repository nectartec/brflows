import streamlit as st
from utils.database import SessionLocal
from utils.database import Empresa, Relatorio # Importe os modelos necessários
def visualizar_relatorios():
    st.title("Visualizar Relatórios")

    # Conectar ao banco de dados
    session = SessionLocal()
    empresas = session.query(Empresa).all()

    if not empresas:
        st.warning("Nenhuma empresa cadastrada. Cadastre uma empresa primeiro.")
        return

    # Selecionar empresa
    empresa_id = st.selectbox("Selecione uma empresa:", [
        (empresa.id, empresa.nome) for empresa in empresas
    ], format_func=lambda x: x[1])

    if empresa_id:
        empresa_selecionada = session.query(Empresa).get(empresa_id[0])

        # Selecionar relatório
        relatorio_id = st.selectbox("Selecione um relatório:", [
            (relatorio.id, relatorio.nome) for relatorio in empresa_selecionada.relatorios
        ], format_func=lambda x: x[1])

        if relatorio_id:
            relatorio_selecionado = session.query(Relatorio).get(relatorio_id[0])
            st.subheader(f"Visualizando: {relatorio_selecionado.nome}")

            # Geração de token para embed
            token = get_power_bi_token(
                empresa_selecionada.client_id,
                empresa_selecionada.client_secret,
                empresa_selecionada.tenant_id
            )

            st.write("Token de acesso gerado:")
            st.code(token)
            
visualizar_relatorios()            