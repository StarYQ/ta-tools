import sqlite3

def initialize_db():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    #existing tables
    cursor.execute('DROP TABLE IF EXISTS scraped_data')
    cursor.execute('''
    CREATE TABLE scraped_data (
        username TEXT PRIMARY KEY,
        class_name TEXT,
        student_list TEXT,
        homework_names TEXT,
        last_scraped TEXT
    )
    ''')

    #new meetings table
    cursor.execute('DROP TABLE IF EXISTS meetings')
    cursor.execute('''
    CREATE TABLE meetings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT,
        start TEXT,
        end TEXT
    )
    ''')

    conn.commit()
    conn.close()

if __name__ == '__main__':
    initialize_db()
    print("Database initialized successfully.")