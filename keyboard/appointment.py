from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import sqlite3
import logging
from contextlib import closing
from config.settings import WORK_HOURS, WORK_MINUTES

def days_keyboard(week_manager=None):
    """Клавиатура с днями недели"""
    days = ["Понедельник", "Вторник", "Среда", "Четверг", "Пятница"]
    buttons = []
    
    for day in days:
        if week_manager and hasattr(week_manager, 'is_day_available') and not week_manager.is_day_available(day):
            buttons.append([InlineKeyboardButton(
                text=f"❌ {day} (недоступен)",
                callback_data="day_unavailable"
            )])
        else:
            buttons.append([InlineKeyboardButton(
                text=f"📅 {day}",
                callback_data=f"day_{day}"
            )])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def times_keyboard(day: str):
    """Клавиатура с 30-минутными интервалами"""
    buttons = []
    try:
        with closing(sqlite3.connect('clinic.db')) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT time FROM appointments WHERE day=?", (day,))
            busy_times = {row[0] for row in cursor.fetchall()}
            
            for hour in WORK_HOURS:
                for minute in WORK_MINUTES:
                    # Пропускаем 13:30 если не нужно
                    if hour == 13 and minute == '30':
                        continue
                        
                    time_str = f"{hour}:{minute}"
                    status = "⛔ занято" if time_str in busy_times else "🕒"
                    buttons.append([
                        InlineKeyboardButton(
                            text=f"{status} {time_str}",
                            callback_data=f"time_{time_str}"
                        )
                    ])
    except sqlite3.Error as e:
        logging.error(f"Database error: {e}")
        # Fallback к стандартным слотам
        for hour in WORK_HOURS:
            time_str = f"{hour}:00"
            buttons.append([
                InlineKeyboardButton(text=time_str, callback_data=f"time_{time_str}")
            ])
    
    buttons.append([InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_days")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def doctor_keyboard():
    """Клавиатура выбора врача"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="👩‍⚕️ Педиатр", callback_data="doctor_pediatrician"),
                InlineKeyboardButton(text="👨‍⚕️ Хирург", callback_data="doctor_surgeon")
            ],
            [
                InlineKeyboardButton(text="👩‍⚕️ Гинеколог", callback_data="doctor_gynecologist")
            ]
        ]
    )

def confirm_keyboard():
    """Клавиатура подтверждения записи"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Подтвердить", callback_data="confirm"),
                InlineKeyboardButton(text="❌ Отмена", callback_data="cancel")
            ]
        ]
    )
