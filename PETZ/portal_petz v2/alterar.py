import streamlit as st
from db_connection import connect_to_db

def get_user_grades(departamento_id):
    conn = connect_to_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM nfse WHERE departamento_id = %s", (departamento_id,))
    grades = cur.fetchall()
    conn.close()
    return grades

def update_nfse(numero_nota, nome_razao_social_tomador, campo2, campo3, campo4, campo5, campo6):
    conn = connect_to_db()
    cur = conn.cursor()
    query = """
    UPDATE nfse
    SET nome_razao_social_tomador = %s,
        endereco_prestador = %s,
        municipio_prestador = %s,
        endereco_tomador = %s,
        municipio_tomador = %s,
        email_tomador = %s,
        status = 'ARQUIVO_ALTERADO'
    WHERE numero_nota = %s
    """
    cur.execute(query, (nome_razao_social_tomador, campo2, campo3, campo4, campo5, campo6, numero_nota))
    conn.commit()
    conn.close()

def edit_nfse():
    st.subheader("Alterar Nota Fiscal")
    nfse_list = get_user_grades(st.session_state.departamento_id)
    if nfse_list:
        # Alteração: armazena o numero_nota no dicionário para que seja usado como filtro
        nfse_options = {f"{nfse[1]} (Nota: {nfse[2]})": nfse[2] for nfse in nfse_list}
        selected_nfse = st.selectbox("Selecione a Nota Fiscal para alterar:", list(nfse_options.keys()))
        
        # Campos a serem alterados
        nome_razao_social_tomador = st.text_input("Nome/Razão Social do Tomador")
        campo2 = st.text_input("Endereço Prestador")
        campo3 = st.text_input("Municipio Prestador")
        campo4 = st.text_input("Endereço Tomador")
        campo5 = st.text_input("Municipio Tomador")
        campo6 = st.text_input("E-mail Tomador")
        
        if st.button("Salvar"):
            numero_nota = nfse_options[selected_nfse]
            update_nfse(numero_nota, nome_razao_social_tomador, campo2, campo3, campo4, campo5, campo6)
            st.success("Nota Fiscal atualizada com sucesso!")
    else:
        st.info("Nenhuma Nota Fiscal encontrada para alterar.")

if "departamento_id" not in st.session_state:
    st.session_state.departamento_id = 1  # ou outro valor padrão ou proveniente do login
