import subprocess
import os

# Import for the Desktop Bot
from botcity.core import DesktopBot

# Import for integration with BotCity Maestro SDK
from botcity.maestro import *

# Disable errors if we are not connected to Maestro
BotMaestroSDK.RAISE_NOT_CONNECTED = False

def main():
    # Chamar o script de extração de PDF
    script_path = r'C:\Projetos Botcity\1. Automação NFe Totvs\RPAPetz\src\pdfextract.py'
    subprocess.run(['python', script_path], check=True)

    # Runner passes the server url, the id of the task being executed,
    # the access token and the parameters that this task receives (when applicable).
    maestro = BotMaestroSDK.from_sys_args()
    # Fetch the BotExecution with details from the task, including parameters
    execution = maestro.get_execution()

    print(f"Task ID is: {execution.task_id}")
    print(f"Task Parameters are: {execution.parameters}")

    bot = DesktopBot()
    
    # Abrir o atalho da aplicação
    bot.execute('C:\\smartclientR2210_HML\\TOTVS-12-HML.lnk')
    
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
    #Após login, clicar para pesquisar a tela
    bot.right_click_at(30,   370)
    bot.type_keys("Inclusao massiva")
    bot.mouse_move(150, 365)
    bot.wait(1000)
    bot.click_at(150, 365)
    bot.wait(40000)
    bot.click_at(445, 295)
    for i in range (1, 15):
        bot.delete()
    bot.paste("C:\Projetos Botcity\massivo\massivo.csv")
    bot.click_at(840, 515)
    bot.wait(5000)
    bot.click_at(220, 190)
    bot.wait(1000)
    bot.click_at(890, 480)
    bot.wait(3000)
    bot.click_at(875, 475) # Fim do upload
    bot.wait(1000)
    bot.click_at(10, 370)
    for i in range (0, 20):
        bot.delete()
    # Agora, vamos abrir a tela 2
    bot.click_at(13,   370)
    bot.paste("Solicitacao de pagamento")
    bot.wait(1000)
    bot.click_at(150, 365)
    bot.wait(25000)
    bot.click_at(1335, 180)
    bot.wait(1000)
    bot.click_at(440, 335)
    bot.click_at(440, 335)
    bot.wait(1000)
    bot.click_at(860, 630)
    bot.wait(1000)
    # Aqui eu clico para visualizar o item
    bot.click_at(270, 180)
    bot.wait(1000)
    bot.click_at(620, 600)
    bot.wait(1000)
    bot.control_c()
    num_nf = bot.get_clipboard()
    bot.click_at(1150, 470)
    bot.wait(1000)
    bot.control_c()
    num_forn = bot.get_clipboard()
    bot.click_at(1320, 120) # Aqui eu sai do item
    bot.wait(1000)
    # Agora vou começar a incluir o anexo do item
    bot.click_at(170, 190)
    bot.wait(1000)
    bot.click_at(360, 185)
    bot.wait(1000)
    bot.click_at(990,  125) # Aqui é pra clicar em Oiutras Ações
    bot.wait(1000)
    bot.click_at(975, 290) # Aqui clicar em Incluir Anexo
    bot.wait(1000)
    bot.click_at(635, 600) # Aqui clicar em Anexar
    bot.wait(1000)
    bot.paste(r"C:\Users\roger.oliveira\Downloads\19371 PETZ CARREFOUR ANCHIETA.pdf")
    bot.wait(1000) 
    bot.click_at(850, 520)
    bot.wait(5000)
    bot.click_at(900, 600)
    bot.wait(1000)
    bot.click_at(1290, 120) # Clicar em Confirmar
    bot.wait(1000)
    bot.click_at(810, 470)
    # Uncomment to mark this task as finished on BotMaestro
    # maestro.finish_task(

    #     task_id=execution.task_id,
    #     status=AutomationTaskFinishStatus.SUCCESS,
    #     message="Task Finished OK."
    # )

def not_found(label):
    print(f"Element not found: {label}")

if __name__ == '__main__':
    main()