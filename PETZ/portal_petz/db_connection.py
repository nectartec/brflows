import psycopg2

def connect_to_db():
    return psycopg2.connect(
        host="localhost",  # Altere para o host do seu banco
        database="petz",  # Nome do banco
        user="postgres",  # Usuário do banco
        password="admin"  # Senha do banco
    )
