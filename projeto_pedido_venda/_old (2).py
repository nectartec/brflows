import streamlit as st
import io
import pyodbc
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.utils import ImageReader
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from email.mime.application import MIMEApplication
import os
import socket
# Configurações de E-mail
SMTP_SERVER = "smtp.office365.com"
SMTP_PORT = 587
EMAIL_USER = "naoresponda@cromus.com.br"
EMAIL_PASS = "6zPSGENLW!95"

# Função para buscar os dados do pedido
def buscar_pedido(pedido_id):
    # Configurações de conexão
    #192.168.8.165
    # Obtém o nome do host
    #hostname = socket.gethostname()
    # Obtém o endereço IP associado ao hostname
    #ip_address = socket.gethostbyname(hostname)
    #st.success(ip_address) 
    server   = '172.16.0.1\SQLEXPRESS'
    database = 'SAFV_3090'
    username = 'sa'
    password = 'fenix' 
    # String de conexão
    conn_str = f'DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={server};DATABASE={database};UID={username};PWD={password}'
    # Criando a conexão
    conn = pyodbc.connect(conn_str)
    cursor = conn.cursor()
    query = """
    SELECT 
        mp.SUBTOTAL,
        mp.DESC_FINANCEIRO,
        mp.VLRDESC_FINANCEIRO,
        mp.TOTAL,
        mp.PEDIDO,
        cc.CODIGO,
        cc.NOME AS NOME_CLIENTE,
        cc.ENDERECO,
        cc.CIDADE,
        cc.CEP,
        cc.CNPJ,
        cc.INSCRICAO_EST,
        cc.TELEFONE,
        cc.EMAIL,
        cc.FAX,
        cc.TRANSPORTADORA,
        mp.INICIO,
        mp.REPRESENTANTE,
        cr.NOME AS NOME_REPRESENTANTE,
        cnd.NOME AS NOME_CONDICAO
    FROM MOV_PEDIDO mp
    JOIN CAD_CLIENTES cc ON mp.CLIENTE = cc.CODIGO
    JOIN CAD_REPRESENTANTES cr ON mp.REPRESENTANTE = cr.CODIGO
    JOIN CAD_CONDICOES cnd ON mp.CONDICAO = cnd.CODIGO 
    WHERE mp.PEDIDO = ?
    """
    cursor.execute(query, (pedido_id,))
    pedido = cursor.fetchone()
    conn.close()
    return pedido
# Função para buscar os dados do pedido
def buscar_item_pedido(pedido_id):
    # Configurações de conexão
    server   = '172.16.0.1\SQLEXPRESS'
    database = 'SAFV_3090'
    username = 'sa'
    password = 'fenix' 
    # String de conexão
    conn_str = f'DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={server};DATABASE={database};UID={username};PWD={password}'
    # Criando a conexão
    conn = pyodbc.connect(conn_str)
    cursor = conn.cursor()
    query = """
    SELECT 
        MOV_ITPEDIDO.PRODUTO AS PRODUTO,
        CAD_PRODUTO.DESCRICAO AS DESCRICAO,
        REPLACE(CONVERT(VARCHAR, CAST(MOV_ITPEDIDO.QTD AS DECIMAL(9,0))), '.', ',') AS Qt_Ped,
        REPLACE(CONVERT(VARCHAR, CAST(MOV_ITPEDIDO.PRECO AS DECIMAL(9,2))), '.', ',') AS Vl_Unit,
        REPLACE(CONVERT(VARCHAR, CAST(MOV_ITPEDIDO.TOTAL AS DECIMAL(9,2))), '.', ',') AS Vl_TOTAL,
        FORMAT(CAST(MOV_ITPEDIDO.IPI AS DECIMAL(9,2)), 'N2', 'pt-BR') AS IPI,
        FORMAT(CAST(MOV_ITPEDIDO.VALOR_IPI AS DECIMAL(9,2)), 'N2', 'pt-BR') AS VALOR_IPI
    FROM MOV_ITPEDIDO
    JOIN CAD_PRODUTO ON MOV_ITPEDIDO.PRODUTO = CAD_PRODUTO.CODIGO
    WHERE MOV_ITPEDIDO.PEDIDO  = ?
    """
    cursor.execute(query, (pedido_id,))
    item_pedido = cursor.fetchall()  # Retorna todas as linhas
    conn.close()
    return item_pedido
