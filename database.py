import sqlite3
import json
from datetime import datetime

def create_connection():
    conn = sqlite3.connect('database.db')
    return conn

def create_tables():
    conn = create_connection()
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                 username TEXT NOT NULL,
                 password TEXT NOT NULL)''')

    # Drop and recreate scraped_data table to ensure schema is correct
    c.execute('DROP TABLE IF EXISTS scraped_data')
    c.execute('''
    CREATE TABLE scraped_data (
        username TEXT PRIMARY KEY,
        class_name TEXT,
        student_list TEXT,
        homework_names TEXT,
        last_scraped TEXT
    )
    ''')

    conn.commit()
    conn.close()

def insert_user(username, password):
    conn = create_connection()
    c = conn.cursor()
    c.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
    conn.commit()
    conn.close()

def get_user(username, password=None):
    conn = create_connection()
    c = conn.cursor()
    if password:
        c.execute("SELECT * FROM users WHERE username = ? AND password = ?", (username, password))
    else:
        c.execute("SELECT * FROM users WHERE username = ?", (username,))
    user = c.fetchone()
    conn.close()
    if user:
        return {'id': user[0], 'username': user[1], 'password': user[2]}
    else:
        return None

def store_scraped_data(username, data):
    conn = create_connection()
    c = conn.cursor()
    c.execute("REPLACE INTO scraped_data (username, class_name, student_list, homework_names, last_scraped) VALUES (?, ?, ?, ?, ?)",
              (username, data['class_name'], json.dumps(data['student_list']), json.dumps(data['homework_names']), data['last_scraped']))
    conn.commit()
    conn.close()

def get_scraped_data(username):
    conn = create_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM scraped_data WHERE username = ?", (username,))
    data = c.fetchone()
    conn.close()
    
    print(data)  # Debugging line to print the fetched data
    
    if data:
        return {
            'class_name': data[1],
            'student_list': json.loads(data[2]) if data[2] else [],
            'homework_names': json.loads(data[3]) if data[3] else [],
            'last_scraped': data[4] if len(data) > 4 and data[4] else None
        }
    else:
        return None
