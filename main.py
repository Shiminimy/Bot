import logging
import asyncio
from aiogram import Bot, Dispatcher
from config.settings import BOT_TOKEN
from config.database import init_db
from handlers.start import setup_handlers as setup_start_handlers
from handlers.appointment import create_appointment_router
from utils.weekly_reset import week_manager
from handlers.consultation import router as consultation_router
from handlers.support import router as support_router  # Роутер поддержки (вопрос-ответ с админом)
from services.admin_commands import router as admin_router  # Админские команды
from config.settings import LOG_FILE, LOG_LEVEL
from middlewares.throttling import ThrottlingMiddleware  # Middleware для защиты от флуда

# Настройка логирования: файл + консоль
logging.basicConfig(
    level=LOG_LEVEL,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),  # Лог в файл
        logging.StreamHandler()         # Лог в консоль
    ]
)

async def main():
    # Инициализация бота и диспетчера
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()

    # Инициализация базы данных
    try:
        init_db()
        logging.info("Database initialized successfully")
    except Exception as e:
        logging.error(f"Failed to initialize database: {e}")
        raise

    # Настройка планировщика сброса расписания (еженедельно)
    try:
        week_manager.init(bot)
        asyncio.create_task(week_manager.schedule_reset())  # Запускаем фоновую задачу сброса расписания
        logging.info("Week manager initialized successfully")
    except Exception as e:
        logging.error(f"Failed to initialize week manager: {e}")
        raise

    # Регистрация всех роутеров
    dp.include_router(consultation_router)  # Роутер консультаций
    dp.include_router(support_router)       # Роутер поддержки
    dp.include_router(admin_router)         # Роутер команд администратора

    # Подключение антифлуд-мидлвари — защита от спама (таймаут 3 секунды)
    dp.message.middleware(ThrottlingMiddleware(limit_seconds=3))

    # Регистрация обработчиков и дополнительных роутеров
    try:
        setup_start_handlers(dp)  # Обработчики стартовых команд (/start и пр.)

        # Роутер записи на приём, с доступом к менеджеру недельного расписания
        appointment_router = create_appointment_router(week_manager)
        dp.include_router(appointment_router)

        logging.info("Handlers registered successfully")
    except Exception as e:
        logging.error(f"Failed to register handlers: {e}")
        raise

    # Запуск бота в режиме polling (опрос обновлений от Telegram)
    logging.info("Starting bot...")
    try:
        await dp.start_polling(bot)
    except Exception as e:
        logging.error(f"Bot stopped with error: {e}")
        raise
    finally:
        await bot.session.close()  # Корректное закрытие сессии

# Точка входа в программу
if __name__ == "__main__":
    try:
        asyncio.run(main())  # Запуск асинхронной функции main()
    except KeyboardInterrupt:
        logging.info("Bot stopped by keyboard interrupt")  # Прерывание вручную (Ctrl+C)
    except SystemExit:
        logging.info("Bot stopped by system exit")         # Завершение через систему
    except Exception as e:
        logging.error(f"Bot crashed with error: {e}")      # Непредвиденная ошибка
    finally:
        logging.info("Bot shutdown complete")              # Завершение работы
