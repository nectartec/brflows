import streamlit as st
from db_connection import connect_to_db
from datetime import datetime

def get_user_grades(departamento_id):
    """Busca os dados da tabela nfse com base no departamento"""
    conn = connect_to_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM nfse WHERE departamento_id = %s", (departamento_id,))
    grades = cur.fetchall()
    conn.close()
    return grades

def insert_into_massivo(numero_nota, item_contab, campo2, campo3, campo4, campo5, campo6, campo7, campo8, campo9, campo10, campo11,
                        campo12, campo13, campo14, campo15, campo16, campo17, campo18, campo19, campo20, campo21):
    """Insere os dados na tabela massivo"""
    conn = connect_to_db()
    cur = conn.cursor()
    
    query = """
    INSERT INTO massivo ("Numero NF", "Item Contab.", "Finalidade", 
    "Tipo Pgto",  "CC.Despesa", "Centro Custo", 
    "Tipo SP", "Codigo Forn.", "Loja Fornec",
    "Valor", "Juros", "Multa",
    "Observacoes", "Serie NF", "Natureza",
    "Pedido Comp.", "Loja Fatura", "It.Cont.Desp",
    "Saldo Solic.", "Rateio ?", "Forma Pgto",
    "Desconto",
    "status")
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 'ARQUIVO_ALTERADO')
    """
    
    cur.execute(query, (numero_nota, item_contab, campo2, campo3, campo4, campo5, campo6, campo7, campo8, campo9, campo10, campo11,
                        campo12, campo13, campo14, campo15, campo16, campo17, campo18, campo19, campo20, campo21))
    conn.commit()
    conn.close()

def safe_date_conversion(date_value):
    """Converte datas de forma segura"""
    if not date_value or str(date_value).startswith("-") or str(date_value) in ["0000-00-00", "None", "null", None]:
        return ""

    try:
        if isinstance(date_value, str):
            return datetime.strptime(date_value, "%Y-%m-%d").strftime("%d/%m/%Y")
        elif isinstance(date_value, datetime):
            return date_value.strftime("%d/%m/%Y")
        else:
            return ""
    except (ValueError, TypeError):
        return ""


def edit_nfse():
    st.subheader("Alterar Nota Fiscal")
    
    nfse_list = get_user_grades(st.session_state.departamento_id)

    if nfse_list:
        nfse_options = {f"Nota: {nfse[3]}": nfse for nfse in nfse_list}
        selected_nfse = st.selectbox("Selecione a Nota Fiscal para alterar:", list(nfse_options.keys()))

        selected_nfse_data = nfse_options[selected_nfse] 

        # ✅ Aplicando a função de conversão segura
        data_emissao = safe_date_conversion(selected_nfse_data[4])
        data_de_vencimento = safe_date_conversion(selected_nfse_data[14])

        st.write(f"Data de Emissão: {data_emissao}")
        st.write(f"Data de Vencimento: {data_de_vencimento}")

        item_contab = st.text_input("Item Contábil", value=selected_nfse_data[27])
        campo2 = st.text_input("Finalidade", value=selected_nfse_data[19])
        campo3 = st.text_input("Tipo Pagamento", value=selected_nfse_data[18])
        campo4 = st.text_input("CC Despesa", value=selected_nfse_data[17])
        campo5 = st.text_input("Centro Custo", value=selected_nfse_data[16])
        campo6 = st.text_input("Tipo SP", value=selected_nfse_data[15])
        campo7 = st.text_input("Código Fornecedor", value=selected_nfse_data[34])
        campo8 = st.text_input("Loja Fornecedor", value=selected_nfse_data[35])
        campo9 = st.text_input("Valor", value=selected_nfse_data[5])
        campo10 = st.text_input("Juros", value=selected_nfse_data[21])
        campo11 = st.text_input("Multa", value=selected_nfse_data[22])
        campo12 = st.text_input("Observações", value=selected_nfse_data[26])
        campo13 = st.text_input("Série NF", value=selected_nfse_data[20])
        campo14 = st.text_input("Natureza", value=selected_nfse_data[28])
        campo15 = st.text_input("Pedido Compra",value=selected_nfse_data[29])
        campo16 = st.text_input("Loja Fatura", value=selected_nfse_data[30])
        campo17 = st.text_input("Item Cont. Desp", value=selected_nfse_data[31])
        campo18 = st.text_input("Saldo Solic", value=selected_nfse_data[32])
        campo19 = st.text_input("Rateio", value=selected_nfse_data[23])
        campo20 = st.text_input("Forma Pagamento", value=selected_nfse_data[24])
        campo21 = st.text_input("Desconto", value=selected_nfse_data[25])

        if st.button("Salvar"):
            numero_nota = str(selected_nfse_data[3])    
            insert_into_massivo(numero_nota, item_contab, campo2, campo3, campo4, campo5, campo6, campo7, campo8, campo9, campo10, campo11,
                                campo12, campo13, campo14, campo15, campo16, campo17, campo18, campo19, campo20, campo21)
            st.success("Nota Fiscal salva na tabela massivo com sucesso!")
    else:
        st.info("Nenhuma Nota Fiscal encontrada para alterar.")

if "departamento_id" not in st.session_state:
    st.session_state.departamento_id = 1 
