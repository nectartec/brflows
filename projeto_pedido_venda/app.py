import streamlit as st
import sqlite3
import io
from reportlab.pdfgen import canvas
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication

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

# Função para gerar o PDF
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

# Função para enviar e-mail com o PDF anexado
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

# Interface do Streamlit
st.title("Gerador de Pedido de Venda")

# Formulário para entrada do ID do pedido
with st.form("pedido_form"):
    pedido_id = st.text_input("ID do Pedido")    
    cliente = st.text_input("Nome do Cliente")
    email = st.text_input("E-mail do Cliente") 
    enviado = st.form_submit_button("Buscar Pedido e Enviar")

# Processa os dados ao clicar em buscar e enviar
if enviado:
    if pedido_id:
        pedido = buscar_pedido(pedido_id)
        if pedido:
            cliente, email, produtos, total = pedido
            pdf_buffer = gerar_pdf(cliente, produtos, total)
            resultado = enviar_email(email, cliente, pdf_buffer)
            st.success(resultado)
        else:
            st.error("Pedido não encontrado.")
    else:
        st.error("Por favor, insira o ID do pedido.")
