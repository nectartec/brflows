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

# Configuração da API da OpenAI
openai.api_key = 'sk-sBXKrXlY-PTv0jTlzo3ru6i4wxLvTQNwPpj7jfiVHNT3BlbkFJvhfI9v8SYKfbIK9nQ1Mx0mTM_d2N58bxmjZ6VxKXsA'

pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# Definicao de caminho raiz
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

# Função para usar OCR no caso de PDFs contendo imagens
def extrair_texto_com_ocr(pagina_pdf):
    imagem = pagina_pdf.to_image(resolution=300)
    caminho_imagem_temp = 'temp_image.png'
    imagem.save(caminho_imagem_temp)
    try:
        texto = pytesseract.image_to_string(Image.open(caminho_imagem_temp))
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

# Função para normalizar o CNPJ removendo caracteres de formatação
def normalize_nf(nf):
    if isinstance(nf, str):
        nf = nf.strip()
    else:
        nf = str(nf)
    # Remover zeros à esquerda
    return nf.lstrip('0')

def clean_cnpj(cnpj):
    if isinstance(cnpj, str):
        cnpj = cnpj.strip()
    else:
        cnpj = str(cnpj)
    cnpj = cnpj.replace('.', '').replace('-', '').replace('/', '')
    # Se o CNPJ tiver menos de 14 dígitos, adicionar zeros à esquerda
    cnpj = cnpj.zfill(14)
    return cnpj


