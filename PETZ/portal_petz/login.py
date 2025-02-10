import streamlit as st
from db_connection import connect_to_db
import bcrypt

def validate_login(email, password):
    conn = connect_to_db()
    cur = conn.cursor()
    
    # Busca o hash da senha armazenada no banco
    cur.execute("SELECT usuario_id, senha_hash, is_admin FROM usuarios WHERE email = %s", (email,))
    user = cur.fetchone()
    
    conn.close()

    if user:
        user_id, senha_hash, is_admin = user
        
        # Verifica se a senha fornecida corresponde ao hash armazenado
        if bcrypt.checkpw(password.encode(), senha_hash.encode()):
            return {"user_id": user_id, "is_admin": is_admin}

    return None

def login_screen():
    st.subheader("Login")
    email = st.text_input("Email")
    password = st.text_input("Senha", type="password")
    
    if st.button("Entrar"):
        user = validate_login(email, password)
        if user:
            st.session_state.authenticated = True
            st.session_state.user_id = user["user_id"]
            st.session_state.user_email = email  # Armazena o email para verificar permissões depois
            st.session_state.is_admin = user["is_admin"]  # Armazena o status de admin
            st.success("Login realizado com sucesso!")
        else:
            st.error("Usuário ou senha inválidos.")
