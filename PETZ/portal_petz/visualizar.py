import streamlit as st
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
    grades = get_user_grades(st.session_state.user_id)
    if grades:
        for grade in grades:
            st.write(f"**{grade[1]}**: {grade[2]}")
    else:
        st.info("Nenhuma nota encontrada.")
