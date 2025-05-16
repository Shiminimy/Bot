import os
import logging
import sqlite3
import subprocess
import sys
from aiogram import Router, types
from aiogram.filters import Command
from config.settings import ADMIN_ID, DB_PATH

# Создаём экземпляр роутера для регистрации команд
router = Router()

# Проверка, является ли пользователь админом
async def is_admin(user_id: int) -> bool:
    return user_id == ADMIN_ID

# Получение всех занятых записей на приём из базы данных
def get_occupied_appointments():
    """Возвращает список занятых записей из БД"""
    try:
        with sqlite3.connect(DB_PATH) as conn:
            conn.row_factory = sqlite3.Row  # Доступ к столбцам по названию
            cursor = conn.cursor()
            # Получаем записи с данными пациента, врача и времени
            cursor.execute("""
                SELECT 
                    a.id,
                    u.first_name || ' ' || u.last_name as patient_name,
                    a.doctor as doctor_name,
                    a.day || ' ' || a.time as appointment_time
                FROM appointments a
                JOIN users u ON a.user_id = u.user_id
                ORDER BY a.day, a.time
            """)
            return cursor.fetchall()
    except sqlite3.Error as e:
        logging.error(f"Database error in get_occupied_appointments: {e}")
        raise

# Команда: /занятые_записи — показать администратору список всех занятых слотов
@router.message(Command("занятые_записи"))
async def show_occupied_appointments(message: types.Message):
    if not await is_admin(message.from_user.id):
        await message.answer("❌ У вас нет прав для использования этой команды.")
        return

    try:
        appointments = get_occupied_appointments()
        if not appointments:
            await message.answer("📅 Нет занятых записей.")
            return
        
        # Формируем текстовый ответ
        response = "📋 Занятые записи:\n\n"
        for app in appointments:
            response += (
                f"🆔 ID: {app['id']}\n"
                f"👤 Пациент: {app['patient_name']}\n"
                f"👨‍⚕️ Врач: {app['doctor_name']}\n"
                f"🕒 Время: {app['appointment_time']}\n"
                f"────────────────────\n"
            )
        
        # Разбиваем длинное сообщение на части, если больше 4000 символов
        if len(response) > 4000:
            parts = [response[i:i+4000] for i in range(0, len(response), 4000)]
            for part in parts:
                await message.answer(part)
        else:
            await message.answer(response)
            
    except Exception as e:
        logging.error(f"Error in /занятые_записи: {e}", exc_info=True)
        await message.answer("⚠️ Произошла ошибка при получении занятых записей.\nПодробности в логах.")

# Команда: /перезапуск — перезапуск бота администратором
@router.message(Command("перезапуск"))
async def restart_bot(message: types.Message):
    if not await is_admin(message.from_user.id):
        await message.answer("❌ У вас нет прав для использования этой команды.")
        return

    try:
        await message.answer("🔄 Бот перезагружается...")

        # Получаем путь к Python-интерпретатору и аргументы запуска
        python = sys.executable
        args = sys.argv

        # Перезапускаем текущий процесс (замена текущего процесса новым)
        os.execl(python, python, *args)
        
    except Exception as e:
        logging.error(f"Restart error: {e}", exc_info=True)
        await message.answer(f"⚠️ Ошибка перезагрузки: {e}")

# Команда: /остановка — остановка бота (завершение процесса)
@router.message(Command("остановка"))
async def stop_bot(message: types.Message):
    if not await is_admin(message.from_user.id):
        await message.answer("❌ У вас нет прав для использования этой команды.")
        return

    try:
        await message.answer("🛑 Бот останавливается...")

        # Показываем, что бот "печатает"
        from aiogram.enums import ChatAction
        await message.bot.send_chat_action(message.chat.id, ChatAction.TYPING)

        # Завершаем процесс (код 0 — нормальное завершение)
        os._exit(0)
        
    except Exception as e:
        logging.error(f"Stop error: {e}", exc_info=True)
        await message.answer(f"⚠️ Ошибка остановки: {e}")

# Команда: /логи — отправить файл логов администратору
@router.message(Command("логи"))
async def get_logs(message: types.Message):
    if not await is_admin(message.from_user.id):
        await message.answer("❌ У вас нет прав для использования этой команды.")
        return

    try:
        log_file = "bot.log"
        # Проверяем, существует ли файл логов
        if not os.path.exists(log_file):
            await message.answer("📁 Файл логов не найден")
            return
        
        # Отправляем лог-файл как документ
        await message.answer_document(types.FSInputFile(log_file))
        
    except Exception as e:
        logging.error(f"Logs error: {e}", exc_info=True)
        await message.answer(f"⚠️ Ошибка получения логов: {e}")
