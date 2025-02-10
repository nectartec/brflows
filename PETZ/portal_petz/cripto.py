import bcrypt
from db_connection import connect_to_db

def atualizar_senhas():
    conn = connect_to_db()
    cur = conn.cursor()

    # Busca todos os usuários
    cur.execute("SELECT usuario_id, senha_hash FROM usuarios")
    users = cur.fetchall()

    for user_id, senha in users:
        if not senha.startswith("$2b$"):  # Verifica se a senha já é um hash do bcrypt
            senha_hash = bcrypt.hashpw(senha.encode(), bcrypt.gensalt()).decode()
            cur.execute("UPDATE usuarios SET senha_hash = %s WHERE usuario_id = %s", (senha_hash, user_id))

    conn.commit()
    conn.close()
    print("Senhas atualizadas com sucesso!")

atualizar_senhas()
