from aiogram import Router, types
from aiogram.filters import CommandStart
from aiogram import Dispatcher  # Добавлен импорт Dispatcher
import logging  # Добавлен импорт logging
from keyboard.kbmain import main_kb

def setup_handlers(dp: Dispatcher):
    """Настройка стартовых обработчиков"""
    router = Router()
   #команда /start 
    @router.message(CommandStart())
    async def cmd_start(message: types.Message):
        try:
            await message.answer(
                "🏥 Добро пожаловать в систему записи на прием!\n"
                "Выберите действие ниже:",
                reply_markup=main_kb
            )
            logging.info(f"User {message.from_user.id} started the bot")  # Логирование
        except Exception as e:
            logging.error(f"Error in cmd_start: {e}")
            await message.answer("⚠️ Произошла ошибка при запуске бота")
    
    dp.include_router(router)