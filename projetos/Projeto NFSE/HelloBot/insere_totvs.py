import csv
import subprocess
import os
from botcity.core import DesktopBot
from botcity.maestro import *
import datetime

# Desabilitar erros caso não esteja conectado ao Maestro
BotMaestroSDK.RAISE_NOT_CONNECTED = False

# Instanciar o Maestro SDK
maestro = BotMaestroSDK.from_sys_args()

def contar_linhas_csv(caminho_csv):
    try:
        with open(caminho_csv, newline='', encoding='utf-8') as csvfile:
            reader = csv.reader(csvfile)
            return sum(1 for row in reader) - 1  # Subtrair 1 para ignorar o cabeçalho
    except Exception as e:
        print(f"Erro ao contar as linhas do CSV: {str(e)}")
        return 0

def main():
    # Fetch the BotExecution with details from the task, including parameters
    execution = maestro.get_execution()

    print(f"Task ID is: {execution.task_id}")
    print(f"Task Parameters are: {execution.parameters}")

    bot = DesktopBot()

    # Definir o label de log
    log_label_execution = "log_execution"

    # Registrar início da tarefa
    maestro.new_log_entry(
        activity_label=log_label_execution,
        values={
            "timestamp": datetime.datetime.now().strftime("%Y-%m-%d_%H-%M"),
            "event": "Início do processo",
            "status": "START",
            "total_processados": 0,
            "total_sucesso": 0,
            "total_falhas": 0,
            "arquivo_pdf": "N/A",
            "error_message": "N/A"
        }
    )

    bot = DesktopBot()
    
    try:
        # Abrir o atalho da aplicação TOTVS
        bot.execute('C:\\smartclientR2210\\TOTVS-12.lnk')
        # Aguardar a aplicação abrir
        bot.wait(5000)
        
        # Preencher o campo de usuário
        bot.paste('rpa.corp')
        bot.tab()

        # Preencher o campo de senha
        bot.wait(1000)
        bot.paste('Petz@2025')

        # Clicar no botão Entrar
        bot.tab()
        bot.tab()
        bot.enter()

        bot.wait(4000)  

        # Fazer login e selecionar módulo de compras
        bot.tab()
        bot.tab()
        bot.tab()
        bot.type_keys("02")
        bot.tab()
        
        bot.wait(1000)
        bot.enter()
        bot.enter()
        bot.wait(5000)
        # Registrar login bem-sucedido
        maestro.new_log_entry(
            activity_label=log_label_execution,
            values={
                "timestamp": datetime.datetime.now().strftime("%Y-%m-%d_%H-%M"),
                "event": "Login bem-sucedido",
                "status": "SUCCESS",
                "total_processados": 0,
                "total_sucesso": 0,
                "total_falhas": 0,
                "arquivo_pdf": "N/A",
                "error_message": "N/A"
            }
        )
        #Após login, clicar para pesquisar a tela
        # bot.right_click_at(30,   370)
        # bot.type_keys("Inclusao massiva SP")
        # bot.mouse_move(150, 365)
        # bot.wait(1000)
        # bot.click_at(150, 365)
        # bot.wait(50000)
        # bot.click_at(445, 318)
        # for i in range (1, 15):
        #     bot.delete()
        # bot.paste(f"C:/Users/roger.oliveira/Documents/PDFExtract/PDFExtract/files/massivo/massivo.csv")
        # bot.click_at(840, 535)
        #  # Calcular o tempo de espera dinamicamente
        # csv_path_massivo = r'C:/Users/roger.oliveira/Documents/PDFExtract/PDFExtract/files/massivo/massivo.csv'
        # numero_linhas = contar_linhas_csv(csv_path_massivo)
        # tempo_espera = 60000 + (5000 * numero_linhas)
        # print(f"Tempo de espera ajustado para: {tempo_espera} milissegundos")
        
        # bot.wait(tempo_espera)  # Espera dinâmica com base no número de linhas

        # bot.click_at(220, 190)
        # bot.wait(1000)
        # bot.click_at(890, 480)
        # bot.wait(5000)
        # bot.click_at(875, 475) # Fim do upload
        # # Registrar sucesso na inclusão massiva
        # maestro.new_log_entry(
        #     activity_label=log_label_execution,
        #     values={                "timestamp": datetime.datetime.now().strftime("%Y-%m-%d_%H-%M"),
        #         "event": "Inclusão massiva concluída",
        #         "status": "SUCCESS",
        #         "total_processados": 1,
        #         "total_sucesso": 1,
        #         "total_falhas": 0,
        #         "arquivo_pdf": "N/A",
        #         "error_message": "N/A"
        #     }
        # )
        # bot.wait(1000)
        # bot.click_at(10, 370)
        # for i in range (0, 20):
        #     bot.delete()

        # Abrir o CSV e iterar pelas linhas
        csv_path = r'C:\Users\roger.oliveira\Documents\PDFExtract\PDFExtract\files\extracted_infos\extracted_nfs.csv'
        with open(csv_path, newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile, delimiter=';')

            # Começar o processo de anexo
            bot.click_at(13, 370)
            bot.paste("Solicitacao de pagamento")
            bot.wait(1000)
            bot.click_at(150, 365)
            bot.wait(30000)

            for row in reader:
                numero_nf = row['Número da Nota Fiscal']
                print("Processando NF: ", numero_nf)
                caminho_arquivo = row['Caminho do Arquivo'].replace('\\', '/')
                print("Caminho do arquivo: ", caminho_arquivo)
                # Clicar no botão "Filtrar"
                bot.click_at(1338, 183)
                bot.wait(2000)
                # Clicar no filtro "Solicitações Criadas"
                bot.click_at(440, 296)
                bot.wait(2000)
                # Clicar no botão para rolar para baixo
                bot.click_at(930, 520)
                bot.wait(2000)
                # Clicar no botão para filtrar NF
                bot.click_at(439, 480)
                bot.wait(2000)
                # Clicar no botão "Aplicar Filtros Selecionados"
                bot.click_at(860, 636)
                bot.wait(2000)
                # Informar o número da NF a ser pesquisada
                bot.type_keys(str(int(numero_nf)))
                bot.wait(2000)
                # Clicar em Confirmar para aplicar o filtro
                bot.click_at(825, 535)
                bot.wait(2000)
                # Clicar em Alterar para inclusão do anexo
                bot.click_at(130, 185)
                bot.wait(3000)
                # Clicar em Outras ações para inclusão do anexo
                bot.click_at(985, 125)
                bot.wait(3000)
                # Clicar em Incluir Anexo
                bot.click_at(974, 273)
                bot.wait(3000)
                # Clicar em Anexar
                bot.click_at(623, 600) 
                bot.wait(3000)
                # Endereçar arquivo a ser anexado
                bot.paste(caminho_arquivo)
                bot.wait(3000) 
                bot.click_at(842, 536)
                bot.wait(5000)
                bot.click_at(900, 600)
                bot.wait(3000)
                bot.click_at(1290, 120) # Clicar em Confirmar
                bot.wait(3000)
                bot.click_at(880, 470) # Clica em Iniciar Fluxo de Aprovação
                bot.wait(3000)

                # Registrar que o arquivo foi anexado com sucesso
                maestro.new_log_entry(
                    activity_label=log_label_execution,
                    values={
                        "timestamp": datetime.datetime.now().strftime("%Y-%m-%d_%H-%M"),
                        "event": f"Arquivo PDF {caminho_arquivo} anexado com sucesso",
                        "status": "SUCCESS",
                        "total_processados": 1,
                        "total_sucesso": 1,
                        "total_falhas": 0,
                        "arquivo_pdf": caminho_arquivo,
                        "error_message": "N/A"
                    }
                )

                # Clicar em Remover filtros após 15s para poder filtrar o próximo
                bot.wait(3000)
                bot.click_at(1210, 145)
                bot.click_at(1210, 145)
                bot.click_at(1210, 145)
                bot.wait(5000)

    except Exception as e:
        # Registrar erro durante o processo
        maestro.new_log_entry(
            activity_label=log_label_execution,
            values={
                "timestamp": datetime.datetime.now().strftime("%Y-%m-%d_%H-%M"),
                "event": f"Erro durante o processo: e",
                "status": "FAILED",
                "total_processados": 0,
                "total_sucesso": 0,
                "total_falhas": 1,
                "arquivo_pdf": "N/A",
                "error_message": str(e)
            }
        )
        print(f"Erro: {str(e)}")

    finally:
        # Registrar finalização da tarefa
        maestro.new_log_entry(
            activity_label=log_label_execution,
            values={
                "timestamp": datetime.datetime.now().strftime("%Y-%m-%d_%H-%M"),
                "event": "Tarefa finalizada",
                "status": "END",
                "total_processados": 1,
                "total_sucesso": 1,
                "total_falhas": 0,
                "arquivo_pdf": "N/A",
                "error_message": "N/A"
            }
        )
        maestro.finish_task(
            task_id=execution.task_id,
            status=AutomationTaskFinishStatus.SUCCESS,
            message="Task Finished OK.",
            total_items=1, # Número total de itens processados
            processed_items=1 # Número de itens processados com sucesso
        )

if __name__ == '__main__':
    main()
