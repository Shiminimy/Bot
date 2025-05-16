# db_queries.py
import sqlite3
from config.settings import DB_PATH

def get_all_appointments():
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM appointments")
        return cursor.fetchall()

def get_occupied_appointments():
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("""
            SELECT a.*, u.first_name, u.last_name 
            FROM appointments a
            JOIN users u ON a.user_id = u.user_id
        """)
        return cursor.fetchall()