# Função principal para processar as NFs e gerar os arquivos
def processar_notas_fiscais(diretorio_pdfs, caminho_acompanhamento, output_nf_path, output_massivo_path, reprocessar_path, historico_execucao_path):
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

    # Carregar o arquivo de acompanhamento
    acompanhamento_df = pd.read_csv(caminho_acompanhamento, sep=';', encoding='ISO-8859-1', dtype=str)

    # Converter colunas para string
    df_notas['Número da Nota Fiscal'] = df_notas['Número da Nota Fiscal'].astype(str)
    acompanhamento_df['NF'] = acompanhamento_df['NF'].astype(str)
    df_notas['CNPJ'] = df_notas['CNPJ'].astype(str)
    acompanhamento_df['CNPJ'] = acompanhamento_df['CNPJ'].astype(str)

    # Aplicar normalização
    df_notas['Número da Nota Fiscal'] = df_notas['Número da Nota Fiscal'].apply(normalize_nf)
    acompanhamento_df['NF'] = acompanhamento_df['NF'].apply(normalize_nf)
    df_notas['CNPJ'] = df_notas['CNPJ'].apply(clean_cnpj)
    acompanhamento_df['CNPJ'] = acompanhamento_df['CNPJ'].apply(clean_cnpj)

    # Remover espaços em branco extras
    df_notas['Número da Nota Fiscal'] = df_notas['Número da Nota Fiscal'].str.strip()
    acompanhamento_df['NF'] = acompanhamento_df['NF'].str.strip()
    df_notas['CNPJ'] = df_notas['CNPJ'].str.strip()
    acompanhamento_df['CNPJ'] = acompanhamento_df['CNPJ'].str.strip()

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
    print("Arquivo de acompanhamento CNPJ: ")
    print(acompanhamento_df['CNPJ'])
    print("Arquivo de acompanhamento NF: ")
    print(acompanhamento_df['NF'])
    for _, row in df_notas.iterrows():
        nf_normalizada = normalize_nf(row['Número da Nota Fiscal'])
        print("CNPJ ANTES DE NORMALIZAR ", row['CNPJ'])
        cnpj_normalizado = clean_cnpj(row['CNPJ'])

        print(f"Processando NF: {nf_normalizada}, CNPJ: {cnpj_normalizado}")

        # Não reaplicar as funções de normalização aqui
        matched_row = acompanhamento_df[
            (acompanhamento_df['NF'] == nf_normalizada) &
            (acompanhamento_df['CNPJ'] == cnpj_normalizado)
        ]

        if not matched_row.empty:
            matched_row = matched_row.iloc[0]

            valor_str = matched_row.get('VALOR', '').replace('R$ ', '').replace('.', '').replace(' ', '')

            try:
                valor_float = float(valor_str.replace(',', '.'))
                if valor_float.is_integer():
                    valor_formatado = str(int(valor_float))  # Converte para inteiro se não houver decimais
                else:
                    valor_formatado = f"{valor_float:.2f}".replace('.', ',')  # Mantém duas casas decimais e substitui . por ,
            except ValueError:
                valor_formatado = valor_str  # Caso ocorra algum erro, mantém o valor original

            linha_massivo = {
                'Descricao': matched_row.get('DESCRICAO', ''),  # Replace ; por ,
                'Tipo SP': matched_row.get('TIPO DE SP', ''),
                'Centro Custo': matched_row.get('CENTRO DE CUSTO', ''),
                'Item Contab.': '',  # Pode ficar vazio
                'Data Pgto': matched_row.get('VENCIMENTO', ''),
                'Codigo Forn.': matched_row.get('COD. FORN.', ''),
                'Loja Fornec': matched_row.get('LOJA FORNEC.', ''),
                'Valor': valor_formatado,
                'Juros': '0',  # Preenchido como '0'
                'Multa': '0',  # Preenchido como '0'
                'Tipo Pgto': matched_row.get('TIPO DE PAG.', ''),
                'Observacoes': '',  # Pode ficar vazio
                'Numero NF': row['Número da Nota Fiscal'].zfill(9),
                'Serie NF': '',  # Pode ficar vazio
                'D. Emiss NF': row['Data Emissão'],  # Extraído do PDF
                'Natureza': '',  # Pode ficar vazio
                'Pedido Comp.': '',  # Pode ficar vazio
                'Loja Fatura': matched_row.get('COD. LOJA', ''),
                'CC.Despesa': matched_row.get('CC.DESPESA', ''),
                'It.Cont.Desp': matched_row.get('ITEM LOJA', ''),  # Deve ser '999'
                'Saldo Solic.': '',  # Pode ficar vazio
                'Competencia': '',  # Pode ficar vazio
                'Rateio ?': matched_row.get('RATEIO ', 'N'),
                'Forma Pgto': matched_row.get('FORMA DE PAG.', ''),
                'Desconto': '',  # Pode ficar vazio
                'Finalidade': matched_row.get('FINALIDADE', '')
            }
            print("Linha do massivo incluida:")
            print(linha_massivo)

            dados_massivo.append(linha_massivo)
            total_sucesso += 1
        else:
            print(f"NF {nf_normalizada} com CNPJ {cnpj_normalizado} não encontrada no acompanhamento.")
            inconsistencia = {
                'Numero NF': row['Número da Nota Fiscal'],
                'CNPJ': row['CNPJ'],
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

# Ajuste na função processar_classificacoes_e_extrair_info_em_lote
def processar_classificacoes_e_extrair_info_em_lote(classificacoes_json, lotes_texto, caminhos_arquivos, dados, diretorio_base, pasta_processados):
    """
    Processa as classificações de documentos e extrai informações das NFS-e.
    Envia uma única requisição ao GPT para todas as NFS-e no lote.
    """
    nfse_texto_lote = []
    caminhos_nfse_lote = []
    indices_nfse = []

    # Preparar um lote apenas com documentos classificados como NFS-e
    for i, texto in enumerate(lotes_texto):
        classificacao = classificacoes_json.get(f"Documento {i+1}", "").lower()
        if classificacao == 'sim':
            nfse_texto_lote.append(texto)
            caminhos_nfse_lote.append(caminhos_arquivos[i])
            indices_nfse.append(i)
        else:
            print(f"Documento {i+1} não é uma NFS-e. Ignorado.")
            logging.info(f"Documento {i+1} não é uma NFS-e. Ignorado.")
            registrar_arquivo_rejeitado(caminhos_arquivos[i])
            # Mover o arquivo para a pasta de rejeitados
            mover_arquivo_para_rejeitados(
                caminho_origem=caminhos_arquivos[i],
                diretorio_base=diretorio_base,
                pasta_rejeitados=r'C:\Users\Public\NFSE_Rejeitadas'
            )

    # Fazer uma única chamada para todas as NFS-e do lote
    if nfse_texto_lote:
        campos_extracao_lote = extrair_informacoes_em_lote(nfse_texto_lote)
        if campos_extracao_lote is None:
            print("Não foi possível extrair informações em lote.")
            return
        for idx, campos_extracao in enumerate(campos_extracao_lote):
            if campos_extracao:
                # Atualizar o caminho do arquivo para a pasta de processados
                caminho_antigo = caminhos_nfse_lote[idx]
                caminho_relativo = os.path.relpath(caminho_antigo, diretorio_base)
                caminho_novo = os.path.join(pasta_processados, caminho_relativo)

                # Criar as pastas no destino, se não existirem
                os.makedirs(os.path.dirname(caminho_novo), exist_ok=True)

                # Mover o arquivo
                try:
                    shutil.move(caminho_antigo, caminho_novo)
                    print(f"Arquivo movido para: {caminho_novo}")
                    logging.info(f"Arquivo movido para: {caminho_novo}")
                except Exception as e:
                    print(f"Erro ao mover o arquivo {caminho_antigo} para {caminho_novo}: {e}")
                    logging.error(f"Erro ao mover o arquivo {caminho_antigo} para {caminho_novo}: {e}")
                    continue  # Pula para a próxima iteração em caso de erro

                # Adicionar os dados extraídos ao 'dados', incluindo o novo caminho
                dados.append(campos_extracao + [caminho_novo])
            else:
                print(f"Não foi possível extrair dados do documento {indices_nfse[idx]+1}")
                logging.warning(f"Não foi possível extrair dados do documento {indices_nfse[idx]+1}")
                # Mover o arquivo para a pasta de rejeitados
                caminho_antigo = caminhos_nfse_lote[idx]
                mover_arquivo_para_rejeitados(
                    caminho_origem=caminho_antigo,
                    diretorio_base=diretorio_base,
                    pasta_rejeitados=r'C:\Users\Public\NFSE_Rejeitadas'
                )

    else:
        print("Nenhuma NFS-e foi identificada neste lote.")

def processar_pdfs(diretorio):
    """
    Processa todos os PDFs no diretório e subdiretórios.
    Usa GPT para classificar e extrair informações em lote.
    Agrupa até 5 PDFs por vez e envia ao GPT.
    """
    dados = []
    lotes_texto = []
    caminhos_arquivos = []
    pasta_processados = r'C:\Users\Public\Processed_NFSe'

    # Caminhar recursivamente em todas as subpastas
    for root, _, files in os.walk(diretorio):
        for filename in files:
            if filename.endswith(".pdf"):
                caminho_completo = os.path.join(root, filename)
                try:
                    # Bloco try-finally para garantir o fechamento do arquivo
                    with pdfplumber.open(caminho_completo) as pdf:
                        texto_completo = ''
                        for pagina in pdf.pages:
                            texto = pagina.extract_text()
                            if not texto:
                                print(f"Usando OCR para extrair texto da página do arquivo: {filename}")
                                texto = extrair_texto_com_ocr(pagina)
                            if texto:
                                texto_completo += texto.replace('\n', ' ')

                        # Adicionar ao lote de textos e arquivos
                        lotes_texto.append(texto_completo)
                        caminhos_arquivos.append(caminho_completo)

                    # Se o lote atingir 5 arquivos, envia para classificação
                    if len(lotes_texto) == 5:
                        classificacoes_json = classificar_documento_em_lote(lotes_texto)
                        processar_classificacoes_e_extrair_info_em_lote(
                            classificacoes_json, lotes_texto, caminhos_arquivos, dados, diretorio, pasta_processados)
                        lotes_texto = []  # Limpa os lotes
                        caminhos_arquivos = []  # Limpa os caminhos

                except Exception as e:
                    print(f"Erro ao processar o arquivo {filename}: {e}")
                    logging.error(f"Erro ao processar o arquivo {filename}: {e}")

    # Verificar se há algum arquivo restante para ser classificado
    if lotes_texto:
        classificacoes_json = classificar_documento_em_lote(lotes_texto)
        processar_classificacoes_e_extrair_info_em_lote(
            classificacoes_json, lotes_texto, caminhos_arquivos, dados, diretorio, pasta_processados)

    # Gerar o DataFrame com os dados extraídos e salvar no CSV
    if dados:  # Verificar se há dados antes de salvar
        df = pd.DataFrame(dados, columns=[
                          'Número da Nota Fiscal', 'Razão Social', 'CNPJ', 'Data Emissão', 'Caminho do Arquivo'])
        df.to_csv(r'C:\\Users\\roger.oliveira\Documents\\Projeto NFSE\\HelloBot\\files\\extracted_infos\\extracted_nfs.csv',
                  sep=';', index=False)
        logging.info(
            "PDFs processados com sucesso e caminhos atualizados no CSV.")
    else:
        print("Nenhum dado foi extraído dos PDFs.")
        df = pd.DataFrame()  # DataFrame vazio se nenhum dado for extraído

    return df

# def processar_classificacoes_e_extrair_info_em_lote(classificacoes_json, lotes_texto, caminhos_arquivos, dados, diretorio_base, pasta_processados):
#     """
#     Processa as classificações de documentos e extrai informações das NFS-e.
#     Envia uma única requisição ao GPT para todas as NFSe no lote.
#     """
#     nfse_texto_lote = []
#     caminhos_nfse_lote = []
#     indices_nfse = []

#     # Preparar um lote apenas com documentos classificados como NFS-e
#     for i, texto in enumerate(lotes_texto):
#         classificacao = classificacoes_json.get(f"Documento {i+1}", "").lower()
#         if classificacao == 'sim':
#             nfse_texto_lote.append(texto)
#             caminhos_nfse_lote.append(caminhos_arquivos[i])
#             indices_nfse.append(i)
#         else:
#             print(f"Documento {i+1} não é uma NFS-e. Ignorado.")
#             logging.info(f"Documento {i+1} não é uma NFS-e. Ignorado.")
#             registrar_arquivo_rejeitado(caminhos_arquivos[i])
#             mover_arquivo_para_rejeitados(caminhos_arquivos[i], r'C:\\Users\\Public\\NFSE_Rejeitadas')

#     # Fazer uma única chamada para todas as NFS-e do lote
#     if nfse_texto_lote:
#         campos_extracao_lote = extrair_informacoes_em_lote(nfse_texto_lote)
#         if campos_extracao_lote is None:
#             print("Não foi possível extrair informações em lote.")
#             return
#         for idx, campos_extracao in enumerate(campos_extracao_lote):
#             if campos_extracao:
#                 # Atualizar o caminho do arquivo para a pasta de processados
#                 caminho_antigo = caminhos_nfse_lote[idx]
#                 caminho_relativo = os.path.relpath(caminho_antigo, diretorio_base)
#                 caminho_novo = os.path.join(pasta_processados, caminho_relativo)

#                 # Criar as pastas no destino, se não existirem
#                 os.makedirs(os.path.dirname(caminho_novo), exist_ok=True)

#                 # Mover o arquivo
#                 shutil.move(caminho_antigo, caminho_novo)
#                 print(f"Arquivo movido para: {caminho_novo}")

#                 # Adicionar os dados extraídos ao 'dados', incluindo o novo caminho
#                 dados.append(campos_extracao + [caminho_novo])
#             else:
#                 print(f"Não foi possível extrair dados do documento {indices_nfse[idx]+1}")

# Função para gerenciar o controle de limite de requisições
def controle_limite_requisicoes():
    global gpt_calls, start_time

    # Se já houver 500 chamadas, espera até completar 1 minuto
    if gpt_calls >= 500:
        elapsed_time = time.time() - start_time
        if elapsed_time < 60:
            wait_time = 60 - elapsed_time
            print(f"Atingido o limite de 3 requisições. Aguardando {wait_time:.2f} segundos.")
            time.sleep(wait_time)
        gpt_calls = 0  # Reseta as chamadas após o tempo de espera
        start_time = time.time()  # Reinicia o temporizador

# Função para extrair informações em lote de até 5 documentos
def extrair_informacoes_em_lote(lista_textos, max_retries=3):
    global gpt_calls, start_time
    """
    Faz a requisição ao GPT-4 mini para extrair informações de até 5 NFs por vez em uma única requisição.
    """
    prompt = (
        "Por favor, extraia as seguintes informações das NFSe abaixo (até 5):\n"
        "1. Número da Nota Fiscal (apenas números, sem caracteres especiais ou espaços).\n"
        "2. Razão Social do Emitente (Prestador).\n"
        "3. CNPJ do Emitente da NFSe (Prestador, com 14 dígitos, sem pontos, traços ou barra, somente os números).\n"
        "4. Data de Emissão no formato dd/mm/aaaa.\n\n"
        "Formate a saída como até 5 linhas CSV, separadas por quebras de linha. Cada linha deve estar no formato:\n"
        "Numero, Razao Social, CNPJ, Data Emissão\n"
        "Me responda SOMENTE as linhas CSV, sem nenhuma formatação adicional como crases, blocos de código ou similares. Não inclua '```' ou qualquer outra coisa além das linhas CSV.\n"
        "Não coloque aspas envolvendo os valores das colunas, pois isso atrapalha meu processo de RPA.\n"
    )

    # Adicionar os textos das NFs ao prompt
    conteudo = "\n\n".join([f"NF {i+1}:\n{texto}" for i, texto in enumerate(lista_textos)])
    prompt += conteudo

    retries = 0
    while retries < max_retries:
        # Gerenciar controle de limite de requisições
        controle_limite_requisicoes()

        try:
            print("Chamada para GPT - Extração em lote")
            response = openai.ChatCompletion.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}]
            )
            gpt_calls += 1  # Incrementa o contador de chamadas
            # A resposta será uma string com várias linhas, cada uma correspondendo a uma NF
            conteudo_resposta = response['choices'][0]['message']['content'].strip()

            # Remove blocos de código (crases) se existirem
            if conteudo_resposta.startswith("```") and conteudo_resposta.endswith("```"):
                conteudo_resposta = conteudo_resposta.strip("```").strip()

            # Agora, dividir as linhas
            linhas_csv = conteudo_resposta.strip().split("\n")
            print("Resposta recebida em lote após limpeza: ", linhas_csv)

            # Converter cada linha em uma lista de campos CSV
            campos = [linha.strip().split(",") for linha in linhas_csv if linha.strip()]
            return campos

            
        except openai.error.RateLimitError as e:
            print(f"Erro de limite de requisição: {e}")
            time.sleep(60)  # Espera 1 minuto em caso de erro de limite
            retries += 1
        except Exception as e:
            print(f"Erro ao extrair informações em lote: {e}")
            return None
    print("Falha ao extrair informações em lote após múltiplas tentativas.")
    return None

