import streamlit as st
import psycopg2
from psycopg2 import sql
from hashlib import sha256
import pandas as pd

# Função para conectar ao banco de dados PostgreSQL
def connect_to_db():
    conn = psycopg2.connect(
        dbname="nfsedb",  # Substitua pelo nome do seu banco de dados
        user="postgres",           # Substitua pelo seu usuário do banco de dados
        password="admin",         # Substitua pela sua senha do banco de dados
        host="localhost",             # Pode ser outro host dependendo do seu servidor
        port="5432"                   # Porta padrão do PostgreSQL
    )
    return conn

# Função para verificar as credenciais no banco de dados
def check_credentials(username, password):
    conn = connect_to_db()
    cursor = conn.cursor()
    
    query = sql.SQL("SELECT usuario, senha FROM registros WHERE usuario = %s;")
    cursor.execute(query, (username,))
    
    user_data = cursor.fetchone()
    cursor.close()
    conn.close()

    if user_data and password == user_data[1]:
        return True
    return False

# Função para verificar se o usuário é administrador
def is_admin(username):
    conn = connect_to_db()
    cursor = conn.cursor()

    query = sql.SQL("SELECT is_admin FROM registros WHERE usuario = %s;")
    cursor.execute(query, (username,))

    result = cursor.fetchone()
    cursor.close()
    conn.close()
    print(result[0])
    return result is not None and result[0] in [True, 'true', 1]

# Função para buscar as notas fiscais no banco de dados
def get_nfse_data():
    conn = connect_to_db()
    cursor = conn.cursor()

    try:
        query = sql.SQL("SELECT * FROM nfse;")
        cursor.execute(query)
        data = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]  # Obter os nomes das colunas
    finally:
        cursor.close()
        conn.close()

    return data, columns

# Função para cadastrar novos usuários
def register_user(username, password, is_admin):
    conn = connect_to_db()
    cursor = conn.cursor()

    try:
        query = sql.SQL("INSERT INTO registros (usuario, senha, is_admin) VALUES (%s, %s, %s);")
        cursor.execute(query, (username, password, is_admin))
        conn.commit()
    finally:
        cursor.close()
        conn.close()

# Função para a página de login
def login_form():
    st.markdown("<div style='text-align: center;'>", unsafe_allow_html=True)
    st.image("petz-logo.png", width=200)  # Ajuste o tamanho com o parâmetro width
    st.markdown("</div>", unsafe_allow_html=True)

    st.title("Login Portal de Automações de Notas - Petz")
    
    username = st.text_input("Usuário")
    password = st.text_input("Senha", type="password")
    
    login_button = st.button("Entrar")
    
    if login_button:
        if username and password:
            if check_credentials(username, password):
                st.session_state['logged_in'] = True
                st.session_state['username'] = username

                # Depuração para verificar o valor de admin
                st.session_state['is_admin'] = is_admin(username)
                st.write(f"Admin detectado: {st.session_state['is_admin']}")  # Linha de depuração
                st.rerun()
            else:
                st.error("Usuário ou senha incorretos!")
        else:
            st.warning("Por favor, preencha ambos os campos!")

# Função para a página principal
# Função para inserir manualmente dados na tabela 'nfse'
def insert_nfse_data(fields):
    conn = connect_to_db()
    cursor = conn.cursor()

    try:
        placeholders = ', '.join(['%s'] * len(fields))
        columns = ', '.join(fields.keys())
        query = sql.SQL(f"INSERT INTO nfse ({columns}) VALUES ({placeholders});")
        cursor.execute(query, tuple(fields.values()))
        conn.commit()
    finally:
        cursor.close()
        conn.close()

# Atualização da página principal
# Função para atualizar uma nota fiscal na tabela 'nfse'
def update_nfse_data(id_nfse, updated_fields):
    conn = connect_to_db()
    cursor = conn.cursor()

    try:
        # Log para depuração
        print(f"Atualizando ID: {id_nfse} com dados: {updated_fields}")

        set_clause = ', '.join([f"{key} = %s" for key in updated_fields.keys()])
        query = sql.SQL(f"UPDATE nfse SET {set_clause} WHERE nfse_id = %s;")
        cursor.execute(query, tuple(updated_fields.values()) + (id_nfse,))
        conn.commit()
    except Exception as e:
        print(f"Erro ao atualizar: {e}")  # Log de erro
        raise
    finally:
        cursor.close()
        conn.close()

# Função para exibir o menu lateral com o botão de logout
def sidebar_menu():
    with st.sidebar:
        st.subheader("Menu")
        logout_button = st.button("Logout", key="logout", help="Sair da conta")
        if logout_button:
            # Remover a sessão de login e redirecionar para a página de login
            st.session_state['logged_in'] = False
            st.session_state['username'] = ""
            st.session_state['is_admin'] = False
            st.rerun()  # Redireciona para a página inicial

