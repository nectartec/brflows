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

def upsert_into_massivo(numero_nota, item_contab, finalidade, tipo_pgto, cc_despesa, centro_custo, tipo_sp, codigo_forn, loja_forn, valor_total, juros, multa,
                        observacoes, serie_nf, natureza, pedido_comp, loja_fatura, it_cont_desp, saldo_solic, rateio, forma_pgto, desconto):
    """Insere ou atualiza os dados na tabela massivo."""
    conn = connect_to_db()
    cur = conn.cursor()

    # Verifica se a nota já existe
    cur.execute("SELECT 1 FROM massivo WHERE \"Numero NF\" = %s", (numero_nota,))
    exists = cur.fetchone()

    if exists:
        query = """
        UPDATE massivo SET
        "Item Contab." = %s,
        "Finalidade" = %s,
        "Tipo Pgto" = %s,
        "CC.Despesa" = %s,
        "Centro Custo" = %s,
        "Tipo SP" = %s,
        "Codigo Forn." = %s,
        "Loja Fornec" = %s,
        "Valor" = %s,
        "Juros" = %s,
        "Multa" = %s,
        "Observacoes" = %s,
        "Serie NF" = %s,
        "Natureza" = %s,
        "Pedido Comp." = %s,
        "Loja Fatura" = %s,
        "It.Cont.Desp" = %s,
        "Saldo Solic." = %s,
        "Rateio ?" = %s,
        "Forma Pgto" = %s,
        "Desconto" = %s,
        "status" = 'ARQUIVO_ALTERADO'
        WHERE "Numero NF" = %s
        """
        cur.execute(query, (item_contab, finalidade, tipo_pgto, cc_despesa, centro_custo, tipo_sp, codigo_forn, loja_forn, valor_total, juros, multa,
                            observacoes, serie_nf, natureza, pedido_comp, loja_fatura, it_cont_desp, saldo_solic, rateio, forma_pgto, desconto, numero_nota))
    else:
        query = """
        INSERT INTO massivo ("Numero NF", "Item Contab.", "Finalidade", 
        "Tipo Pgto",  "CC.Despesa", "Centro Custo", 
        "Tipo SP", "Codigo Forn.", "Loja Fornec",
        "Valor", "Juros", "Multa",
        "Observacoes", "Serie NF", "Natureza",
        "Pedido Comp.", "Loja Fatura", "It.Cont.Desp",
        "Saldo Solic.", "Rateio ?", "Forma Pgto",
        "Desconto", "status")
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 'ARQUIVO_ALTERADO')
        """
        cur.execute(query, (numero_nota, item_contab, finalidade, tipo_pgto, cc_despesa, centro_custo, tipo_sp, codigo_forn, loja_forn, valor_total, juros, multa,
                            observacoes, serie_nf, natureza, pedido_comp, loja_fatura, it_cont_desp, saldo_solic, rateio, forma_pgto, desconto))

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
        finalidade = st.text_input("Finalidade", value=selected_nfse_data[19])
        tipo_pgto = st.text_input("Tipo Pagamento", value=selected_nfse_data[18])
        cc_despesa = st.text_input("CC Despesa", value=selected_nfse_data[17])
        centro_custo = st.text_input("Centro Custo", value=selected_nfse_data[16])
        tipo_sp = st.text_input("Tipo SP", value=selected_nfse_data[15])
        codigo_forn = st.text_input("Código Fornecedor", value=selected_nfse_data[34])
        loja_forn = st.text_input("Loja Fornecedor", value=selected_nfse_data[35])
        valor_total = st.text_input("Valor", value=selected_nfse_data[5])
        juros = st.text_input("Juros", value=selected_nfse_data[21])
        multa = st.text_input("Multa", value=selected_nfse_data[22])
        observacoes = st.text_input("Observações", value=selected_nfse_data[26])
        serie_nf = st.text_input("Série NF", value=selected_nfse_data[20])
        natureza = st.text_input("Natureza", value=selected_nfse_data[28])
        pedido_comp = st.text_input("Pedido Compra",value=selected_nfse_data[29])
        loja_fatura = st.text_input("Loja Fatura", value=selected_nfse_data[30])
        it_cont_desp = st.text_input("Item Cont. Desp", value=selected_nfse_data[31])
        saldo_solic = st.text_input("Saldo Solic", value=selected_nfse_data[32])
        rateio = st.text_input("Rateio", value=selected_nfse_data[23])
        forma_pgto = st.text_input("Forma Pagamento", value=selected_nfse_data[24])
        desconto = st.text_input("Desconto", value=selected_nfse_data[25])

        if st.button("Salvar"):
            numero_nota = str(selected_nfse_data[3])    
            upsert_into_massivo(numero_nota, item_contab, finalidade, tipo_pgto, cc_despesa, centro_custo, tipo_sp, codigo_forn, loja_forn, valor_total, juros, multa,
                                observacoes, serie_nf, natureza, pedido_comp, loja_fatura, it_cont_desp, saldo_solic, rateio, forma_pgto, desconto)
            st.success("Nota Fiscal salva na tabela massivo com sucesso!")
    else:
        st.info("Nenhuma Nota Fiscal encontrada para alterar.")

if "departamento_id" not in st.session_state:
    st.session_state.departamento_id = 1 
