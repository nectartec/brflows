import streamlit as st
from db_connection import connect_to_db  # Função que conecta ao banco de dados

# Função para incluir usuário no banco
def insert_user(nome, email, senha_hash):
    conn = connect_to_db()
    cur = conn.cursor()

    # Verifica se o login já existe
    cur.execute("SELECT usuario_id FROM usuarios WHERE email = %s", (email,))
    user_exists = cur.fetchone()

    if user_exists:
        st.warning("Já existe um usuário com este login.")
        return

    # Insere o novo usuário
    cur.execute(
        "INSERT INTO usuarios (nome, email, senha_hash) VALUES (%s, %s, %s)",
        (nome, email, senha_hash),
    )
    conn.commit()
    conn.close()
    st.success("Usuário incluído com sucesso!")

# Tela de inclusão de usuários
def incluir_usuario():
    st.subheader("Incluir Usuário")

    # Formulário de inclusão
    with st.form("form_incluir_usuario"):
        username = st.text_input("Nome do Usuário")
        login = st.text_input("Login")
        password = st.text_input("Senha", type="password")

        # Botão para enviar
        submitted = st.form_submit_button("Salvar")
        if submitted:
            if username and login and password:
                insert_user(username, login, password)
            else:
                st.error("Preencha todos os campos.")