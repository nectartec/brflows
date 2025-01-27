import os
import psycopg2
from psycopg2 import sql
from psycopg2.extras import RealDictCursor
from pdf2image import convert_from_bytes
from PIL import Image
import google.generativeai as genai
import json
from dotenv import load_dotenv
import tempfile
import logging

# Configuração de Logs
logging.basicConfig(
    filename='processar_nfse.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Carregar variáveis de ambiente do arquivo .env
load_dotenv()

# ***CONFIGURAÇÃO***
# Carregar credenciais do .env
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_NAME = os.getenv("DB_NAME", "nfsedb")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "admin")
DB_PORT = os.getenv("DB_PORT", 5432)
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "AIzaSyA6t16a4JyKSSBU0Bu7ttweGTl3PstnnqQ")

# Configurar a API do Gemini
genai.configure(api_key=GEMINI_API_KEY)

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
        print("CONECTOU AO BD")
        return conn
    except Exception as e:
        logging.error(f"Erro ao conectar ao banco de dados: {e}")
        print(f"Erro ao conectar ao banco de dados: {e}")
        raise

def extrair_info_nfse(image_path):
    """
    Envia a imagem para a API do Gemini e extrai informações da NFSE.
    """
    try:
        # Abre a imagem com PIL e converte para RGB (se necessário)
        img = Image.open(image_path).convert("RGB")

        # Define o prompt
        prompt = """
        Extraia as informações desta nota fiscal de serviços eletrônica. 
        Seja preciso e completo. Inclua:
        * Número da nota
        * Data e hora de emissão
        * Data de vencimento
        * Dados do prestador (CNPJ, nome/razão social, endereço)
        * Dados do tomador (CNPJ, nome/razão social, endereço, e-mail)
        * Descrição dos serviços
        * Valor total do serviço

        Formate a resposta em JSON, NÃO UTILIZE blocos de codigo Markdown (```, ´´´). Ou seja, devolva apenas um JSON, usando as chaves em português, no schema abaixo:
        Tenha total atenção nas unidades de medidas, bem como separadores de milhares utilizados de exemplos no pseudo-json abaixo, principalmente em valores numéricos, sempre use um formato aceitavel no BD do Postgres como resposta.
        {
            "numero_nota": "xxxx",
            "data_emissao": "dd/mm/yyyy",
            "data_vencimento": "dd/mm/yyyy",
            "prestador": {
                "cnpj": "xxx",
                "nome_razao_social": "xxx",
                "endereco": "xxx",
                "municipio": "xxx",
                "inscricao_municipal": "xxx",
                "uf": "xx"
            },
            "tomador": {
                "cnpj": "xxxx",
                "nome_razao_social": "xxxx",
                "endereco": "xxx",
                "municipio": "xxx",
                "uf": "xx",
                "email": "xxxx",
                "inscricao_municipal": "xxxx"
            },
            "data_emissao_nf": "dd/mm/aaaa",
            "valor_total": "xxxx,xx"
        }
        """

        # Escolhe o modelo Gemini Pro Vision
        model = genai.GenerativeModel(model_name="gemini-1.5-flash-8b")

        # Faz a requisição
        response = model.generate_content([prompt, img])

        if response.text:
            return response.text
        else:
            logging.warning("Nenhuma resposta válida retornada pela API do Gemini.")
            print("Nenhuma resposta válida retornada pela API do Gemini.")
            return None

    except FileNotFoundError:
        logging.error("Erro: Arquivo de imagem não encontrado.")
        print("Erro: Arquivo de imagem não encontrado.")
        return None
    except Exception as e:
        logging.error(f"Erro inesperado ao extrair informações da NFSE: {e}")
        print(f"Erro inesperado ao extrair informações da NFSE: {e}")
        return None

