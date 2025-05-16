import sqlite3
import logging

def init_db():
    try:
        conn = sqlite3.connect('clinic.db')
        cursor = conn.cursor()

        # Таблица пользователей
        cursor.execute('''CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            first_name TEXT,
            last_name TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )''')

        # Таблица записей
        cursor.execute('''CREATE TABLE IF NOT EXISTS appointments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            day TEXT,
            time TEXT,
            doctor TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(user_id) ON DELETE CASCADE
        )''')

        # Таблица консультаций
        cursor.execute('''CREATE TABLE IF NOT EXISTS consultations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            message TEXT,
            response TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(user_id) ON DELETE CASCADE
        )''')

        # Индексы
        cursor.execute('''CREATE INDEX IF NOT EXISTS idx_appointments_day_time 
                       ON appointments(day, time)''')
        cursor.execute('''CREATE INDEX IF NOT EXISTS idx_appointments_user 
                       ON appointments(user_id)''')

        conn.commit()
        logging.info("Database initialized successfully")
    except sqlite3.Error as e:
        logging.error(f"Failed to initialize database: {e}")
        raise
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    init_db()