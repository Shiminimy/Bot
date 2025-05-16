import os

BOT_TOKEN = "7107311050:AAFeWNHNLD5m3i3APHUswEfbfYYvsxniC-8"

ADMIN_ID = 869613280
DOCTOR_ID = 123456789
DOCTORS = {
    "pediatrician": 869613280,  # ID педиатра в Telegram
    "surgeon": 869613280,       # ID хирурга
    "gynecologist": 869613280   # ID гинеколога
}
DOCTOR_TITLES = {
    "pediatrician": "👩‍⚕️ Педиатр",
    "surgeon": "👨‍⚕️ Хирург",
    "gynecologist": "👩‍⚕️ Гинеколог"
}

WORK_HOURS = [10, 11, 12, 13]
WORK_MINUTES = ['00', '30']     # Добавляем поддержку 30-минутных интервалов

DB_PATH = "clinic.db"

# Настройки логирования
LOG_FILE = os.getenv("LOG_FILE", "bot.log")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")