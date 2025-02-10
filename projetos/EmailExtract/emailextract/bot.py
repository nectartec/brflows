import os
import time
import datetime
import pythoncom
import win32com.client
import logging
from botcity.core import DesktopBot
from botcity.maestro import *
import pandas as pd

# Configuração de logging
logging.basicConfig(
    filename='outlook_email_processor.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Caminho da planilha de observabilidade
planilha_observability = r'C:\\Users\\Public\\Observability\\Email\\Email_Observability.xlsx'

# Diretório base para salvar os anexos
BASE_SAVE_PATH = r'C:\\Users\\Public\\NFSe'

# Desabilitar erros caso não esteja conectado ao Maestro
BotMaestroSDK.RAISE_NOT_CONNECTED = False

def create_directory(base_path, email_received_time):
    """
    Cria uma estrutura de diretórios baseada no intervalo de hora de recebimento do e-mail.
    Exemplo: C: Users Public NFSe 2024-09-17 11.00-11.59
    """
    date_str = email_received_time.strftime('%Y-%m-%d')
    hour = email_received_time.hour
    time_interval_str = f"{hour:02d}.00-{hour:02d}.59"
    path = os.path.join(base_path, date_str, time_interval_str)
    return path

def registrar_falha_na_planilha(data_processo, data_email, emitente, titulo, anexos_recebidos, anexos_nao_salvos, erro=None):
    """
    Função para registrar as falhas na planilha de observabilidade, incluindo erros gerais no processamento de e-mails.
    """
    # Carregar o dataframe existente
    df = pd.read_excel(planilha_observability, sheet_name='Planilha1')

    # Criar um novo registro com as informações do erro
    novo_registro = pd.DataFrame({
        'Data do Processo': [data_processo],
        'Data e hora do e-mail': [data_email if data_email else 'Erro ao ler e-mail'],
        'Emitente': [emitente if emitente else 'Erro ao ler e-mail'],
        'Título do e-mail': [titulo if titulo else 'Erro ao ler e-mail'],
        'Anexos recebidos': [', '.join(anexos_recebidos) if anexos_recebidos else 'Erro ao ler anexos'],
        'Anexos não salvos': [', '.join(anexos_nao_salvos) if anexos_nao_salvos else 'Erro ao salvar anexos'],
        'Erro': [erro if erro else 'N/A']
    })

    # Usar pd.concat para adicionar o novo registro ao dataframe existente
    df = pd.concat([df, novo_registro], ignore_index=True)

    # Salvar de volta para o arquivo
    df.to_excel(planilha_observability, sheet_name='Planilha1', index=False, engine='openpyxl')

    return df

def save_pdf_attachments(mail, save_path, emitente, titulo):
    """
    Salva os anexos PDF de um e-mail no caminho especificado. 
    Só cria a pasta se houver anexos a salvar.
    """
    attachments = mail.Attachments
    pdf_saved = False  # Flag para saber se algum PDF foi salvo
    pdf_attachments_recebidos = []  # Lista de anexos salvos com sucesso
    pdf_attachments_falhas = []  # Lista de anexos que falharam no salvamento
    total_pdf_attachments = 0  # Contagem de PDFs recebidos com sucesso

    for attachment in attachments:
        # Verifica se o anexo é um arquivo PDF
        if attachment.FileName.lower().endswith('.pdf'):
            # Apenas criar a pasta se houver PDFs
            if not pdf_saved:
                os.makedirs(save_path, exist_ok=True)
                pdf_saved = True
                logging.info(f'Pasta criada: {save_path}')

            attachment_path = os.path.join(save_path, attachment.FileName)
            try:
                attachment.SaveAsFile(attachment_path)
                logging.info(f'Anexo PDF salvo: {attachment_path}')
                print(f'Anexo PDF salvo: {attachment_path}')
                pdf_attachments_recebidos.append(attachment.FileName)  # Anexar o nome do arquivo à lista de sucessos
                total_pdf_attachments += 1  # Contabilizar o sucesso para as métricas
            except Exception as e:
                pdf_attachments_falhas.append(attachment.FileName)  # Anexar o nome do arquivo à lista de falhas
                logging.error(f'Erro ao salvar anexo {attachment.FileName}: {e}')
                print(f'Erro ao salvar anexo {attachment.FileName}: {e}')
    
    # Se houve falhas no salvamento, registrar na planilha
    if len(pdf_attachments_falhas) > 0:
        data_processo = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        data_email = mail.ReceivedTime.strftime('%Y-%m-%d %H:%M:%S')
        registrar_falha_na_planilha(data_processo, data_email, emitente, titulo, pdf_attachments_recebidos, pdf_attachments_falhas)
    
    return pdf_saved, total_pdf_attachments

def process_unread_emails(maestro, log_label_execution):
    """
    Conecta ao Outlook, lê e-mails não lidos, salva anexos PDF e marca os e-mails como lidos.
    Retorna o total de processados, total de sucesso, total de falhas, anexos recebidos e anexos salvos.
    """
    total_processados = 0
    total_sucesso = 0
    total_falhas = 0
    total_anexos_pdf_recebidos = 0  # Contagem de PDFs recebidos
    total_anexos_pdf_salvos = 0  # Contagem de PDFs salvos com sucesso

    try:
        # Inicializa o COM para threads
        pythoncom.CoInitialize()
        
        # Conecta ao Outlook
        outlook = win32com.client.Dispatch("Outlook.Application").GetNamespace("MAPI")
        inbox = outlook.GetDefaultFolder(6)  # 6 refere-se à pasta Inbox

        # Filtra e-mails não lidos
        messages = inbox.Items
        messages = messages.Restrict("[UnRead] = True")
        messages.Sort("[ReceivedTime]", True)  # Ordena do mais recente para o mais antigo

        count = messages.Count
        logging.info(f'Iniciando processamento de {count} e-mails não lidos.')
        print(f'Iniciando processamento de {count} e-mails não lidos.')

        for i in range(count, 0, -1):
            total_processados += 1
            try:
                mail = messages.Item(i)
                emitente = mail.SenderEmailAddress
                titulo = mail.Subject
                
                # Verifica quantos anexos PDF o e-mail possui
                pdf_attachments_count = sum(1 for attachment in mail.Attachments if attachment.FileName.lower().endswith('.pdf'))
                
                if pdf_attachments_count > 0:
                    total_anexos_pdf_recebidos += pdf_attachments_count  # Atualizar a contagem de PDFs recebidos
                    received_time = mail.ReceivedTime
                    save_path = create_directory(BASE_SAVE_PATH, received_time)
                    pdf_saved, anexos_salvos = save_pdf_attachments(mail, save_path, emitente, titulo)
                    total_anexos_pdf_salvos += anexos_salvos  # Atualizar a contagem de PDFs salvos
                    
                    if pdf_saved:
                        total_sucesso += 1
                        logging.info(f'Anexos PDF processados para o e-mail de {received_time}')
                        print(f'Anexos PDF processados para o e-mail de {received_time}')
                # Marca o e-mail como lido
                mail.UnRead = False
                mail.Save()
            except Exception as e:
                total_falhas += 1
                logging.error(f'Erro ao processar o e-mail {i}: {e}')
                print(f'Erro ao processar o e-mail {i}: {e}')
                
                # Registrar erro na planilha de observabilidade
                data_processo = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                registrar_falha_na_planilha(data_processo, None, None, None, None, None, erro=str(e))
        
        logging.info('Processamento de e-mails concluído.')
        print('Processamento de e-mails concluído.')
    
    except Exception as e:
        logging.critical(f'Erro crítico no processamento de e-mails: {e}')
        print(f'Erro crítico no processamento de e-mails: {e}')
    
    finally:
        pythoncom.CoUninitialize()

    # Retornar os totais processados, sucessos, falhas, e contagem de PDFs recebidos e salvos
    return {
        "total_processados": total_processados,
        "total_sucesso": total_sucesso,
        "total_falhas": total_falhas,
        "total_anexos_pdf_recebidos": total_anexos_pdf_recebidos,
        "total_anexos_pdf_salvos": total_anexos_pdf_salvos
    }


def main():
    # Integração com o Maestro
    maestro = BotMaestroSDK.from_sys_args()
    execution = maestro.get_execution()

    print(f"Task ID is: {execution.task_id}")
    print(f"Task Parameters are: {execution.parameters}")

    log_label_execution = "log_execution_email_processing"
    
    # Registrar início da tarefa
    maestro.new_log_entry(
        activity_label=log_label_execution,
        values={
            "timestamp": datetime.datetime.now().strftime("%Y-%m-%d_%H-%M"),
            "event": "Início do processo de extração de e-mails",
            "status": "START",
            "total_processados": 0,
            "total_sucesso": 0,
            "total_falhas": 0,
            "total_anexos_pdf_recebidos": 0,
            "total_anexos_pdf_salvos": 0
        }
    )

    # Processar os e-mails e capturar os totais
    resultados = process_unread_emails(maestro, log_label_execution)

    # Registrar log único com resumo do processo
    maestro.new_log_entry(
        activity_label=log_label_execution,
        values={
            "timestamp": datetime.datetime.now().strftime("%Y-%m-%d_%H-%M"),
            "event": "Resumo do processo de e-mails",
            "status": "END",
            "total_processados": resultados["total_processados"],
            "total_sucesso": resultados["total_sucesso"],
            "total_falhas": resultados["total_falhas"],
            "total_anexos_pdf_recebidos": resultados["total_anexos_pdf_recebidos"],
            "total_anexos_pdf_salvos": resultados["total_anexos_pdf_salvos"]
        }
    )

    # Finalizar a tarefa no Maestro com os números reais
    maestro.finish_task(
        task_id=execution.task_id,
        status=AutomationTaskFinishStatus.SUCCESS,
        message="Processo de extração de e-mails concluído.",
        total_items=1,  # Número total de itens processados
        processed_items=1,  # Itens processados com sucesso
        failed_items=0  # Itens com falha
    )

if __name__ == "__main__":
    main()
