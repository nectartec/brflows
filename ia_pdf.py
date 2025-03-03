import os
import time
import datetime
import pythoncom
import win32com.client
import logging
import io
import psycopg2
from psycopg2 import sql
import pdfplumber
import openai
import json
from dotenv import load_dotenv
 
# Import para OCR
from pdf2image import convert_from_path
from PIL import Image
import pytesseract
 
# Carregar variáveis de ambiente (se necessário)
load_dotenv()
 
# Configuração de logging
logging.basicConfig(
    filename='outlook_nfse_processor.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
 
# Define a chave de API do OpenAI
openai.api_key = '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'
 
# Se necessário, configure também a sua GEMINI_API_KEY
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "AIzaSyA6t16a4JyKSSBU0Bu7ttweGTl3PstnnqQ")
 
# Configuração do Tesseract
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
os.environ["TESSDATA_PREFIX"] = r"C:\Program Files\Tesseract-OCR\tessdata"
 
print("API Key do OpenAI configurada.")
 
# Limite de notas a serem processadas nesta execução
LIMITE_NOTAS = 20000000000000
print(f"Limite de notas definido: {LIMITE_NOTAS}")
 
# Configurações do banco de dados (ajuste conforme seu ambiente)
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_NAME = os.getenv("DB_NAME", "nfsedb")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "admin")
DB_PORT = os.getenv("DB_PORT", 5432)
print("Configurações do banco de dados carregadas.")
 
# Variáveis de controle para chamadas à API
gpt_calls = 0
start_time = time.time()
 
# ====================== FUNÇÕES DE CONEXÃO COM O BD ======================
def conectar_bd():
    """
    Conecta ao banco de dados PostgreSQL.
    """
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            port=DB_PORT
        )
        logging.info("Conexão com o banco de dados estabelecida com sucesso.")
        print("Conexão com o BD estabelecida.")
        return conn
    except Exception as e:
        logging.error(f"Erro ao conectar ao banco de dados: {e}")
        print(f"Erro ao conectar ao BD: {e}")
        raise
 
def salvar_arquivo_no_bd(nome_arquivo, arquivo_bytes):
    """
    Insere o anexo no BD na tabela nfse com status ARQUIVO_RECEBIDO.
    A tabela deve ter colunas (nfse_id SERIAL, nome_arquivo TEXT, arquivo BYTEA, status TEXT).
    """
    print(f"Salvando arquivo no BD: {nome_arquivo}")
    conn = conectar_bd()
    try:
        with conn.cursor() as cursor:
            insert_query = sql.SQL("""
                INSERT INTO nfse (nome_arquivo, arquivo, departamento_id, status)
                VALUES (%s, %s, 1, %s)
                RETURNING nfse_id;
            """)
            cursor.execute(insert_query, (nome_arquivo, psycopg2.Binary(arquivo_bytes), 'ARQUIVO_RECEBIDO'))
            nfse_id = cursor.fetchone()[0]
        conn.commit()
        logging.info(f"Arquivo {nome_arquivo} salvo no BD com nfse_id {nfse_id}.")
        print(f"Arquivo {nome_arquivo} salvo com nfse_id {nfse_id}.")
        return nfse_id
    except Exception as e:
        logging.error(f"Erro ao salvar arquivo {nome_arquivo} no BD: {e}")
        print(f"Erro ao salvar arquivo {nome_arquivo} no BD: {e}")
    finally:
        conn.close()
 
# ====================== FUNÇÕES DE EXTRAÇÃO DE TEXTO DO PDF ======================
def extrair_texto_de_pdf(caminho_pdf):
    """
    Tenta extrair o texto do PDF utilizando pdfplumber.
    Caso não haja texto (PDF em imagem), utiliza OCR para extrair o texto.
    """
    print(f"Iniciando extração de texto do PDF: {caminho_pdf}")
    try:
        with pdfplumber.open(caminho_pdf) as pdf:
            texto_completo = ""
            for pagina in pdf.pages:
                texto = pagina.extract_text()
                if texto:
                    texto_completo += texto + "\n"
            texto_extraido = texto_completo.strip()
            if texto_extraido:
                print("Extração de texto concluída com pdfplumber.")
                return texto_extraido
            else:
                print("Nenhum texto encontrado com pdfplumber, iniciando OCR.")
                return extrair_texto_com_ocr(caminho_pdf)
    except Exception as e:
        logging.error(f"Erro ao extrair texto do PDF {caminho_pdf}: {e}")
        print(f"Erro na extração do PDF {caminho_pdf}: {e}")
        return ""
 
def extrair_texto_com_ocr(caminho_pdf):
    """
    Converte o PDF em imagens e usa pytesseract para extrair o texto.
    Ajuste o poppler_path se necessário.
    """
    print(f"Iniciando extração OCR para {caminho_pdf}.")
    try:
        poppler_path = r"C:\Users\roger.oliveira\Downloads\Release-24.08.0-0\poppler-24.08.0\Library\bin"  # Exemplo; ajuste se necessário
        imagens = convert_from_path(caminho_pdf, dpi=300, poppler_path=poppler_path)
        texto_total = ""
        for imagem in imagens:
            texto = pytesseract.image_to_string(imagem, lang='por')
            texto_total += texto + "\n"
        texto_total = texto_total.strip()
        print("Extração OCR concluída.")
        return texto_total
    except Exception as e:
        logging.error(f"Erro ao extrair texto via OCR do PDF {caminho_pdf}: {e}")
        print(f"Erro na extração OCR do PDF {caminho_pdf}: {e}")
        return ""
 
