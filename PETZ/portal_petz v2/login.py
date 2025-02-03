import streamlit as st
from db_connection import connect_to_db

def validate_login(email, password):
    conn = connect_to_db()
    cur = conn.cursor()
    cur.execute("SELECT usuario_id, departamento_id FROM usuarios WHERE email = %s AND senha_hash = %s", (email, password))
    user = cur.fetchone()
    conn.close()
    return user[0] if user else None

def login_screen():
    st.subheader("Login")
    email = st.text_input("Email")
    password = st.text_input("Senha", type="password")
    if st.button("Entrar"):
        user_id = validate_login(email, password)
        if user_id:
            st.session_state.authenticated = True
            st.session_state.user_id = user_id
            st.success("Login realizado com sucesso!")
        else:
            st.error("Usuário ou senha inválidos.")