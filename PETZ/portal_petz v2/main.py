import streamlit as st
from menu_lateral import menu_lateral

 
def main():
     
    st.image("petz-logo.png", width=200)  # Ajuste o tamanho com o parâmetro width
    st.markdown("</div>", unsafe_allow_html=True)
    st.title("Sistema de Notas com Login")
    menu_lateral()

if __name__ == "__main__":
    main()