# ====================== FUNÇÕES DE CONTROLE DE REQUISIÇÕES ======================
def controle_limite_requisicoes():
    """
    Controla o limite de chamadas à API (ex.: 15 RPM para GPT-4, ou outro modelo com limites diferentes).
    """
    global gpt_calls, start_time
    if gpt_calls >= 500:
        elapsed_time = time.time() - start_time
        if elapsed_time < 60:
            wait_time = 60 - elapsed_time
            logging.info(f"Limite de 15 RPM atingido. Aguardando {wait_time:.2f} segundos.")
            print(f"Aguardando {wait_time:.2f} segundos devido ao limite de chamadas.")
            time.sleep(wait_time)
        gpt_calls = 0
        start_time = time.time()
 
# ====================== FUNÇÕES DE CLASSIFICAÇÃO (EM LOTE) ======================
def classificar_documento_em_lote(lista_textos, max_retries=3):
    """
    Envia os textos dos documentos para a API GPT-4 para classificação.
    A resposta deverá ser um JSON no formato:
      { "Documento 1": "Sim" ou "Não", "Documento 2": "Sim" ou "Não", ... }
    """
    global gpt_calls, start_time
    prompt = (
        "Você recebeu textos de documentos fiscais. Para cada documento, responda apenas com 'Sim' ou 'Não' "
        "se o documento é uma Nota Fiscal de Serviços Eletrônica (NFS-e). "
        "Retorne um JSON válido, exclusivamente no seguinte formato (sem texto extra):\n\n"
        "{\n"
        "  \"Documento 1\": \"Sim\" ou \"Não\",\n"
        "  \"Documento 2\": \"Sim\" ou \"Não\",\n"
        "  ...\n"
        "}\n\n"
        "IMPORTANTE:\n"
        "- Não retorne códigos de formatação ou texto fora do JSON.\n"
        "- Se não tiver certeza, responda \"Não\". O JSON deve ser 100% parseável.\n\n"
    )
    conteudo = "\n\n".join([f"Documento {i+1}:\n{texto}" for i, texto in enumerate(lista_textos)])
    prompt += conteudo
    print("Enviando prompt para classificação (gpt-4).")
    logging.info(f"Prompt enviado (primeiros 200 caracteres): {prompt[:200]}")
    retries = 0
    while retries < max_retries:
        controle_limite_requisicoes()
        try:
            response = openai.ChatCompletion.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}]
            )
            gpt_calls += 1
            classificacoes_str = response['choices'][0]['message']['content'].strip()
            if classificacoes_str.startswith("```") and classificacoes_str.endswith("```"):
                classificacoes_str = classificacoes_str.strip("```").strip()
            print("Resposta da API (gpt-4) recebida.")
            logging.info("Resposta da API (gpt-4) recebida.")
            return json.loads(classificacoes_str)
        except openai.RateLimitError as e:
            logging.warning(f"Limite de requisição atingido: {e}. Tentando novamente em 60 segundos.")
            print("Limite de requisição atingido (gpt-4). Aguardando 60 segundos...")
            time.sleep(60)
            retries += 1
        except json.JSONDecodeError as e:
            logging.error(f"Erro ao decodificar JSON: {e}")
            print(f"Erro ao decodificar JSON: {e}")
            return {}
        except Exception as e:
            logging.error(f"Erro na classificação (gpt-4) em lote: {e}")
            print(f"Erro na classificação em lote com gpt-4: {e}")
            return {}
    logging.error("Falha na classificação em lote após múltiplas tentativas (gpt-4).")
    print("Falha na classificação em lote após múltiplas tentativas (gpt-4).")
    return {}
 
# ====================== FUNÇÃO PARA PROCESSAR O LOTE ======================
def processar_lote(lote_textos, lote_arquivos, total_nfse_salvos):
    """
    Processa o lote de anexos: classifica com GPT-4 e salva os que forem "Sim" no BD.
    Remove os arquivos temporários.
    Retorna a quantidade atualizada de notas NFSe salvas.
    """
    print("Processando lote de anexos (gpt-4).")
    classificacoes = classificar_documento_em_lote(lote_textos)
    for idx, (nome_arq, arq_bytes, temp_arq) in enumerate(lote_arquivos):
        key = f"Documento {idx+1}"
        resultado = classificacoes.get(key, "").strip().lower()
        print(f"Classificação para {nome_arq} ({key}): {resultado}")
        logging.info(f"Classificação para {nome_arq} ({key}): {resultado}")
        if resultado == "sim":
            if total_nfse_salvos < LIMITE_NOTAS:
                salvar_arquivo_no_bd(nome_arq, arq_bytes)
                total_nfse_salvos += 1
                print(f"Arquivo {nome_arq} salvo no BD.")
            else:
                logging.info("Limite de 200 notas atingido; não serão salvos mais arquivos.")
                print("Limite de 200 notas atingido; interrompendo salvamento.")
        else:
            logging.info(f"Arquivo {nome_arq} não foi classificado como NFSe.")
            print(f"Arquivo {nome_arq} descartado (não NFSe).")
        if os.path.exists(temp_arq):
            os.remove(temp_arq)
            print(f"Arquivo temporário {temp_arq} removido.")
    return total_nfse_salvos
 
