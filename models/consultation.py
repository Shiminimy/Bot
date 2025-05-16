import sqlite3
from datetime import datetime

def save_consultation(patient_id: int, doctor_type: str, question: str, answer: str = None):
    with sqlite3.connect('clinic.db') as conn:
        conn.execute(
            "INSERT INTO consultations (patient_id, doctor_type, question, answer, created_at) VALUES (?, ?, ?, ?, ?)",
            (patient_id, doctor_type, question, answer, datetime.now())
        )
        conn.commit()