import streamlit as st
from db_connection import connect_to_db

def get_user_grades(departamento_id):
    conn = connect_to_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM nfse WHERE departamento_id = %s", (departamento_id,))
    grades = cur.fetchall()
    conn.close()
    return grades

def update_grade(grade_id, nome_razao_social_tomador):
    conn = connect_to_db()
    cur = conn.cursor()
    cur.execute("UPDATE  SET nome_razao_social_tomador = %s WHERE id = %s", (nome_razao_social_tomador, grade_id))
    conn.commit()
    conn.close()

def edit_grades():
    '''
    st.subheader("Alterar Nota")
    grades = get_user_grades(st.session_state.departamento_id)
    if grades:
        grade_options = {f"{grade[1]} (Nota: {grade[2]})": grade[0] for grade in grades}
        selected_grade = st.selectbox("Selecione a matéria para alterar:", list(grade_options.keys()))
        new_grade = st.number_input("Nova nota:", min_value=0.0, max_value=100.0, step=0.1)
        if st.button("Salvar"):
            grade_id = grade_options[selected_grade]
            update_grade(grade_id, nome_razao_social_tomador)
            st.success("Nota atualizada com sucesso!")
    else:
        st.info("Nenhuma nota encontrada para alterar.")
    '''    
