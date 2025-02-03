import streamlit as st
from login import login_screen
from visualizar import view_grades
from alterar import edit_nfse
from incluir_usuarios import incluir_usuario  # Importe a função

def menu_lateral():
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
        st.session_state.user_id = None

    if not st.session_state.authenticated:
        login_screen()
    else:
        st.sidebar.title("Menu")
        option = st.sidebar.radio("Selecione uma opção", ["Visualizar Notas", "Alterar Notas","Incluir Usuário","Sair"])

        if option == "Visualizar Notas":
            view_grades()
        elif option == "Alterar Notas":
            edit_nfse()
        elif option == "Incluir Usuário":
            incluir_usuario()    
        elif option == "Sair":
            st.session_state.authenticated = False
            st.session_state.user_id = None
            st.info("Você saiu do sistema.")