# Função para classificar o documento em lote
def classificar_documento_em_lote(lista_textos, max_retries=3):
    global gpt_calls, start_time
    """
    Envia vários documentos ao GPT em uma única requisição e retorna se cada um é uma NFS-e.
    """
    prompt = (
        "Você recebeu textos de documentos fiscais. Para cada documento, responda apenas com 'Sim' ou 'Não' se o documento é uma Nota Fiscal de Serviços Eletrônica (NFS-e).\n\n"
        "Atente-se que você deverá responder Sim somente para o que for NFSe, ou seja, Nota Fiscal de Serviço Eletronica, DANFE, Notas Fiscais de Produtos e outras coisas Não são NFSE!\n"
        "A resposta deve ser um JSON no seguinte formato:\n"
        "{\n"
        "  'Documento 1': 'Sim' ou 'Não',\n"
        "  'Documento 2': 'Sim' ou 'Não',\n"
        "  'Documento 3': 'Sim' ou 'Não',\n"
        "  ...\n"
        "}\n\n"
    )

    # Adicionar os textos dos documentos ao prompt
    conteudo = "\n\n".join([f"Documento {i+1}:\n{texto}" for i, texto in enumerate(lista_textos)])
    prompt += conteudo

    retries = 0
    while retries < max_retries:
        # Gerenciar controle de limite de requisições
        controle_limite_requisicoes()

        try:
            print("Chamada para GPT - Classificação em lote")
            response = openai.ChatCompletion.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}]
            )
            gpt_calls += 1  # Incrementa o contador de chamadas

            # A resposta será um JSON com a classificação de cada documento
            classificacoes = response['choices'][0]['message']['content'].strip()

            # Remove blocos de código (crases) se existirem
            if classificacoes.startswith("```") and classificacoes.endswith("```"):
                classificacoes = classificacoes.strip("```json").strip("```")

            # Converter a string JSON para dicionário
            return json.loads(classificacoes)  # Use json.loads() para converter a string JSON para dicionário

        except openai.error.RateLimitError as e:
            print(f"Erro de limite de requisição: {e}")
            time.sleep(60)
            retries += 1
        except json.JSONDecodeError as e:
            print(f"Erro ao decodificar o JSON: {e}")
            return {}
        except Exception as e:
            print(f"Erro na classificação em lote: {e}")
            return {}
    print("Falha ao classificar documentos em lote após múltiplas tentativas.")
    return {}

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

    # Processar as notas fiscais extraídas e gerar os arquivos de saída
    df_massivo, df_reprocessar, df_historico = processar_notas_fiscais(
        diretorio_pdfs=pdf_directory,
        caminho_acompanhamento=os.path.join(base_dir, 'files/acompanhamento/acompanhamento.csv'),
        output_nf_path=output_nf_path,
        output_massivo_path=output_massivo_path,
        reprocessar_path=reprocessar_path,
        historico_execucao_path=historico_execucao_path
    )

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
