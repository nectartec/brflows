import numpy as np
import cv2
import os
import pdfplumber
import pandas as pd
import openai
import pytesseract
from PIL import Image
import datetime
import time
from botcity.maestro import *
import logging
import json
import shutil
import re

# Configuração da API da OpenAI
openai.api_key = 'sk-sBXKrXlY-PTv0jTlzo3ru6i4wxLvTQNwPpj7jfiVHNT3BlbkFJvhfI9v8SYKfbIK9nQ1Mx0mTM_d2N58bxmjZ6VxKXsA'

pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

os.environ["TESSDATA_PREFIX"] = r"C:\Program Files\Tesseract-OCR\tessdata"

# Definição de caminho raiz
BASE_SAVE_PATH = r'C:\\Users\\Public\\NFSe'
gpt_calls = 0
start_time = time.time()
# Desabilitar erros caso não esteja conectado ao Maestro
BotMaestroSDK.RAISE_NOT_CONNECTED = False
# Instanciar o Maestro SDK
maestro = BotMaestroSDK.from_sys_args()

# Definir o label de log para o processo de PDFs
log_label_pdfs = "log_pdfs"
log_total_sucesso = 0
log_total_falhas = 0
log_total_processados = 0

# Configuração de logging
logging.basicConfig(
    filename='pdf_extract.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Caminho da planilha de PDFs rejeitados
planilha_rejeitados = r'C:\\Users\\Public\\Observability\\PDFExtract\\rejeitados.xlsx'

# Funções de pré-processamento de imagem
def adjust_resolution(image):
    # Aumentar a resolução da imagem
    scale_percent = 200  # Aumenta a resolução em 200%
    width = int(image.shape[1] * scale_percent / 100)
    height = int(image.shape[0] * scale_percent / 100)
    dim = (width, height)
    # Interpolação bicúbica para melhor qualidade
    resized = cv2.resize(image, dim, interpolation=cv2.INTER_CUBIC)
    return resized

def convert_to_grayscale(image):
    return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

def remove_background(image):
    # Aplicar limiarização adaptativa
    return cv2.adaptiveThreshold(image, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                 cv2.THRESH_BINARY, 31, 2)

def deskew_image(image):
    coords = np.column_stack(np.where(image > 0))
    angle = cv2.minAreaRect(coords)[-1]
    if angle < -45:
        angle = -(90 + angle)
    else:
        angle = -angle
    (h, w) = image.shape[:2]
    center = (w // 2, h // 2)
    M = cv2.getRotationMatrix2D(center, angle, 1.0)
    rotated = cv2.warpAffine(image, M, (w, h),
                             flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
    return rotated

def remove_noise(image):
    # Aplicar filtro de mediana
    denoised = cv2.medianBlur(image, 3)
    return denoised

# Função para usar OCR no caso de PDFs contendo imagens
def extrair_texto_com_ocr(pagina_pdf):
    imagem = pagina_pdf.to_image(resolution=300)
    caminho_imagem_temp = 'temp_image.png'
    imagem.save(caminho_imagem_temp)
    try:
        # Carregar a imagem
        img = cv2.imread(caminho_imagem_temp)
        # Pré-processamento
        img = convert_to_grayscale(img)
        img = adjust_resolution(img)
        img = remove_noise(img)
        img = deskew_image(img)
        img = remove_background(img)
        # Salvar a imagem pré-processada
        cv2.imwrite(caminho_imagem_temp, img)
        # Configurações do Tesseract
        custom_config = r'--oem 3 --psm 6 -l por'
        texto = pytesseract.image_to_string(Image.open(caminho_imagem_temp), config=custom_config)
    except Exception as e:
        print(f"Erro ao extrair texto com OCR: {e}")
        texto = ''
    finally:
        # Garantir que a imagem temporária seja fechada e removida
        if os.path.exists(caminho_imagem_temp):
            os.remove(caminho_imagem_temp)
    return texto

# Função para salvar o arquivo excluído na planilha de rejeitados
def registrar_arquivo_rejeitado(caminho_arquivo):
    data_hora = time.strftime('%Y-%m-%d %H:%M:%S')

    # Carregar a planilha existente ou criar uma nova
    if os.path.exists(planilha_rejeitados):
        df = pd.read_excel(planilha_rejeitados)
    else:
        df = pd.DataFrame(columns=['data_hora_processamento', 'caminho_arquivo_excluido'])

    # Adicionar o novo registro
    novo_registro = {'data_hora_processamento': data_hora, 'caminho_arquivo_excluido': caminho_arquivo}
    df = pd.concat([df, pd.DataFrame([novo_registro])], ignore_index=True)

    # Salvar de volta na planilha
    df.to_excel(planilha_rejeitados, index=False)

# Função para normalizar a NF
def normalize_nf(nf):
    if isinstance(nf, str):
        nf = nf.strip()
        nf = nf.replace(' ', '')
        nf = re.sub(r'\D', '', nf)  # Remove tudo que não é dígito
    else:
        nf = str(nf)
    return nf

# Função para limpar e padronizar o CNPJ
def clean_cnpj(cnpj):
    if isinstance(cnpj, str):
        cnpj = cnpj.strip()
        cnpj = cnpj.replace('.', '').replace('-', '').replace('/', '').replace(' ', '')
    else:
        cnpj = str(cnpj)
    # Se o CNPJ tiver menos de 14 dígitos, adicionar zeros à esquerda
    cnpj = cnpj.zfill(14)
    return cnpj

# Função principal para processar as NFs e gerar os arquivos
def processar_notas_fiscais(diretorio_pdfs, caminho_acompanhamento_excel, output_nf_path, output_massivo_path, reprocessar_path, historico_execucao_path):
    global log_total_processados, log_total_sucesso, log_total_falhas
    # Registrar início do processamento
    maestro.new_log_entry(
        activity_label=log_label_pdfs,
        values={
            "timestamp": datetime.datetime.now().strftime("%Y-%m-%d_%H-%M"),
            "event": "Início do processamento de PDFs",
            "status": "START",
            "total_processados": 0,
            "total_sucesso": 0,
            "total_falhas": 0
        }
    )

    # Processar os PDFs e extrair as informações
    df_notas = processar_pdfs(diretorio_pdfs)
    log_total_processados = len(df_notas)

    # Carregar o arquivo de acompanhamento diretamente do Excel, forçando as colunas 'NF' e 'CNPJ' como string
    acompanhamento_df = pd.read_excel(caminho_acompanhamento_excel, dtype={'NF': str, 'CNPJ': str})

    # Remover espaços em branco e caracteres não numéricos das NFs
    df_notas['Número da Nota Fiscal'] = df_notas['Número da Nota Fiscal'].astype(str).str.strip().str.replace(' ', '').str.replace(r'\D', '', regex=True)
    acompanhamento_df['NF'] = acompanhamento_df['NF'].astype(str).str.strip().str.replace(' ', '').str.replace(r'\D', '', regex=True)

    # Limpar e padronizar o CNPJ
    df_notas['CNPJ'] = df_notas['CNPJ'].apply(clean_cnpj)
    acompanhamento_df['CNPJ'] = acompanhamento_df['CNPJ'].apply(clean_cnpj)

    # Confirmar que todos os CNPJs têm 14 dígitos
    df_notas['CNPJ'] = df_notas['CNPJ'].apply(lambda x: x.zfill(14))
    acompanhamento_df['CNPJ'] = acompanhamento_df['CNPJ'].apply(lambda x: x.zfill(14))

    # Remover espaços em branco extras
    df_notas['Número da Nota Fiscal'] = df_notas['Número da Nota Fiscal'].str.strip()
    acompanhamento_df['NF'] = acompanhamento_df['NF'].str.strip()
    df_notas['CNPJ'] = df_notas['CNPJ'].str.strip()
    acompanhamento_df['CNPJ'] = acompanhamento_df['CNPJ'].str.strip()

    # Adicionar prints para verificar os valores das colunas
    print("Colunas em df_notas:", df_notas.columns.tolist())
    print("Colunas em acompanhamento_df:", acompanhamento_df.columns.tolist())

    # Salvar o DataFrame atualizado
    df_notas.to_csv(output_nf_path, sep=';', index=False)

    # Gerar o arquivo massivo.csv e reprocessar.csv
    df_massivo, df_reprocessar, df_historico = gerar_massivo_csv(df_notas, acompanhamento_df, output_massivo_path, reprocessar_path, historico_execucao_path)
    log_total_sucesso = len(df_massivo)
    log_total_falhas = len(df_reprocessar) if df_reprocessar is not None else 0

    # Registrar finalização do processamento
    maestro.new_log_entry(
        activity_label=log_label_pdfs,
        values={
            "timestamp": datetime.datetime.now().strftime("%Y-%m-%d_%H-%M"),
            "event": "Processamento de PDFs finalizado",
            "status": "END",
            "total_processados": log_total_processados,
            "total_sucesso": log_total_sucesso,
            "total_falhas": log_total_falhas
        }
    )

    # Garantir que a função sempre retorna os três DataFrames, mesmo que vazios
    return df_massivo, df_reprocessar, df_historico

# Função para gerar o arquivo massivo.csv e reprocessar.csv
def gerar_massivo_csv(df_notas, acompanhamento_df, output_massivo_path, reprocessar_path, historico_execucao_path):
    # As colunas do arquivo massivo
    colunas_massivo = [
        'Descricao', 'Tipo SP', 'Centro Custo', 'Item Contab.', 'Data Pgto',
        'Codigo Forn.', 'Loja Fornec', 'Valor', 'Juros', 'Multa', 'Tipo Pgto',
        'Observacoes', 'Numero NF', 'Serie NF', 'D. Emiss NF', 'Natureza',
        'Pedido Comp.', 'Loja Fatura', 'CC.Despesa', 'It.Cont.Desp', 'Saldo Solic.',
        'Competencia', 'Rateio ?', 'Forma Pgto', 'Desconto', 'Finalidade'
    ]

    dados_massivo = []
    dados_reprocessar = []
    total_processadas = len(df_notas)
    total_sucesso = 0
    total_falhas = 0

    for _, row in df_notas.iterrows():
        nf_original = row['Número da Nota Fiscal']
        cnpj_original = row['CNPJ']

        nf_normalizada = str(normalize_nf(nf_original))
        cnpj_normalizado = str(clean_cnpj(cnpj_original))

        print(f"NF extraída: {nf_original}, NF normalizada: {nf_normalizada}")
        print(f"CNPJ extraído: {cnpj_original}, CNPJ normalizado: {cnpj_normalizado}")

        acompanhamento_df['NF'] = acompanhamento_df['NF'].apply(lambda x: str(x).zfill(9))
        acompanhamento_df['CNPJ'] = acompanhamento_df['CNPJ'].apply(lambda x: str(x).zfill(14))

        nf_normalizada = str(int(nf_normalizada)).zfill(9)
        cnpj_normalizado = str(int(cnpj_normalizado)).zfill(14)
        # Verificar se a NF e CNPJ normalizados existem no DataFrame de acompanhamento
        nf_existe = str(nf_normalizada).zfill(9) in acompanhamento_df['NF'].values
        cnpj_existe = str(cnpj_normalizado).zfill(14) in acompanhamento_df['CNPJ'].values

        print(f"NF existe no acompanhamento: {nf_existe}")
        print(f"CNPJ existe no acompanhamento: {cnpj_existe}")

        # Buscar a linha correspondente no acompanhamento_df
        matched_row = acompanhamento_df[
            (acompanhamento_df['NF'] == nf_normalizada) &
            (acompanhamento_df['CNPJ'] == cnpj_normalizado)
        ]

        if not matched_row.empty:
            matched_row = matched_row.iloc[0]
            print(f"Correspondência encontrada para NF {nf_normalizada} com CNPJ {cnpj_normalizado}")

            # Processar os campos necessários para o arquivo massivo
            valor_str = str(matched_row.get('VALOR', '')).replace('R$ ', '').replace('.00', '').replace(' ', '')

            try:
                valor_float = float(valor_str.replace(',', '.'))
                if valor_float.is_integer():
                    valor_formatado = str(int(valor_float))  # Converte para inteiro se não houver decimais
                else:
                    valor_formatado = f"{valor_float:.2f}".replace('.', ',')  # Mantém duas casas decimais
            except ValueError:
                valor_formatado = valor_str  # Caso ocorra algum erro, mantém o valor original

            linha_massivo = {
                'Descricao': matched_row.get('DESCRIÇÃO ', ''),
                'Tipo SP': str(int(matched_row.get('TIPO DE SP', 0))).zfill(6),
                'Centro Custo': str(matched_row.get('CENTRO DE CUSTO', '')).replace('.0', ''),
                'Item Contab.': '',  # Pode ficar vazio
                'Data Pgto': pd.to_datetime(matched_row.get('VENCIMENTO', '')).strftime('%d/%m/%Y'),
                'Codigo Forn.': str(matched_row.get('COD. FORN.', '')).replace('.0', '').zfill(8),
                'Loja Fornec': '01',  # Ajuste conforme necessário
                'Valor': valor_formatado,
                'Juros': '0',
                'Multa': '0',
                'Tipo Pgto': str(matched_row.get('TIPO DE PAG.', '')).replace('.0', ''),
                'Observacoes': '',
                'Numero NF': nf_normalizada.zfill(9),
                'Serie NF': '',
                'D. Emiss NF': row['Data Emissão'],
                'Natureza': '',
                'Pedido Comp.': '',
                'Loja Fatura': matched_row.get('COD. LOJA', ''),
                'CC.Despesa': str(matched_row.get('CC.DESPESA', '')).replace('.0', ''),
                'It.Cont.Desp': str(matched_row.get('ITEM LOJA', '')).replace('.0', '').zfill(4),
                'Saldo Solic.': '',
                'Competencia': '',
                'Rateio ?': matched_row.get('RATEIO ', 'N'),
                'Forma Pgto': str(matched_row.get('FORMA DE PAG.', '')).replace('.0', ''),
                'Desconto': '',
                'Finalidade': str(matched_row.get('FINALIDADE', '')).replace('.0', '')
            }

            dados_massivo.append(linha_massivo)
            total_sucesso += 1
        else:
            print(f"NF {nf_normalizada} com CNPJ {cnpj_normalizado} não encontrada no acompanhamento.")
            inconsistencia = {
                'Numero NF': nf_original,
                'CNPJ': cnpj_original,
                'Inconsistência': 'NF ou CNPJ não encontrados no acompanhamento.'
            }
            dados_reprocessar.append(inconsistencia)
            total_falhas += 1

    # Gerar o arquivo massivo.csv
    df_massivo = pd.DataFrame(dados_massivo, columns=colunas_massivo)
    df_massivo.to_csv(output_massivo_path, sep=';', index=False)
    print("Arquivo massivo.csv gerado com sucesso!")

    # Inicializa df_reprocessar
    df_reprocessar = None

    # Se houver NFs para reprocessar, cria o arquivo reprocessar.csv
    if dados_reprocessar:
        df_reprocessar = pd.DataFrame(dados_reprocessar)
        reprocessar_folder = os.path.dirname(reprocessar_path)
        os.makedirs(reprocessar_folder, exist_ok=True)
        df_reprocessar.to_csv(reprocessar_path, sep=';', index=False)
        print("Arquivo reprocessar.csv gerado com sucesso!")
    else:
        print("Nenhuma NF para reprocessar.")

    # Gerar o arquivo de histórico de execução
    historico = {
        'Total NFs Processadas': total_processadas,
        'Total NFs Sucesso': total_sucesso,
        'Total NFs Falhas': total_falhas,
        'Percentual Sucesso': f"{(total_sucesso / total_processadas) * 100:.2f}%" if total_processadas > 0 else "0%",
        'Percentual Falhas': f"{(total_falhas / total_processadas) * 100:.2f}%" if total_processadas > 0 else "0%",
        'Detalhes das Falhas': [f"NF: {item['Numero NF']}, CNPJ: {item['CNPJ']}, Inconsistência: {item['Inconsistência']}" for item in dados_reprocessar]
    }

    df_historico = pd.DataFrame([historico])
    df_historico.to_csv(historico_execucao_path, sep=';', index=False)
    print("Arquivo historico_execucao.csv gerado com sucesso!")

    # Retornar os três DataFrames
    return df_massivo, df_reprocessar, df_historico

# Função para mover arquivos para a pasta de rejeitados, mantendo a estrutura de pastas
def mover_arquivo_para_rejeitados(caminho_origem, diretorio_base, pasta_rejeitados):
    # Verificar se o arquivo de origem existe
    if not os.path.exists(caminho_origem):
        print(f"O arquivo {caminho_origem} não existe.")
        logging.warning(f"O arquivo {caminho_origem} não existe e não pode ser movido.")
        return

    # Obter o caminho relativo em relação ao diretório base
    caminho_relativo = os.path.relpath(caminho_origem, diretorio_base)
    caminho_destino = os.path.join(pasta_rejeitados, caminho_relativo)

    # Criar as pastas no destino, se não existirem
    os.makedirs(os.path.dirname(caminho_destino), exist_ok=True)

    # Se o arquivo já existir no destino, adicionar um sufixo para evitar sobreposição
    if os.path.exists(caminho_destino):
        nome_arquivo = os.path.basename(caminho_destino)
        nome_base, extensao = os.path.splitext(nome_arquivo)
        contador = 1
        while os.path.exists(caminho_destino):
            novo_nome_arquivo = f"{nome_base}_{contador}{extensao}"
            caminho_destino = os.path.join(os.path.dirname(caminho_destino), novo_nome_arquivo)
            contador += 1

    # Mover o arquivo
    try:
        shutil.move(caminho_origem, caminho_destino)
        print(f"Arquivo movido para: {caminho_destino}")
        logging.info(f"Arquivo movido para: {caminho_destino}")
    except Exception as e:
        print(f"Erro ao mover o arquivo {caminho_origem} para {caminho_destino}: {e}")
        logging.error(f"Erro ao mover o arquivo {caminho_origem} para {caminho_destino}: {e}")

# ... (restante das funções permanece inalterado)

def main():
    # Integração com o Maestro
    maestro = BotMaestroSDK.from_sys_args()
    execution = maestro.get_execution()

    # Parâmetro para o diretório onde os PDFs foram salvos pelo processo de extração de e-mails
    pdf_directory = BASE_SAVE_PATH

    # Definição de caminhos dos arquivos de saída (como no processo anterior)
    base_dir = os.path.dirname(os.path.abspath(__file__))  # Diretório raiz da automação
    output_nf_path = os.path.join(base_dir, 'files/extracted_infos/extracted_nfs.csv')
    output_massivo_path = os.path.join(base_dir, 'files/massivo/massivo.csv')
    reprocessar_path = os.path.join(base_dir, 'files/reprocessamento/reprocessar.csv')
    historico_execucao_path = os.path.join(base_dir, 'files/extracted_infos/historico_execucao.csv')

    print(f"Task ID is: {execution.task_id}")
    print(f"Task Parameters are: {execution.parameters}")
    caminho_excel = r'C:\Users\roger.oliveira\Documents\Projeto NFSE\HelloBot\files\acompanhamento\Acompanhamento R1 - notas transportadoras At. 29.10.xlsx'

    # Processar as notas fiscais extraídas e gerar os arquivos de saída
    df_massivo, df_reprocessar, df_historico = processar_notas_fiscais(
        diretorio_pdfs=pdf_directory,
        caminho_acompanhamento_excel=caminho_excel,
        output_nf_path=output_nf_path,
        output_massivo_path=output_massivo_path,
        reprocessar_path=reprocessar_path,
        historico_execucao_path=historico_execucao_path
    )

    filter_extracted_nfs(output_nf_path, output_massivo_path)

    # Enviar logs finais para o Maestro com os totais de processamentos
    print(f"Total processados: {log_total_processados}")
    print(f"Total sucesso: {log_total_sucesso}")
    print(f"Total falhas: {log_total_falhas}")

    # Finalizar a tarefa no Maestro
    maestro.finish_task(
        task_id=execution.task_id,
        status=AutomationTaskFinishStatus.SUCCESS,
        message="Processo de extração de PDFs e geração de arquivos concluído com sucesso."
    )

if __name__ == '__main__':
    main()
