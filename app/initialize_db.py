import sqlite3

def initialize_db():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    cursor.execute('DROP TABLE IF EXISTS scraped_data')  # Drop the table if it exists

    cursor.execute('''
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

if __name__ == '__main__':
    initialize_db()
    print("Database initialized successfully.")
