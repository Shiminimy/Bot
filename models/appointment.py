import sqlite3
import logging
from contextlib import closing  # Для безопасного закрытия соединения с БД

def save_appointment(user_id: int, day: str, time: str, doctor: str):
    """
    Сохраняет запись на приём в базу данных clinic.db.
    Использует защищённый блок try-except и контекстный менеджер closing.
    """
    try:
        # Открываем соединение с базой данных clinic.db
        with closing(sqlite3.connect('clinic.db')) as conn:
            # Включаем режим журнала WAL (write-ahead logging)
            # Это увеличивает устойчивость к сбоям и позволяет нескольким процессам работать с БД
            conn.execute("PRAGMA journal_mode=WAL")

            # Создаём курсор для выполнения SQL-запросов
            cursor = conn.cursor()

            # Выполняем SQL-запрос на добавление записи о приёме
            cursor.execute(
                "INSERT INTO appointments (user_id, day, time, doctor) VALUES (?, ?, ?, ?)",
                (user_id, day, time, doctor)
            )

            # Подтверждаем изменения (коммит)
            conn.commit()

    except sqlite3.IntegrityError as e:
        # Обработка ошибок целостности (например, дубликаты, ограничения UNIQUE)
        logging.error(f"Integrity error saving appointment: {e}")
        raise ValueError("Запись уже существует или данные некорректны")

    except sqlite3.Error as e:
        # Общая ошибка работы с базой данных
        logging.error(f"Database error saving appointment: {e}")
        raise

    except Exception as e:
        # Непредвиденная ошибка
        logging.error(f"Unexpected error in save_appointment: {e}")
        raise
