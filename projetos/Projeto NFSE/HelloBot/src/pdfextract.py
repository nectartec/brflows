import os
import pdfplumber
import pandas as pd
import openai
import datetime
from botcity.maestro import *
import pytesseract
from PIL import Image

# Configuração da API da OpenAI
openai.api_key = 'sk-tYK04qgvqTiw-epl1TLTUuhwvqoKPIrC6EHb901XheT3BlbkFJzQIQQ7rBj0af7IZ-p8juSMjl61jxbUFzz5F-4yUU0A'

# Desabilitar erros caso não esteja conectado ao Maestro
BotMaestroSDK.RAISE_NOT_CONNECTED = False

# Instanciar o Maestro SDK
maestro = BotMaestroSDK.from_sys_args()

# Definir o label de log para o processo de PDFs
log_label_pdfs = "log_pdfs"
log_total_sucesso = 0
log_total_falhas = 0
log_total_processados = 0

# Configurar o caminho do Tesseract
# Altere o caminho abaixo para o local onde o Tesseract foi instalado no seu sistema
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# Função para extrair informações com o GPT
def extrair_informacoes(texto):
    prompt = (
        "Por favor, extraia as seguintes informações da NFS-e:\n"
        "1. Número da Nota Fiscal (apenas números, sem caracteres especiais ou espaços)\n"
        "2. Razão Social do Emitente (Prestador)\n"
        "3. CNPJ do Emitente (Prestador)\n"
        "4. Data de Emissão.\n\n"
        "Formate a saída como uma linha CSV no formato: Numero, Razao Social, CNPJ, Data Emissão. \n\n"
        "Me responda SOMENTE a linha CSV, pois isto impacta na minha aplicação, portanto, sem nenhuma palavra ou caractere adicional"
    )
    response = openai.ChatCompletion.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt + f"\n\n{texto}"}]
    )
    return response['choices'][0]['message']['content'].strip()

# Função para garantir que a resposta esteja no formato correto
def verificar_e_extrair(texto):
    max_tentativas = 3
    for tentativa in range(max_tentativas):
        linha_csv = extrair_informacoes(texto)
        linha_csv = linha_csv.replace("```", "").replace("\n", "")
        
        campos = [campo.strip() for campo in linha_csv.split(',')]
        
        try:
            campos[0] = str(int(campos[0]))  # Remove zeros à esquerda
        except ValueError:
            print("Erro ao converter o número da NF para inteiro.")
        
        if len(campos) == 4:
            return campos
        else:
            print("Entrando em Reprocessamento para a NF")
            aviso_prompt = f"A resposta anterior estava incorreta. Formate a informação corretamente como uma linha CSV: Número da Nota Fiscal, Razão Social, CNPJ, Data Emissão.\n{linha_csv}"
            response = openai.ChatCompletion.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": aviso_prompt}]
            )
            linha_csv = response['choices'][0]['message']['content'].strip()
            campos = [campo.strip() for campo in linha_csv.split(',')]
            try:
                campos[0] = str(int(campos[0]))
            except ValueError:
                print("Erro ao converter o número da NF para inteiro.")
            if len(campos) == 4:
                return campos
    return None

# Função para extrair texto de PDFs que contenham imagens
def extrair_texto_com_ocr(pagina_pdf):
    # Converte a página em uma imagem temporária para uso com OCR
    imagem = pagina_pdf.to_image(resolution=300)
    caminho_imagem_temp = 'temp_image.png'
    imagem.save(caminho_imagem_temp)
    
    # Usa OCR para extrair texto da imagem
    texto = pytesseract.image_to_string(Image.open(caminho_imagem_temp))
    
    # Remove a imagem temporária após o processamento
    os.remove(caminho_imagem_temp)
    
    return texto

# Função para processar PDFs no diretório
def processar_pdfs(diretorio):
    dados = []
    global log_total_sucesso, log_total_falhas, log_total_processados
    
    for filename in os.listdir(diretorio):
        if filename.endswith(".pdf"):
            caminho_completo = os.path.join(diretorio, filename)
            log_total_processados += 1
            
            try:
                with pdfplumber.open(caminho_completo) as pdf:
                    texto_completo = ''
                    for pagina in pdf.pages:
                        texto = pagina.extract_text()
                        if not texto:  # Se não extrair texto, usar OCR
                            print(f"Usando OCR para extrair texto da página {pagina.page_number} do arquivo {filename}")
                            texto = extrair_texto_com_ocr(pagina)
                        if texto:
                            texto_completo += texto.replace('\n', ' ')
                    if texto_completo:
                        campos = verificar_e_extrair(texto_completo)
                        if campos:
                            dados.append(campos + [caminho_completo])  # Adiciona campos e caminho do arquivo
                            log_total_sucesso += 1
                        else:
                            log_total_falhas += 1
                            registrar_erro_pdf(caminho_completo, "Erro na extração dos campos")
                    
            except Exception as e:
                log_total_falhas += 1
                registrar_erro_pdf(caminho_completo, str(e))
    
    df = pd.DataFrame(dados, columns=['Número da Nota Fiscal', 'Razão Social', 'CNPJ', 'Data Emissão', 'Caminho do Arquivo'])
    
    maestro.new_log_entry(
        activity_label=log_label_pdfs,
        values={
            "timestamp": datetime.datetime.now().strftime("%Y-%m-%d_%H-%M"),
            "event": "Processamento de PDFs concluído",
            "status": "SUCCESS",
            "total_processados": log_total_processados,
            "total_sucesso": log_total_sucesso,
            "total_falhas": log_total_falhas
        }
    )
    
    return df

