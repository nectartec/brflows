import streamlit as st
import bcrypt
from db_connection import connect_to_db  # Função que conecta ao banco de dados
from psycopg2 import sql

# Função para verificar se o usuário é administrador
def is_admin(email):
    conn = connect_to_db()
    cursor = conn.cursor()

    query = sql.SQL("SELECT is_admin FROM usuarios WHERE email = %s;")
    cursor.execute(query, (email,))

    result = cursor.fetchone()
    cursor.close()
    conn.close()

    if result is not None:
        return bool(result[0])  # Retorna True se is_admin for verdadeiro no banco

    return False  # Se não encontrar o usuário, assume que não é admin

# Função para gerar hash seguro da senha
def hash_password(password):
    salt = bcrypt.gensalt()  # Gera um salt aleatório
    return bcrypt.hashpw(password.encode(), salt).decode()  # Retorna a senha criptografada

# Função para incluir usuário no banco com senha criptografada
def insert_user(nome, email, senha, is_admin=False):
    conn = connect_to_db()
    cur = conn.cursor()

    # Verifica se o email já existe
    cur.execute("SELECT usuario_id FROM usuarios WHERE email = %s", (email,))
    user_exists = cur.fetchone()

    if user_exists:
        st.warning("Já existe um usuário com este email.")
        conn.close()
        return

    # Recupera o departamento_id do session_state ou define um valor padrão
    departamento_id = st.session_state.get("departamento_id")
    if departamento_id is None:
        st.error("Departamento não definido na sessão.")
        conn.close()
        return

    # Criptografa a senha antes de armazená-la
    senha_hash = hash_password(senha)

    # Insere o novo usuário incluindo o departamento_id e o status de administrador
    cur.execute(
        "INSERT INTO usuarios (nome, email, senha_hash, departamento_id, is_admin) VALUES (%s, %s, %s, %s, %s)",
        (nome, email, senha_hash, departamento_id, is_admin),
    )
    conn.commit()
    conn.close()
    st.success("Usuário incluído com sucesso!")

# Tela de inclusão de usuários
def incluir_usuario():
    st.subheader("Incluir Usuário")

    # Verifica se o usuário está autenticado
    if "authenticated" not in st.session_state or not st.session_state.authenticated:
        st.error("Você precisa estar logado para acessar esta página.")
        return

    # Obtém o email do usuário logado
    email_logado = st.session_state.get("user_email")

    if not email_logado:
        st.error("Erro ao recuperar as informações do usuário logado.")
        return

    # Verifica se o usuário logado é admin
    if not is_admin(email_logado):
        st.error("Apenas administradores podem cadastrar novos usuários.")
        return

    # Formulário de inclusão
    with st.form("form_incluir_usuario"):
        nome = st.text_input("Nome do Usuário")
        email = st.text_input("Email")
        senha = st.text_input("Senha", type="password")
        is_admin_value = st.checkbox("Conceder acesso de administrador")

        # Botão para enviar
        submitted = st.form_submit_button("Salvar")
        if submitted:
            if nome and email and senha:
                insert_user(nome, email, senha, is_admin_value)
            else:
                st.error("Preencha todos os campos.")

# Definição do departamento_id no início da aplicação
if "departamento_id" not in st.session_state:
    st.session_state.departamento_id = 1
