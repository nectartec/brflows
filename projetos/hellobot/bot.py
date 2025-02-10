from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import pyautogui
import pandas as pd
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium import webdriver
from selenium.webdriver.edge.service import Service
from selenium.webdriver.edge.options import Options

# Import for the Desktop Bot
from botcity.core import DesktopBot

# Import for integration with BotCity Maestro SDK
from botcity.maestro import *

# Disable errors if we are not connected to Maestro
BotMaestroSDK.RAISE_NOT_CONNECTED = False

def main():
    # Runner passes the server url, the id of the task being executed,
    # the access token and the parameters that this task receives (when applicable).
    maestro = BotMaestroSDK.from_sys_args()
    ## Fetch the BotExecution with details from the task, including parameters
    execution = maestro.get_execution()
    execution = maestro.get_execution()

    print(f"Task ID is: {execution.task_id}")
    print(f"Task Parameters are: {execution.parameters}")

    bot = DesktopBot()

    HC_op = pd.read_excel(r"C:\\Users\\Public\\projetos\\hellobot\\files\\" + 'HC op.xlsx')
    HC = HC_op.loc[HC_op['Situação'] != "Demitido"]
    HC['CPF'] = HC['CPF'].apply(lambda x: str(x).zfill(11))
    # Lista de nomes dos arquivos das planilhas
    arquivos = ['ad1.xlsx']
    # Coluna específica que você deseja concatenar
    coluna_especifica = 'CPF'
    # Lista para armazenar os valores da coluna específica de cada planilha
    valores_coluna = []
    # Loop para ler cada planilha e armazenar os valores da coluna específica
    for arquivo in arquivos:
        df = pd.read_excel(r"C:\\Users\\Public\\projetos\\hellobot\\files\\" + arquivo, dtype={coluna_especifica: str})
        valores_coluna.append(df[coluna_especifica])
    # Concatenar os valores da coluna em uma única série
    serie = pd.concat(valores_coluna, ignore_index=True)
    serie_final = serie.to_frame(name='CPF')  # Converte a série em um DataFrame com nome de coluna 'CPF'
    # Mesclar com o DataFrame HC
    df_admissoes = pd.merge(serie_final, HC[['CPF', 'CHAPA']], on='CPF', how='left')
    df_admissoes_filtrada = df_admissoes[df_admissoes['CHAPA'].notna()]
    df_semchapa = df_admissoes[df_admissoes['CHAPA'].isna()]
    # Salvar o DataFrame resultante em um novo arquivo
    df_admissoes_filtrada.to_excel('admissoes.xlsx', index=False)
    df_semchapa.to_excel('sem_chapa.xlsx', index=False)
    time.sleep(2)
    
    ##### BAIXA DE FOTOS #####
    
    pyautogui.PAUSE=2.2
    base=pd.read_excel("admissoes.xlsx")
    # Inicialize o driver do Selenium
    # Inicialize o driver do Selenium
    #driver_path = r'C:\Users\fernanda.francisco\Downloads\edgedriver_win64 1\msedgedriver.exe'
    # Configurar o serviço do EdgeDriver
    #service = Service(executable_path=driver_path)
    # Configurar as opções do EdgeDriver
    #options = Options()
    # Inicializar o EdgeDriver com o serviço e opções
    driver = webdriver.Edge()
    driver.implicitly_wait(2)
    # Abra a página da web
    driver.get("https://petz.gupy.io/admission/companies/")
    # Tempo para posicionar o WE e o Chrome
    time.sleep(20)
    # Login
    driver.find_element(By.XPATH, '//*[@id="username"]').click()
    pyautogui.write("naiany.zamariolli@petz.com.br")
    driver.find_element(By.XPATH, '//*[@id="password"]').click()
    pyautogui.write("Mac@rio09")
    pyautogui.press('enter')
    time.sleep(60) 

    #try:
        # Espera até que o botão esteja presente e então clica nele
        #fechar_button = WebDriverWait(driver, 1).until(
            #EC.element_to_be_clickable((By.CSS_SELECTOR, "button[aria-label='Fechar']")))
        #fechar_button.click()
    #except TimeoutException:
        #print("Tempo limite excedido. O botão 'Fechar' não foi encontrado.")
    #except NoSuchElementException:
        #print("Elemento não encontrado, pulando interação.")
    #except Exception as e:
        #print(f"Erro ao tentar clicar no botão: {e}")
    
    # Troca de página
    #driver.find_element(By.XPATH, '//*[@id="navigate-between-products__product__title"]').click()
    #time.sleep(3)
    driver.find_element(By.XPATH, '//*[@id="root"]/div[4]/div/div[1]/div[2]/div/div[1]/div/div/div[1]/div/div[2]/ul/li[7]/button/div').click()
    
    # Itere sobre cada perfil
    for index, row in base.iterrows():
    
        chapa = row['CHAPA']

        #Download da foto
        driver.find_element(By.XPATH, '//*[@id="list-search-input"]').click()
        pyautogui.press('backspace',11)
        pyautogui.write(str(row['CPF']).zfill(11))
        pyautogui.press('enter')
        time.sleep(6)
        driver.find_element(By.XPATH,'//*[@id="pre-employee-table-card"]/div[2]/table/tbody').click()
        time.sleep(8)             #//*[@id="pre-employee-table-card"]/div[2]/table/tbody
        pyautogui.press('tab',2)
        pyautogui.press('enter')
        #Fechar popup
        #try:
        # Espera até que o botão esteja presente e então clica nele
            #fechar_button = WebDriverWait(driver, 1).until(
                #EC.element_to_be_clickable((By.CSS_SELECTOR, "button[aria-label='Fechar']")))
            #fechar_button.click()
            #tabs=3
        #except TimeoutException:
            #print("Tempo limite excedido. O botão 'Fechar' não foi encontrado.")
            #tabs=2
        #except NoSuchElementException:
            #print("Elemento não encontrado, pulando interação.")
            #tabs=2
        #except Exception as e:
            #print(f"Erro ao tentar clicar no botão: {e}")
            #tabs=2
        #time.sleep(1)   
        #pyautogui.press('tab',tabs)
        #pyautogui.press('enter')
        #driver.find_element_by_xpath("//*[contains(text(), 'Talvez mais tarde')]").click()
        #driver.find_element(By.XPATH,'/html/body/div[4]/div[2]/div/div/button[2]/span[1]').click()
        #driver.find_element(By.XPATH,'/html/body/div[5]/div[2]/div/div/button[2]/span[1]/div/span').click()
        #/html/body/div[4]/div[2]/div/div/button[2]/span[1]/div
        # Encontre a linha desejada com base em algum critério, como o texto em uma célula
        row = driver.find_element(By.XPATH, "//tr[contains(td, 'Selfie com Pet')]")
    
        # Encontre o botão dentro dessa linha
        row.find_element(By.XPATH, ".//button[contains(@id, 'icon-download-form-button')]").click()
    
        #driver.find_element(By.XPATH, "//*[@id='b3c21c62-94b6-4c95-9276-020037899ac1-tab']/div/div/div/table/tbody/tr[11]/button[contains(@class, 'icon-button')]").click()
        time.sleep(1)#####1.5
        pyautogui.press('down')
        pyautogui.press('enter')
        #driver.find_element(By.XPATH,'//*[@class="jss461"]').click()
        time.sleep(7)####10   
        #Extrair e renomear
        pyautogui.keyDown('alt')
        pyautogui.press('tab')
        pyautogui.keyUp('alt')
        #pyautogui.press('up',70)
        pyautogui.press('F5')
        pyautogui.moveTo(212, 94)
        pyautogui.mouseDown()
        pyautogui.mouseUp()
        time.sleep(1)
        pyautogui.mouseDown()
        pyautogui.mouseUp()
        pyautogui.press('F5')
        pyautogui.moveTo(460, 150)
        pyautogui.mouseDown()
        pyautogui.mouseUp()
        pyautogui.press('enter')
        pyautogui.press('down')
        pyautogui.press('enter')
        pyautogui.press('down')
        pyautogui.press('enter')
        pyautogui.press('down')
        pyautogui.hotkey('ctrl','c')
        pyautogui.moveTo(928, 67)
        pyautogui.mouseDown()
        pyautogui.mouseUp()
        pyautogui.press('backspace')
        pyautogui.write(r'C:\Users\naiany.zamariolli\Documents\ROBO\Fotos')
        pyautogui.press('enter')
        pyautogui.hotkey('ctrl','v')
        pyautogui.moveTo(278, 93)
        pyautogui.mouseDown()
        pyautogui.mouseUp()
        time.sleep(3)
        #pyautogui.moveTo(278, 93)
        pyautogui.mouseDown()
        pyautogui.mouseUp()
        pyautogui.press('F5')
        pyautogui.moveTo(606, 128)
        pyautogui.mouseDown()
        pyautogui.mouseUp()
        pyautogui.press('F2')
        pyautogui.write(str(chapa).zfill(8))
        pyautogui.press('enter')
        pyautogui.moveTo(928, 67)
        pyautogui.mouseDown()
        pyautogui.mouseUp()
        pyautogui.press('backspace')
        pyautogui.write(r'C:\Users\naiany.zamariolli\Downloads')
        pyautogui.press('enter')
        pyautogui.keyDown('alt')
        pyautogui.press('tab')
        pyautogui.keyUp('alt')
        # Volte para a página anterior (ou para a página principal de perfis)
        driver.back()
    
        time.sleep(8)
        #Fechar popup
        #try:
        # Espera até que o botão esteja presente e então clica nele
            #fechar_button = WebDriverWait(driver, 1).until(
                #EC.element_to_be_clickable((By.CSS_SELECTOR, "button[aria-label='Fechar']")))
            #fechar_button.click()
        #except TimeoutException:
            #print("Tempo limite excedido. O botão 'Fechar' não foi encontrado.")
        #except NoSuchElementException:
            #print("Elemento não encontrado, pulando interação.")
        #except Exception as e:
            #print(f"Erro ao tentar clicar no botão: {e}")
    pyautogui.alert("Processo concluído")
    # Alerta de conclusão
    bot.alert("Processo concluído")
    maestro.finish_task(
        task_id=execution.task_id,
        status=AutomationTaskFinishStatus.SUCCESS,
        message="Task Finished OK."
    )

    def not_found(bot, label):
        print(f"Elemento não encontrado: {label}")


def not_found(label):
    print(f"Element not found: {label}")


if __name__ == '__main__':
    main()