# Função para gerar o PDF
def gerar_pdf(nr_pedido, codigo_cli, nome_cli, ender,
              nom_cidade, cep, cnpj, inscrEst,
              Telefone, Email, Fax, Transportadora,
              NomeRepresentante, Inicio, NomeCondicao,
              vlTOTAL, Subtotal, DescontoFinanceiro,
              ValorDesconto, observacao):
    pdf_buffer = io.BytesIO()
    c = canvas.Canvas(pdf_buffer)
    # Configurando fonte em negrito (Helvetica-Bold) e tamanho
    c.setFont("Helvetica-Bold", 12)
    c.drawString(20, 800, f"Cromus Embalagens Ind. e Com. Ltda")
    c.drawString(500,800, f"Pedido: {nr_pedido}")
    # Configurando fonte (Helvetica) e tamanho
    c.setFont("Helvetica", 10)
    c.drawString(20, 780, f"Rua Alpont, 320 - Capuava")
    c.drawString(20, 760, f"Maua - SP - 09380-115")
    c.drawString(20, 740, f"Fone: (11) 4514-8000 Fax: (11) 4514-8054")
    c.drawString(20, 720, f"cromus@cromus.com.br")
    c.drawString(20, 700, f"www.cromus.com.br")


    c.setFont("Helvetica-Bold", 12)
    c.drawString(20, 680, f"Comprador")
    c.setFont("Helvetica", 10)
    c.drawString(20,660, f"{codigo_cli} - {nome_cli}") 
    c.drawString(20,640, f"{ender} - {nom_cidade} - {cep}")  
    c.drawString(20,620, f"CNPJ: {cnpj} Insc. Est.: {inscrEst}")
    c.drawString(20,600, f"Fone: {Telefone} Email: {Email}")  
    c.drawString(20,580, f"Fax: {Fax} Transportadora: {Transportadora}")    
    c.drawString(20,560, f"Data: {Inicio} Representante: {NomeRepresentante}") 
    c.drawString(20,540, f"Condição de Pagamento: {NomeCondicao}")         
    
    c.setFont("Helvetica-Bold", 12) 
    c.drawString(20, 520, f"Itens do Pedido")
     
    c.setFont("Helvetica", 10)   
    largura, altura = letter
    # Define posições iniciais
    x_inicial = 10
    y_inicial = altura - 300
    linha_print = y_inicial 
    largura_colunas = [80, 80, 80, 50, 80, 80, 50, 50]  # Tamanhos das colunas
    
    item_pedido = buscar_item_pedido(pedido_id)
    #st.success(item_pedido) 
    # Definir o cabeçalho da tabela
    dados = [
        ["Imagem", "Produto", "Descrição", "Qnt", "Preço Uni.", "Total", "IPI", "Valor IPI"]
    ]
     
    # Converte o retorno em uma lista, seja único ou múltiplo
    if isinstance(item_pedido, pyodbc.Row):
        item_pedido_lista = [list(item_pedido)]  # Apenas um registro
    else:
        item_pedido_lista = [list(row) for row in item_pedido]  # Vários registros
        
    
    # Verifica se é uma lista válida
    if isinstance(item_pedido_lista, list):
        for item in item_pedido_lista:
            if isinstance(item, (list, tuple)) and len(item) >= 7:
                # Nome da imagem com base no nome do produto
                
                dados.append([
                    " ",                   # imagem
                    item[0],               # Produto
                    item[1],               # Descrição
                    item[2],               # Quantidade
                    f"R$ {item[3]}",       # Preço Unitário
                    f"R$ {item[4]}",       # Total
                    item[5],               # IPI
                    item[6]                # Valor IPI
                ])
            else:
                st.warning(f"Item inválido ou com elementos insuficientes: {item}")
    else:
        st.error("Nenhum item encontrado ou formato inválido.")
  # Função para desenhar a borda da célula
    def desenhar_celula(x, y, largura, altura, texto="", imagem=False, caminho_imagem=None):
        c.rect(x, y - altura, largura, altura, stroke=1, fill=0)  # Ajuste para alinhar com a altura
        if texto:
            # Centraliza verticalmente o texto
            texto_y = y - altura / 2 + 5
            c.drawString(x + 5, texto_y, texto)
        elif imagem and caminho_imagem:
            # Desenha a imagem se existir
            try:
                img = ImageReader(caminho_imagem)
                c.drawImage(
                    img,
                    x + 5,  # Margem horizontal
                    y - altura + 5,  # Margem vertical
                    largura - 10,  # Ajuste para largura da célula
                    altura - 10,  # Ajuste para altura da célula
                    preserveAspectRatio=True,
                    anchor='c',
                )
            except Exception as e:
                c.drawString(x + 5, y - altura + 15, "Erro Img")

    # Desenha a tabela
    y = y_inicial
    for linha_index, linha in enumerate(dados):
        x = x_inicial
        altura_celula = 50 if linha_index > 0 else 30  # Altura maior para linhas com imagens

        # Verifica se ainda cabe na página antes de desenhar a próxima linha
        if y - altura_celula < 50:
            c.showPage()  # Adiciona uma nova página
            c.setFont("Helvetica", 10)
            y = altura - 50  # Reinicia o valor de y no topo da nova página

        for coluna_index, item in enumerate(linha):
            if coluna_index == 0 and linha_index > 0:  # Primeira coluna: imagem
                caminho_imagem = os.path.join("imagem", f"{linha[1]}.jpg")
                if os.path.exists(caminho_imagem):
                    desenhar_celula(x, y, largura_colunas[coluna_index], altura_celula, imagem=True, caminho_imagem=caminho_imagem)
                else:
                    desenhar_celula(x, y, largura_colunas[coluna_index], altura_celula, texto="Sem Imagem")
            else:  # Outras colunas: texto
                desenhar_celula(x, y, largura_colunas[coluna_index], altura_celula, texto=str(item))

            x += largura_colunas[coluna_index]  # Move para a próxima coluna

        # Move para a próxima linha
        y -= altura_celula

  
       
    linha_print = y - 240
    c.drawString(20, linha_print + 210, f"Prezado cliente,")
    c.drawString(20, linha_print + 200, f"Para que possamos dar continuidade ao seu pedido será necessário o")
    c.drawString(20, linha_print + 190, f"envio das documentações para análise de crédito: Requerimento")
    c.drawString(20, linha_print + 180, f"de Empresário, Contrato Social ou Ata, Comprovante de endereço da")
    c.drawString(20, linha_print + 170, f"empresa, Informações comerciais e bancárias. Pedido sujeito à")
    c.drawString(20, linha_print + 160, f"aprovação. Entre em contato (11) 4514-8052 Email: credito@cromus.com.br")
        
        
    c.drawString(470, linha_print + 200, f"Subtotal: R$ {Subtotal}")     
    c.drawString(470, linha_print + 190, f"{DescontoFinanceiro} - Desconto Financeiro: {ValorDesconto}")
    c.drawString(470, linha_print + 180, f"Total: R$ {vlTOTAL}")
    
    c.setFont("Helvetica-Bold", 12) 
    c.drawString(20,linha_print + 130 , f"TIPO DE FRETE:")
    c.setFont("Helvetica", 10)
    c.drawString(20,linha_print + 100 , f"|_| CIF |_| FOB")
    
    c.drawString(20,linha_print + 80 , f"Regiões S / SE / CO : 6%")
    c.drawString(20,linha_print + 70 , f"Regiões N / NE : 9%")
    
    c.drawString(20,linha_print + 50 , f"Nome Legível: _______________________________________________________")
    c.drawString(20,linha_print + 40 , f"Assinatura: _________________________________________________________")
    c.drawString(20,linha_print + 30 , f"Vendedor: ___________________________________________________________")
    
    c.save()
    pdf_buffer.seek(0)
    return pdf_buffer