def processar_nfse(conn, nfse_raw):
    """
    Processa uma NFSE: converte PDF para JPG, extrai dados, popula a tabela nfse e atualiza status.
    """
    nfse_id = nfse_raw['nfse_id']
    nome_arquivo = nfse_raw['nome_arquivo']
    arquivo_bytes = nfse_raw['arquivo']

    logging.info(f"Iniciando processamento da NFSE ID: {nfse_id}, Arquivo: {nome_arquivo}")
    print(f"Iniciando processamento da NFSE ID: {nfse_id}, Arquivo: {nome_arquivo}")

    if not arquivo_bytes:
        logging.warning(f"NFSE ID {nfse_id} possui 'arquivo' nulo. Pulando.")
        print(f"NFSE ID {nfse_id} possui 'arquivo' nulo. Pulando.")
        return

    try:
        # Especifique o caminho para o Poppler
        poppler_path = r"C:\Users\roger.oliveira\Downloads\Release-24.08.0-0\poppler-24.08.0\Library\bin"  # Atualize conforme sua instalação

        # Converter PDF para JPG usando pdf2image
        imagens = convert_from_bytes(arquivo_bytes, fmt='jpeg', poppler_path=poppler_path)

        if not imagens:
            logging.warning(f"Nenhuma imagem extraída do arquivo '{nome_arquivo}'.")
            print(f"Nenhuma imagem extraída do arquivo '{nome_arquivo}'.")
            return

        # Salvar a primeira página como JPG temporariamente
        with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as temp_img:
            imagens[0].save(temp_img.name, 'JPEG')
            temp_img_path = temp_img.name

        logging.info(f"Arquivo '{nome_arquivo}' convertido para JPG: {temp_img_path}")
        print(f"Arquivo '{nome_arquivo}' convertido para JPG: {temp_img_path}")

        # Extrair informações usando a API do Gemini
        resultado = extrair_info_nfse(temp_img_path)

        # Remover o arquivo temporário
        os.remove(temp_img_path)

        if not resultado:
            logging.warning(f"Extração de informações falhou para o arquivo '{nome_arquivo}'.")
            print(f"Extração de informações falhou para o arquivo '{nome_arquivo}'.")
            return

        # Parsear o JSON retornado
        try:
            print("RESULTADO")
            resultado = resultado.replace("```json", "").replace("```", "")
            print(resultado)
            dados_nfse = json.loads(resultado)
            logging.info(f"Dados extraídos para a NFSE ID {nfse_id}: {dados_nfse}")
            print(f"Dados extraídos para a NFSE ID {nfse_id}: {dados_nfse}")
        except json.JSONDecodeError:
            logging.error(f"Erro ao decodificar o JSON retornado pela API para o arquivo '{nome_arquivo}': {resultado}")
            print(f"Erro ao decodificar o JSON retornado pela API para o arquivo '{nome_arquivo}'.")
            return

        # Atualizar os dados extraídos e o status na tabela nfse
        with conn.cursor() as cursor:
            update_query = sql.SQL("""
                UPDATE nfse
                SET 
                    numero_nota = %s,
                    data_emissao = TO_DATE(%s, 'DD/MM/YYYY'),
                    data_de_vencimento = TO_DATE(%s, 'DD/MM/YYYY'),
                    cnpj_prestador = %s,
                    nome_razao_social_prestador = %s,
                    endereco_prestador = %s,
                    municipio_prestador = %s,
                    inscricao_municipal_prestador = %s,
                    uf_prestador = %s,
                    cnpj_tomador = %s,
                    nome_razao_social_tomador = %s,
                    endereco_tomador = %s,
                    municipio_tomador = %s,
                    inscricao_municipal_tomador = %s,
                    uf_tomador = %s,
                    email_tomador = %s,
                    data_emissao_nf = TO_DATE(%s, 'DD/MM/YYYY'),
                    valor_total = %s,
                    status = %s,
                    updated_at = NOW()
                WHERE nfse_id = %s;
            """)

            cursor.execute(update_query, (
                dados_nfse.get('numero_nota'),
                dados_nfse.get('data_emissao'),
                dados_nfse.get('data_vencimento'),
                dados_nfse.get('prestador', {}).get('cnpj'),
                dados_nfse.get('prestador', {}).get('nome_razao_social'),
                dados_nfse.get('prestador', {}).get('endereco'),
                dados_nfse.get('prestador', {}).get('municipio'),
                dados_nfse.get('prestador', {}).get('inscricao_municipal'),
                dados_nfse.get('prestador', {}).get('uf'),
                dados_nfse.get('tomador', {}).get('cnpj'),
                dados_nfse.get('tomador', {}).get('nome_razao_social'),
                dados_nfse.get('tomador', {}).get('endereco'),
                dados_nfse.get('tomador', {}).get('municipio'),
                dados_nfse.get('tomador', {}).get('inscricao_municipal'),
                dados_nfse.get('tomador', {}).get('uf'),
                dados_nfse.get('tomador', {}).get('email'),
                dados_nfse.get('data_emissao_nf'),
                dados_nfse.get('valor_total').replace('.', '').replace(',', '.'),  # Ajuste aqui
                'ARQUIVO_EXTRAIDO',
                nfse_id
            ))

        conn.commit()
        logging.info(f"NFSE ID {nfse_id} processada com sucesso e status atualizado para 'ARQUIVO_EXTRAIDO'.")
        print(f"NFSE ID {nfse_id} processada com sucesso e status atualizado para 'ARQUIVO_EXTRAIDO'.")
    except Exception as e:
        print(f"Deu pau ao processar o arquivo {nfse_raw}: {e}")
    

def main():
    """
    Função principal que coordena o processamento das NFSEs.
    """
    try:
        # Conectar ao banco de dados
        conn = conectar_bd()
        print("CONECTOU AO BD")
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            # Selecionar NFSEs com status 'ARQUIVO_RECEBIDO' e com 'arquivo' e 'nome_arquivo' não nulos
            select_query = sql.SQL("""
                SELECT 
                    nfse_id,
                    nome_arquivo,
                    arquivo
                FROM 
                    nfse
                WHERE 
                    status = 'ARQUIVO_RECEBIDO'
                    AND arquivo IS NOT NULL
                    AND nome_arquivo IS NOT NULL;
            """)
            cursor.execute(select_query)
            nfse_lista = cursor.fetchall()
            print(f"Encontradas {len(nfse_lista)} NFSEs para processar.")
            logging.info(f"Encontradas {len(nfse_lista)} NFSEs para processar.")
            print(nfse_lista)  # Opcional: Remove após confirmar que está funcionando

        if not nfse_lista:
            logging.info("Nenhuma NFSE com status 'ARQUIVO_RECEBIDO' encontrada.")
            print("Nenhuma NFSE com status 'ARQUIVO_RECEBIDO' encontrada.")
            conn.close()
            return

        # Processar cada NFSE
        for nfse_raw in nfse_lista:
            processar_nfse(conn, nfse_raw)

        # Fechar a conexão
        conn.close()
        logging.info("Processamento concluído e conexão com o banco de dados fechada.")
        print("Processamento concluído e conexão com o banco de dados fechada.")

    except Exception as e:
        logging.error(f"Erro no processo principal: {e}")
        print(f"Erro no processo principal: {e}")

if __name__ == "__main__":
    main()