# ====================== FUNÇÃO PRINCIPAL DE PROCESSAMENTO DE E-MAILS ======================
def processar_emails_nfse(log_label_execution):
    """
    Conecta ao Outlook, lê os e-mails não lidos e processa seus anexos PDF.
    Extrai texto com pdfplumber ou OCR, envia para GPT-4 em lotes de 5 e, se classificado como NFSe, salva no BD.
    Retorna as métricas:
      - emails_lidos: quantidade de e-mails processados
      - anexos_recebidos: quantidade de anexos PDF recebidos
      - notas_identificadas: quantidade de notas NFSe (anexos classificados e salvos)
    """
    print("Iniciando processamento de e-mails NFSe.")
    total_emails_lidos = 0
    total_nfse_salvos = 0
    total_anexos_recebidos = 0
 
    lote_textos = []
    lote_arquivos = []
 
    try:
        pythoncom.CoInitialize()
        outlook = win32com.client.Dispatch("Outlook.Application").GetNamespace("MAPI")
        inbox = outlook.GetDefaultFolder(6)  # Pasta Inbox
        messages = inbox.Items.Restrict("[UnRead] = True")
        messages.Sort("[ReceivedTime]", True)
 
        count = messages.Count
        logging.info(f"Iniciando processamento de {count} e-mails não lidos.")
        print(f"Iniciando processamento de {count} e-mails não lidos.")
 
        for i in range(count, 0, -1):
            try:
                mail = messages.Item(i)
                print(f"Processando e-mail {i}.")
                logging.info(f"E-mail {i} - To: {mail.To} | CC: {mail.CC}")
 
                total_emails_lidos += 1
                logging.info(f"E-mail {i} processando.")
 
                attachments = mail.Attachments
                for j in range(1, attachments.Count + 1):
                    attachment = attachments.Item(j)
                    if attachment.FileName.lower().endswith('.pdf'):
                        total_anexos_recebidos += 1
                        temp_path = os.path.join(os.environ.get("TEMP", "C:\\Temp"), attachment.FileName)
                        print(f"Salvando anexo {attachment.FileName} em {temp_path}.")
                        attachment.SaveAsFile(temp_path)
                        texto = extrair_texto_de_pdf(temp_path)
                        print(f"Texto extraído de {attachment.FileName} (primeiros 100 caracteres): {texto[:100]}")
                        logging.info(f"Texto extraído de {attachment.FileName} (primeiros 100 caracteres): {texto[:100]}")
                        lote_textos.append(texto)
                        with open(temp_path, "rb") as f:
                            arquivo_bytes = f.read()
                        lote_arquivos.append((attachment.FileName, arquivo_bytes, temp_path))
 
                        # Quando atingir 5 anexos, processa o lote com GPT-4
                        if len(lote_textos) == 5:
                            print("Lote de 5 anexos completo. Processando lote (gpt-4).")
                            total_nfse_salvos = processar_lote(lote_textos, lote_arquivos, total_nfse_salvos)
                            lote_textos = []
                            lote_arquivos = []
 
                        if total_nfse_salvos >= LIMITE_NOTAS:
                            print("Limite total de notas atingido. Interrompendo processamento.")
                            logging.info("Limite total de notas atingido; interrompendo processamento.")
                            break
 
                mail.UnRead = False
                mail.Save()
                print(f"E-mail {i} marcado como lido.")
 
                if total_nfse_salvos >= LIMITE_NOTAS:
                    break
 
            except Exception as e:
                logging.error(f"Erro ao processar o e-mail {i}: {e}")
                print(f"Erro ao processar o e-mail {i}: {e}")
 
        # Processa eventual lote remanescente
        if lote_textos:
            print("Processando lote remanescente (gpt-4).")
            total_nfse_salvos = processar_lote(lote_textos, lote_arquivos, total_nfse_salvos)
 
        logging.info("Processamento de e-mails concluído.")
        print("Processamento de e-mails concluído.")
    except Exception as e:
        logging.critical(f"Erro crítico no processamento de e-mails: {e}")
        print(f"Erro crítico no processamento de e-mails: {e}")
    finally:
        pythoncom.CoUninitialize()
 
    return {
        "emails_lidos": total_emails_lidos,
        "anexos_recebidos": total_anexos_recebidos,
        "notas_identificadas": total_nfse_salvos
    }
 
# ====================== FUNÇÃO MAIN ======================
def main():
    log_label_execution = ''
    resultados = processar_emails_nfse(log_label_execution)
    print("Resultados do processamento:", resultados)

    print("Tarefa finalizada.")
 
if __name__ == "__main__":
    main()