# Função para enviar o e-mail com o PDF anexado
def enviar_email(destinatario, pedido, pdf_buffer):
    msg = MIMEMultipart()
    msg["From"] = EMAIL_USER
    msg["To"] = destinatario
    msg["Subject"] = "Pedido de Venda"

   # Corpo do e-mail em texto e HTML
    body = (
        "Olá,<br>"
        "Esse é o seu pedido realizado no Open House da Cromus.<br>"
        "A novidade é que você consegue visualizar todos os itens através das fotos que incluímos no pedido.<br>"
        "Lembrando que os preços do Open House foram elaborados considerando o valor do dólar de 5,80.<br>"
        "Havendo variações do dólar para abaixo de 5,80 ou acima de 6,20, os preços poderão sofrer reajustes.<br>"
        "Observação: Consideraremos o valor do dólar de 15/06/2025.<br>"
        "Estamos felizes em fazer parte do seu Natal 2025.<br>"
        "Obrigado pela presença em nosso evento!<br><br>"  
        f"<strong>Observação:</strong> {observacao}<br><br>"  # Inclusão da observação
        '<img src="cid:logo_Email.jpeg" alt="Imagem do Pedido" style="width:300px;"><br>'
    )
    parte_html = MIMEText(body, "html")
    msg.attach(parte_html)
    # Adiciona a imagem ao e-mail
    with open("logo_Email.jpeg", "rb") as img_file:  # Substitua pelo caminho correto da sua imagem
        img = MIMEImage(img_file.read())
        img.add_header("Content-ID", "<logo_Email>")
        img.add_header("Content-Disposition", "inline", filename="logo_Email.jpeg")
        msg.attach(img) 
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

