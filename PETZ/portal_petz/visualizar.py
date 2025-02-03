import streamlit as st
import pandas as pd
from db_connection import connect_to_db

def get_user_grades(user_id):
    conn = connect_to_db()
    cur = conn.cursor()
    cur.execute("SELECT nfse.departamento_id,valor_total,numero_nota FROM nfse inner join usuarios on usuarios.departamento_id = nfse.departamento_id WHERE usuario_id = %s", (user_id,))
    grades = cur.fetchall()
    conn.close()
    return grades

def view_grades():
    st.subheader("Minhas Notas")

    # Obtém as notas do usuário
    grades = get_user_grades(st.session_state.user_id)

    if grades:
        # Converte para DataFrame
        df = pd.DataFrame(grades, columns=["ID Departamento", "Valor Total", "Nota"])

        # Inicializa variáveis de estado para os filtros
        if "depto_filter" not in st.session_state:
            st.session_state.depto_filter = ""
        if "valor_filter" not in st.session_state:
            st.session_state.valor_filter = ""
        if "nota_filter" not in st.session_state:
            st.session_state.nota_filter = ""

        # Campos de entrada para filtragem
        depto_filter = st.text_input("Filtrar por ID Departamento", st.session_state.depto_filter)
        valor_filter = st.text_input("Filtrar por Valor Total", st.session_state.valor_filter)
        nota_filter = st.text_input("Filtrar por Nota", st.session_state.nota_filter)

        col1, col2 = st.columns([0.5, 0.5])

        with col1:
            filtrar = st.button("Filtrar")
        with col2:
            limpar = st.button("Limpar Filtros")

        # Aplica os filtros apenas se o botão "Filtrar" for pressionado
        if filtrar:
            st.session_state.depto_filter = depto_filter
            st.session_state.valor_filter = valor_filter
            st.session_state.nota_filter = nota_filter

            # Aplica filtro de ID Departamento (se preenchido)
            if depto_filter:
                df = df[df["ID Departamento"].astype(str) == depto_filter]

            # Aplica filtro de Valor Total (se preenchido)
            if valor_filter:
                try:
                    df = df[df["Valor Total"] == float(valor_filter)]
                except ValueError:
                    st.warning("Por favor, insira um número válido no filtro de Valor Total.")

            # Aplica filtro de Nota (se preenchido)
            if nota_filter:
                try:
                    df = df[df["Nota"] == float(nota_filter)]
                except ValueError:
                    st.warning("Por favor, insira um número válido no filtro de Nota.")

        # Se o botão "Limpar Filtros" for pressionado, resetamos os filtros
        if limpar:
            st.session_state.depto_filter = ""
            st.session_state.valor_filter = ""
            st.session_state.nota_filter = ""
            st.rerun()  # Atualiza a página para limpar os filtros

        # Exibe a tabela filtrada
        st.table(df[["ID Departamento", "Valor Total", "Nota"]])
    else:
        st.info("Nenhuma nota encontrada.")

