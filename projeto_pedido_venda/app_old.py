import streamlit as st
from reportlab.pdfgen import canvas
import smtplib
import sqlite3
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
import io  # Importação correta do módulo io
# Configurações de E-mail
SMTP_SERVER = "email-ssl.com.br"
SMTP_PORT = 587
EMAIL_USER = "richardt.rieper@nectartec.com.br"
EMAIL_PASS = "Matheus29@"

# Conexão com o banco de dados SQLite (pode ser substituído por MySQL, PostgreSQL, etc.)
def conectar_banco():
    conn = sqlite3.connect("pedidos.db")  # Substitua pelo caminho do seu banco de dados
    return conn

# Função para buscar os dados do pedido
def buscar_pedido(pedido_id):
    conn = conectar_banco()
    cursor = conn.cursor()
    cursor.execute("SELECT cliente, email, produtos, total FROM pedidos WHERE id = ?", (pedido_id,))
    pedido = cursor.fetchone()
    conn.close()
    return pedido


def gerar_pdf(cliente, produtos, total):
    pdf_buffer = io.BytesIO()
    c = canvas.Canvas(pdf_buffer)
    c.drawString(100, 800, f"Pedido de Venda")
    c.drawString(100, 780, f"Cliente: {cliente}")
    c.drawString(100, 760, f"Produtos: {produtos}")
    c.drawString(100, 740, f"Total: R$ {total}")
    c.save()
    pdf_buffer.seek(0)
    return pdf_buffer

def enviar_email(destinatario, cliente, pdf_buffer):
    msg = MIMEMultipart()
    msg["From"] = EMAIL_USER
    msg["To"] = destinatario
    msg["Subject"] = "Pedido de Venda"
    body = f"Olá {cliente}, segue o seu pedido em anexo."
    msg.attach(MIMEText(body, "plain"))

    attachment = MIMEApplication(pdf_buffer.read(), _subtype="pdf")
    attachment.add_header("Content-Disposition", "attachment", filename="pedido.pdf")
    msg.attach(attachment)

    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(EMAIL_USER, EMAIL_PASS)
            server.sendmail(EMAIL_USER, destinatario, msg.as_string())
        return "Pedido enviado com sucesso!"
    except Exception as e:
        return f"Erro ao enviar o pedido: {e}"

st.title("Gerador de Pedido de Venda")
with st.form("pedido_form"):
    cliente = st.text_input("Nome do Cliente")
    email = st.text_input("E-mail do Cliente")
    produtos = st.text_area("Descrição dos Produtos")
    total = st.text_input("Total (R$)")
    enviado = st.form_submit_button("Enviar Pedido")

if enviado:
    if cliente and email and produtos and total:
        pdf_buffer = gerar_pdf(cliente, produtos, total)
        resultado = enviar_email(email, cliente, pdf_buffer)
        st.success(resultado)
    else:
        st.error("Por favor, preencha todos os campos.")
