import sqlite3
import logging
from contextlib import closing

def save_user(user_id: int, first_name: str, last_name: str):
    """Безопасное сохранение пользователя с проверкой существования"""
    try:
        with closing(sqlite3.connect('clinic.db')) as conn:
            conn.execute("PRAGMA journal_mode=WAL")
            cursor = conn.cursor()
            
            # Проверяем существование пользователя
            cursor.execute("SELECT 1 FROM users WHERE user_id = ?", (user_id,))
            
            if cursor.fetchone():
                # Обновляем данные
                cursor.execute(
                    "UPDATE users SET first_name = ?, last_name = ? WHERE user_id = ?",
                    (first_name, last_name, user_id)
                )
            else:
                # Создаем нового пользователя
                cursor.execute(
                    "INSERT INTO users (user_id, first_name, last_name) VALUES (?, ?, ?)",
                    (user_id, first_name, last_name)
                )
            conn.commit()
            
    except sqlite3.IntegrityError as e:
        logging.warning(f"User {user_id} already exists: {e}")
        raise
    except sqlite3.Error as e:
        logging.error(f"Database error saving user {user_id}: {e}")
        raise
    except Exception as e:
        logging.error(f"Unexpected error in save_user: {e}")
        raise