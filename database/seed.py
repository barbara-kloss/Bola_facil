"""
Script para popular o banco de dados com dados iniciais
"""

import sqlite3
from datetime import datetime, timedelta

def seed_database():
    """Insere dados iniciais no banco de dados"""
    
    conn = sqlite3.connect('database/bolao.db')
    cursor = conn.cursor()
    
    # TODO: Inserir usuários, jogos e dados de teste
    
    conn.commit()
    conn.close()
    print("Banco de dados populado com sucesso!")

if __name__ == '__main__':
    seed_database()
