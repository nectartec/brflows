import time
import threading
from pywinauto import Application

TERA_TERM_PATH = r"C:\Users\roger.oliveira\Downloads\TTERMPRO_HML\TTERMPRO_HML\ttermpro.exe"

CREDENTIALS = [
    {"username": "rpa.corp",  "password": "Petz@2025***"},
    {"username": "rpa.corp1", "password": "Petz@2025***"},
    {"username": "rpa.corp2", "password": "Petz@2025***"}
]

# Se quiser abrir mais de 1 janela por usuário, altere aqui.
# (por exemplo, 2 janelas para cada dos 3 usuários, total 6 janelas)
NUM_JANELAS_POR_USUARIO = 3

def automatizar_tera_term(usuario_totvs, senha_totvs):
    """Abre e automatiza o Tera Term usando Pywinauto, para o usuário e senha especificados."""
    # Inicia o Tera Term
    app = Application(backend="win32").start(TERA_TERM_PATH)
    
    # Aguarda o Tera Term ficar disponível
    time.sleep(20)
    main_window = app.window(title_re=".*Tera Term.*", found_index=0)
    main_window.wait("exists", timeout=20)
    main_window.wait("ready",  timeout=20)

    # Sequência de teclas e caracteres (login, senha, menus, etc.)
    main_window.send_keystrokes("{ENTER}")
    time.sleep(5)
    main_window.send_keystrokes("{ENTER}")
    time.sleep(2)
    main_window.send_keystrokes("{ENTER}")
    time.sleep(2)

    # Digita o usuário
    main_window.send_chars(usuario_totvs)
    main_window.send_keystrokes("{ENTER}")
    time.sleep(2)

    # Digita a senha
    main_window.send_chars(senha_totvs)
    main_window.send_keystrokes("{ENTER}")
    time.sleep(2)

    # Exemplo de sequência adicional de teclas (você ajusta conforme a necessidade)
    main_window.send_keystrokes("{ENTER}")
    time.sleep(2)
    main_window.send_keystrokes("{DOWN}")
    main_window.send_keystrokes("{ENTER}")  # Cadastros
    time.sleep(3)
    main_window.send_keystrokes("{ENTER}")  # Etiquetas
    time.sleep(3)
    main_window.send_keystrokes("{ENTER}")
    time.sleep(3)
    main_window.send_keystrokes("{ENTER}")
    time.sleep(3)
    main_window.send_keystrokes("{ENTER}")
    time.sleep(3)

def main():
    threads = []

    # Para cada credencial, vamos abrir 'NUM_JANELAS_POR_USUARIO' janelas
    for cred in CREDENTIALS:
        usuario = cred["username"]
        senha   = cred["password"]

        for _ in range(NUM_JANELAS_POR_USUARIO):
            t = threading.Thread(target=automatizar_tera_term, args=(usuario, senha))
            t.start()
            threads.append(t)

    print(f"Inicializando as janelas...")

    # Aguarda todas as threads finalizarem
    for t in threads:
        t.join()

    print("Todas as janelas foram abertas e automatizadas simultaneamente.")

if __name__ == "__main__":
    main()
