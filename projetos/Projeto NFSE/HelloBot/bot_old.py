import subprocess
import os
from botcity.core import DesktopBot
from botcity.maestro import *
import datetime

# Desabilitar erros caso não esteja conectado ao Maestro
BotMaestroSDK.RAISE_NOT_CONNECTED = False

# Instanciar o Maestro SDK
maestro = BotMaestroSDK.from_sys_args()

def main():
    # Fetch the BotExecution with details from the task, including parameters
    execution = maestro.get_execution()

    print(f"Task ID is: {execution.task_id}")
    print(f"Task Parameters are: {execution.parameters}")

    bot = DesktopBot()

    #script_path = r'C:\Users\roger.oliveira\Documents\Projeto NFSE\HelloBot\src\pdfextract.py'
    #subprocess.run(['python', script_path], check=True)

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
        bot.execute('C:\\smartclientR2210_HML\\TOTVS-12-HML.lnk')
        # Aguardar a aplicação abrir
        bot.wait(5000)
        
        # Preencher o campo de usuário
        bot.paste('rpa.corp')
        bot.tab()

        # Preencher o campo de senha
        bot.wait(1000)
        bot.paste('Petz@2025***')

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
        
        # #Após login, clicar para pesquisar a tela
        # bot.right_click_at(30,   370)
        # bot.type_keys("Inclusao massiva SP")
        # bot.mouse_move(150, 365)
        # bot.wait(1000)
        # bot.click_at(150, 365)
        # bot.wait(40000)
        # bot.click_at(445, 295)
        # for i in range (1, 15):
        #     bot.delete()
        # bot.paste(f"C:/Users/roger.oliveira/Documents/PDFExtract/PDFExtract/files/massivo/massivo.csv")
        # bot.click_at(840, 515)
        # bot.wait(10000)
        # bot.click_at(220, 190)
        # bot.wait(1000)
        # bot.click_at(890, 480)
        # bot.wait(5000)
        # bot.click_at(875, 475) # Fim do upload
        # # Registrar sucesso na inclusão massiva
        # maestro.new_log_entry(
        #     activity_label=log_label_execution,
        #     values={
        #         "timestamp": datetime.datetime.now().strftime("%Y-%m-%d_%H-%M"),
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
        bot.click_at(13,   370)
        bot.paste("Solicitacao de pagamento")
        bot.wait(1000)
        bot.click_at(150, 365)
        bot.wait(60000)
        #################################
        # AQUI COMEÇA O LOOP
        # Clicar no botão "Filtrar"
        bot.click_at(1338, 183)
        bot.wait(1000)
        # Clicar no botão para rolar para baixo
        bot.click_at(930, 520)
        bot.wait(1000)
        # Clicar no botão para filtrar NF
        bot.click_at(439, 480)
        bot.wait(1000)
        # Clicar no botão "Aplicar Filtros Selecionados"
        bot.click_at(860, 636)
        bot.wait(1000)
        # Informar o número da NF a ser pesquisada
        bot.paste("19371")
        bot.wait(1000)
        # Clicar em Confirmar para aplicar o filtro
        bot.click_at(825, 535)
        bot.wait(1000)
        # Clicar em Alterar para inclusão do anexo
        bot.click_at(135, 185)
        bot.wait(1000)
        # Clicar em Outras ações para inclusão do anexo
        bot.click_at(985, 125)
        bot.wait(1000)
        # Clicar em Incluir Anexo
        bot.click_at(1000, 290)
        bot.wait(1000)
        # Clicar em Anexar
        bot.click_at(635, 600) 
        bot.wait(1000)
        # Endereçar arquivo a ser anexado
        bot.paste(r"C:\Users\roger.oliveira\Downloads\19371 PETZ CARREFOUR ANCHIETA.pdf")
        bot.wait(1000) 
        bot.click_at(850, 520)
        bot.wait(10000)
        bot.click_at(900, 600)
        bot.wait(1000)
        bot.click_at(1290, 120) # Clicar em Confirmar
        bot.wait(1000)
        bot.click_at(810, 470)
        bot.wait(1000)
        # Clicar em Remover filtros após 30s para poder filtrar o próximo
        bot.wait(40000)
        bot.click_at(1210, 150)
        # bot.wait(40000)
        # bot.click_at(1335, 180)
        # bot.wait(1000)
        # bot.click_at(440, 335)
        # bot.click_at(440, 335)
        # bot.wait(1000)
        # bot.click_at(860, 630)
        # bot.wait(1000)
        # # Aqui eu clico para visualizar o item
        # bot.click_at(270, 180)
        # bot.wait(1000)
        # bot.click_at(620, 600)
        # bot.wait(1000)
        # bot.control_c()
        # num_nf = bot.get_clipboard()
        # bot.click_at(1150, 470)
        # bot.wait(1000)
        # bot.control_c()
        # num_forn = bot.get_clipboard()
        # bot.click_at(1320, 120) # Aqui eu sai do item
        # bot.wait(1000)
        # # Agora vou começar a incluir o anexo do item
        # bot.click_at(170, 190)
        # bot.wait(1000)
        # bot.click_at(360, 185)
        # bot.wait(1000)
        # bot.click_at(990,  125) # Aqui é pra clicar em Oiutras Ações
        # bot.wait(1000)
        # bot.click_at(975, 290) # Aqui clicar em Incluir Anexo
        # bot.wait(1000)
        # bot.click_at(635, 600) # Aqui clicar em Anexar
        # bot.wait(1000)
        # bot.paste(r"C:\Users\roger.oliveira\Downloads\19371 PETZ CARREFOUR ANCHIETA.pdf")
        # bot.wait(1000) 
        # bot.click_at(850, 520)
        # bot.wait(10000)
        # bot.click_at(900, 600)
        # bot.wait(1000)
        # bot.click_at(1290, 120) # Clicar em Confirmar
        # bot.wait(1000)
        # bot.click_at(810, 470)
        # Registrar que os números foram extraídos com sucesso
        # maestro.new_log_entry(
        #     activity_label=log_label_execution,
        #     values={
        #         "timestamp": datetime.datetime.now().strftime("%Y-%m-%d_%H-%M"),
        #         "event": "Número da NF e Fornecedor extraídos",
        #         "status": "SUCCESS",
        #         "total_processados": 1,
        #         "total_sucesso": 1,
        #         "total_falhas": 0,
        #         "arquivo_pdf": "N/A",
        #         "error_message": "N/A",
        #         "nf": num_nf,
        #         "fornecedor": num_forn
        #     }
        # )

        # Registrar que o arquivo foi anexado com sucesso
        maestro.new_log_entry(
            activity_label=log_label_execution,
            values={
                "timestamp": datetime.datetime.now().strftime("%Y-%m-%d_%H-%M"),
                "event": "Arquivo PDF anexado com sucesso",
                "status": "SUCCESS",
                "total_processados": 1,
                "total_sucesso": 1,
                "total_falhas": 0,
                "arquivo_pdf": r"19371 PETZ CARREFOUR ANCHIETA.pdf",
                "error_message": "N/A"
            }
        )

    except Exception as e:
        # Registrar erro durante o processo
        maestro.new_log_entry(
            activity_label=log_label_execution,
            values={
                "timestamp": datetime.datetime.now().strftime("%Y-%m-%d_%H-%M"),
                "event": "Erro durante o processo",
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