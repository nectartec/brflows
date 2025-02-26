
import streamlit as st
from utils.database import SessionLocal
from utils.database import Empresa  # Importe os modelos necessários
def gerenciar_relatorios():
    st.title("Gerenciar Relatórios")

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
        st.subheader(f"Relatórios da empresa: {empresa_selecionada.nome}")

        # Listar relatórios
        relatorios = empresa_selecionada.relatorios
        if relatorios:
            for relatorio in relatorios:
                st.write(f"*{relatorio.nome}* - Report ID: {relatorio.report_id}")

        # Adicionar relatório
        st.subheader("Adicionar novo relatório")
        with st.form("add_relatorio"):
            nome_relatorio = st.text_input("Nome do Relatório")
            report_id = st.text_input("Report ID")
            submit = st.form_submit_button("Adicionar")

            if submit:
                novo_relatorio = Relatorio(
                    nome=nome_relatorio, report_id=report_id, empresa_id=empresa_selecionada.id
                )
                session.add(novo_relatorio)
                session.commit()
                st.success("Relatório adicionado com sucesso!")

    session.close()
gerenciar_relatorios()    