# Função para registrar erros no log
def registrar_erro_pdf(arquivo, mensagem_erro):
    maestro.new_log_entry(
        activity_label=log_label_pdfs,
        values={
            "timestamp": datetime.datetime.now().strftime("%Y-%m-%d_%H-%M"),
            "event": f"Erro ao processar o PDF {arquivo}",
            "status": "FAILED",
            "total_processados": log_total_processados,
            "total_sucesso": log_total_sucesso,
            "total_falhas": log_total_falhas,
            "arquivo_pdf": arquivo,
            "error_message": mensagem_erro
        }
    )

# Função para normalizar o CNPJ removendo caracteres de formatação
def clean_cnpj(cnpj):
    if isinstance(cnpj, str):
        return cnpj.replace('.', '').replace('-', '').replace('/', '')
    return cnpj

# Função para tratar o número da NF e remover zeros à esquerda
def normalize_nf(nf):
    try:
        return str(int(nf)).lstrip('0')
    except ValueError:
        return nf

# Função para gerar o arquivo massivo.csv e reprocessamento.csv
def gerar_massivo_csv(df_notas, acompanhamento_df, output_massivo_path, reprocessar_path, historico_execucao_path):
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
        nf_normalizada = normalize_nf(row['Número da Nota Fiscal'])
        cnpj_normalizado = clean_cnpj(row['CNPJ'])

        print(f"Processando NF: {nf_normalizada}, CNPJ: {cnpj_normalizado}")

        matched_row = acompanhamento_df[
            (acompanhamento_df['NF'].apply(normalize_nf) == nf_normalizada) & 
            (acompanhamento_df['CNPJ'].apply(clean_cnpj) == cnpj_normalizado)
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
                'Descricao': matched_row.get('DESCRIÇÃO ', '').replace(';', ','),  # Replace ; por ,
                'Tipo SP': matched_row.get('TIPO DE SP', ''),
                'Centro Custo': matched_row.get('CENTRO DE CUSTO', ''),
                'Item Contab.': '',  # Pode ficar vazio
                'Data Pgto': matched_row.get('VENCIMENTO', ''),
                'Codigo Forn.': matched_row.get('COD. FORN.', ''),
                'Loja Fornec': matched_row.get('COD. LOJA', ''),
                'Valor': valor_formatado,
                'Juros': '0',  # Preenchido como '0'
                'Multa': '0',  # Preenchido como '0'
                'Tipo Pgto': matched_row.get('TIPO DE PAG.', ''),
                'Observacoes': '',  # Pode ficar vazio
                'Numero NF': row['Número da Nota Fiscal'],
                'Serie NF': '',  # Pode ficar vazio
                'D. Emiss NF': row['Data Emissão'],  # Extraído do PDF
                'Natureza': '',  # Pode ficar vazio
                'Pedido Comp.': '',  # Pode ficar vazio
                'Loja Fatura': matched_row.get('COD. LOJA', ''),
                'CC.Despesa': matched_row.get('CC.DESPESA', ''),
                'It.Cont.Desp': '999',  # Deve ser '999'
                'Saldo Solic.': '',  # Pode ficar vazio
                'Competencia': '',  # Pode ficar vazio
                'Rateio ?': matched_row.get('RATEIO ', 'N'),
                'Forma Pgto': matched_row.get('FORMA DE PAG.', ''),
                'Desconto': '',  # Pode ficar vazio
                'Finalidade': matched_row.get('FINALIDADE', '')
            }
            
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

    return df_massivo, df_reprocessar, df_historico


# Função principal para processar as NFs e gerar os arquivos
def processar_notas_fiscais(diretorio_pdfs, caminho_acompanhamento, output_nf_path, output_massivo_path, reprocessar_path, historico_execucao_path):
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

    # Carregar o arquivo de acompanhamento
    acompanhamento_df = pd.read_csv(caminho_acompanhamento, sep=';', encoding='ISO-8859-1', dtype=str)

    # Tratar colunas como inteiros para comparação
    df_notas['Número da Nota Fiscal'] = df_notas['Número da Nota Fiscal'].apply(normalize_nf)
    acompanhamento_df['NF'] = acompanhamento_df['NF'].apply(normalize_nf)

    df_notas['CNPJ'] = df_notas['CNPJ'].apply(clean_cnpj)
    acompanhamento_df['CNPJ'] = acompanhamento_df['CNPJ'].apply(clean_cnpj)

    # Salvar o DataFrame atualizado
    df_notas.to_csv(output_nf_path, sep=';', index=False)

    # Gerar o arquivo massivo.csv e reprocessar.csv
    gerar_massivo_csv(df_notas, acompanhamento_df, output_massivo_path, reprocessar_path, historico_execucao_path)

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

# Caminhos dos diretórios e arquivos usando o caminho relativo
base_dir = os.path.dirname(os.path.abspath(__file__))
diretorio_pdfs = os.path.join(base_dir, '../files/nfs')
caminho_acompanhamento = os.path.join(base_dir, '../files/acompanhamento/acompanhamento.csv')
output_nf_path = os.path.join(base_dir, '../files/extracted_infos/extracted_nfs.csv')
output_massivo_path = os.path.join(base_dir, '../files/massivo/massivo.csv')
reprocessar_path = os.path.join(base_dir, '../files/reprocessamento/reprocessar.csv')
historico_execucao_path = os.path.join(base_dir, '../files/extracted_infos/historico_execucao.csv')

# Processar as notas fiscais e gerar os arquivos
processar_notas_fiscais(diretorio_pdfs, caminho_acompanhamento, output_nf_path, output_massivo_path, reprocessar_path, historico_execucao_path)