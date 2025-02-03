import streamlit as st
from db_connection import connect_to_db
import base64

def get_nfse_by_invoice(numero_nota, departamento_id):
    """
    Busca a nota fiscal com base no número informado e no departamento.
    """
    conn = connect_to_db()
    cur = conn.cursor()
    query = "SELECT * FROM nfse WHERE numero_nota = %s AND departamento_id = %s"
    cur.execute(query, (numero_nota, departamento_id))
    nfse = cur.fetchone()
    conn.close()
    return nfse

def update_nfse_status(nfse_id, status):
    """
    Atualiza o status da nota fiscal para o valor informado.
    """
    conn = connect_to_db()
    cur = conn.cursor()
    query = "UPDATE nfse SET status = %s WHERE id = %s"
    cur.execute(query, (status, nfse_id))
    conn.commit()
    conn.close()

def display_pdf(pdf_bytes):
    """
    Converte o conteúdo em bytes do PDF para base64 e exibe-o em um iframe.
    """
    pdf_base64 = base64.b64encode(pdf_bytes).decode('utf-8')
    pdf_display = f'<iframe src="data:application/pdf;base64,{pdf_base64}" width="700" height="1000" type="application/pdf"></iframe>'
    st.markdown(pdf_display, unsafe_allow_html=True)

def edit_nfse():
    st.subheader("Alterar Nota Fiscal")
    
    # Filtro para número da nota fiscal
    numero_nota = st.text_input("Digite o número da Nota Fiscal para filtrar:")
    
    if st.button("Buscar Nota"):
        if not numero_nota:
            st.error("Por favor, informe o número da Nota Fiscal.")
            return
        
        # Certifique-se de que st.session_state.departamento_id esteja definido
        nfse = get_nfse_by_invoice(numero_nota, st.session_state.departamento_id)
        if nfse:
            # Dividindo a área em duas colunas para exibir PDF e dados extraídos lado a lado
            col1, col2 = st.columns(2)
            
            # Supondo que o campo PDF seja o último da linha retornada
            pdf_bytes = nfse[-1]  # Ajuste o índice conforme sua tabela
            
            with col1:
                st.markdown("### Nota Fiscal (PDF):")
                display_pdf(pdf_bytes)
            
            with col2:
                st.markdown("### Dados Extraídos:")
                # Exemplo: supondo a seguinte ordem de colunas:
                # [0] id, [1] nome_razao_social_tomador, [2] numero_nota,
                # [3] campo2, [4] campo3, [5] campo4, [6] campo5, [7] campo6, [8] status, [9] pdf
                st.write(f"**ID:** {nfse[0]}")
                st.write(f"**Nome/Razão Social do Tomador:** {nfse[1]}")
                st.write(f"**Número da Nota:** {nfse[2]}")
                st.write(f"**Campo 2:** {nfse[3]}")
                st.write(f"**Campo 3:** {nfse[4]}")
                st.write(f"**Campo 4:** {nfse[5]}")
                st.write(f"**Campo 5:** {nfse[6]}")
                st.write(f"**Campo 6:** {nfse[7]}")
                st.write(f"**Status Atual:** {nfse[8]}")
            
            # Botão para confirmar e atualizar o status da nota
            if st.button("Confirmar"):
                update_nfse_status(nfse[0], "ARQUIVO_AGUARDANDO")
                st.success("Nota Fiscal atualizada com status 'ARQUIVO_AGUARDANDO'.")
        else:
            st.error("Nenhuma Nota Fiscal encontrada para o número informado.")