# Initialize session state for keys
for key in ["pedido_id", "cliente", "email"]:
    if key not in st.session_state:
        st.session_state[key] = ""

def buscar_e_atualizar_pedido():
    pedido_id = st.session_state["pedido_id"]
    if pedido_id:
        pedido = buscar_pedido(pedido_id)
        st.session_state["cliente"] = pedido[6]
        st.session_state["email"] = pedido[13] 


# Campo fora do formulário para capturar o ID do Pedido
pedido_id = st.text_input(
    "ID do Pedido",
    value=st.session_state["pedido_id"],
    key="pedido_id",
    on_change=buscar_e_atualizar_pedido,  # Callback ao alterar o pedido_id
)
# Form to collect and edit data
with st.form("pedido_form"):
    # Widgets inside the form reference only `key`, no need for `value`
    st.text_input("Nome do Cliente", key="cliente")
    email = st.text_input("E-mail do Cliente", key="email")
    observacao = st.text_area("Observação")
    enviado = st.form_submit_button("Enviar Pedido")
    
 
        
if enviado:
    if pedido_id:
        pedido= buscar_pedido(pedido_id)
        if pedido:           
            Subtotal           = pedido[0]
            DescontoFinanceiro = pedido[1]
            ValorDesconto      = pedido[2]
            vlTOTAL    = pedido[3]
            nr_pedido  = pedido[4] 
            codigo_cli = pedido[5]
            nome_cli   = pedido[6]
            ender      = pedido[7]
            nom_cidade = pedido[8]
            cep        = pedido[9]
            cnpj       = pedido[10]
            inscrEst   = pedido[11]
            Telefone   = pedido[12]
            Email      = pedido[13]
            Fax        = pedido[14]
            Transportadora    = pedido[15] 
            NomeRepresentante = pedido[16] 
            Inicio            = pedido[17]
            NomeCondicao      = pedido[18]
            #observacao = observacao
            pdf_buffer = gerar_pdf(nr_pedido, codigo_cli, nome_cli, ender, nom_cidade, cep,
                                   cnpj, inscrEst, Telefone, Email, Fax, Transportadora,
                                   NomeRepresentante, Inicio, NomeCondicao,
                                   vlTOTAL, Subtotal, DescontoFinanceiro, ValorDesconto, observacao)
            resultado = enviar_email(email, pedido, pdf_buffer)
            st.success(resultado)
        else:
            st.error("Pedido não encontrado.")
    else:
        st.error("Por favor, insira o ID do pedido.")