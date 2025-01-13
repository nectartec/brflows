import sqlite3

# Conectando ao banco (se não existir, será criado)
conn = sqlite3.connect('pedidos.db')

# Criando uma tabela de exemplo
cursor = conn.cursor()
cursor.execute('''
CREATE TABLE IF NOT EXISTS pedidos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    cliente TEXT NOT NULL,
    email TEXT NOT NULL,
    produtos TEXT NOT NULL,
    total REAL NOT NULL
)
''')

# Inserindo um exemplo de pedido
cursor.execute('''
INSERT INTO pedidos (cliente, email, produtos, total)
VALUES ('João da Silva', 'joao@example.com', 'Produto A, Produto B', 150.75)
''')

# Confirmando as mudanças e fechando
conn.commit()
conn.close()

print("Banco de dados criado e exemplo de pedido inserido.")