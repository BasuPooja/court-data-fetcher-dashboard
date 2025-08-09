import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), 'court_data.db')

def log_query(case_number):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS queries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            case_number TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    cursor.execute('INSERT INTO queries (case_number) VALUES (?)', (case_number,))
    conn.commit()
    conn.close()