# Página principal atualizada
def main_page():
    # Chamar o menu lateral com o botão de logout
    sidebar_menu()

    st.title(f"Bem-vindo(a), {st.session_state['username']}!")
    st.write("Aqui estão as notas fiscais:")

    # Mock de dados da tabela para demonstração
    data, columns = get_nfse_data()
    
    if data:
        df = pd.DataFrame(data, columns=columns)

        # Filtros (3 em cima, 3 embaixo)
        st.subheader("Filtrar Notas Fiscais")
        col1, col2, col3 = st.columns(3)
        filtro_id = col1.number_input("ID da Nota Fiscal:", min_value=0, step=1, format="%d")
        filtro_numero = col2.text_input("Número da Nota:")
        filtro_data = col3.date_input("Data de Emissão:", value=None)

        col4, col5, col6 = st.columns(3)
        filtro_status = col4.text_input("Status:")
        filtro_emissor = col5.text_input("Emissor:")
        filtro_destinatario = col6.text_input("Destinatário:")

        # Aplicar os filtros
        if st.button("Buscar"):
            # Filtragem flexível
            filtered_df = df[
                ((df["nfse_id"] == filtro_id) if filtro_id > 0 else True) &
                ((df["numero_nota"].str.contains(filtro_numero, na=False)) if filtro_numero else True) &
                ((df["data_emissao"] == filtro_data.strftime("%Y-%m-%d")) if filtro_data else True) &
                ((df["status"].str.contains(filtro_status, na=False)) if filtro_status else True) &
                ((df["emissor"].str.contains(filtro_emissor, na=False)) if filtro_emissor else True) &
                ((df["destinatario"].str.contains(filtro_destinatario, na=False)) if filtro_destinatario else True)
            ]

            if not filtered_df.empty:
                st.write("Notas fiscais encontradas:")
                st.dataframe(filtered_df)

                # Selecionar nota para edição
            selected_index = st.selectbox(
            "Selecione uma nota fiscal para editar:",
            filtered_df.index,
            format_func=lambda x: f"ID: {filtered_df.loc[x, 'nfse_id']} - Número: {filtered_df.loc[x, 'numero_nota']}"
)

            if 'selected_nfse' not in st.session_state or st.session_state['selected_nfse'] != selected_index:
                st.session_state['selected_nfse'] = selected_index

            selected_nfse = filtered_df.loc[st.session_state['selected_nfse']]

                # Formulário de edição
            st.subheader(f"Edição da Nota Fiscal ID: {selected_nfse['nfse_id']}")
            with st.form("edit_nfse_form"):
                    updated_fields = {}

                    editable_columns = ["data_emissao_nf",
                                         "nome_razao_social_prestador", "endereco_prestador", "municipio_prestador",
                                         "email_tomador", "cnpj_prestador"]

                    cols = st.columns(len(editable_columns))

                    for idx, col_name in enumerate(editable_columns):
                        with cols[idx]:
                            updated_fields[col_name] = st.text_input(f"{col_name}:", value=str(selected_nfse[col_name]))
                    
                    submit_update = st.form_submit_button("Salvar Alterações")
                    if submit_update:
                        st.write("Botão clicado. Dados a serem atualizados", updated_fields)
                        try:
                            update_nfse_data(selected_nfse["nfse_id"], updated_fields)
                            st.success("Nota fiscal atualizada com sucesso!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Erro ao atualizar a nota fiscal: {e}")
        else:
                st.warning("Nenhuma nota fiscal encontrada para os critérios fornecidos.")
    else:
        st.write("Nenhuma nota fiscal encontrada.")

# Função para a página de administração
def admin_page():
    # Chamar o menu lateral com o botão de logout
    sidebar_menu()

    st.title("Página de Administração")
    st.write(f"Usuário atual: {st.session_state['username']}")
    st.write(f"Permissão de admin: {st.session_state['is_admin']}")

    if st.session_state['is_admin']:
        st.write("Gerencie os usuários aqui.")
        with st.form("register_user_form"):
            new_username = st.text_input("Novo Usuário")
            new_password = st.text_input("Senha", type="password")
            is_admin = st.checkbox("Administrador")
            submit_button = st.form_submit_button("Cadastrar Usuário")

            if submit_button:
                if new_username and new_password:
                    register_user(new_username, new_password, is_admin)
                    st.success("Usuário cadastrado com sucesso!")
                else:
                    st.error("Por favor, preencha todos os campos.")
    else:
        st.error("Acesso negado! Esta página é apenas para administradores.")

def add_custom_css():
    st.markdown(
        f"""
        <style>
        /* Cor de fundo personalizada */
        .main {{
            background-color: #fef8df !important;
        }}
        
        /* Cor do fundo da barra lateral */
        [data-testid="stSidebar"] {{
            background-color: #fef8df !important;
        }}
        
        /* Alterar cor dos botões ao serem clicados */
        button:active {{
            background-color: #6aa7e1 !important;
            color: white !important;
        }}
        
        /* Garantir que os textos do botão sejam visíveis */
        button {{
            color: black !important;
        }}
        </style>
        """,
        unsafe_allow_html=True
    )

# Função principal
def main():
    add_custom_css()  # Aplicar estilo personalizado

    if 'logged_in' not in st.session_state or not st.session_state['logged_in']:
        login_form()
    else:
        menu = st.sidebar.selectbox("Menu", ["Página Principal", "Administração"])

        if menu == "Página Principal":
            main_page()
        elif menu == "Administração":
            admin_page()

if __name__ == "__main__":
    main()