import sqlite3
from datetime import datetime, timedelta
import asyncio
import logging
from aiogram import Bot
from config.settings import ADMIN_ID

class WeekManager:
    def __init__(self):
        self.bot = None
        self.db_path = "clinic.db"
        self.day_map = {
            "Понедельник": 0,
            "Вторник": 1, 
            "Среда": 2,
            "Четверг": 3,
            "Пятница": 4
        }
        self.last_reset_date = None  # Дата последнего сброса

    def init(self, bot: Bot):
        """Инициализация с экземпляром бота"""
        self.bot = bot
    
    async def schedule_reset(self):
        """Запускает еженедельный сброс в субботу в 00:00"""
        while True:
            try:
                now = datetime.now()
                current_date = now.date()

                # Проверяем, что сегодня суббота (5) и сброс еще не выполнялся
                if now.weekday() == 5 and self.last_reset_date != current_date:
                    # Вычисляем время до 00:00
                    time_until_midnight = (now.replace(hour=0, minute=0, second=0, microsecond=0) 
                                         + timedelta(days=1) - now).total_seconds()

                    # Ждем до 00:00
                    if time_until_midnight > 0:
                        await asyncio.sleep(time_until_midnight)

                    # Выполняем сброс
                    await self.reset_database()
                    self.last_reset_date = current_date

                    # Ждем 24 часа перед следующей проверкой
                    await asyncio.sleep(86400)
                else:
                    # Ждем 1 час до следующей проверки
                    await asyncio.sleep(3600)
                    
            except Exception as e:
                logging.error(f"Error in schedule_reset: {e}")
                await asyncio.sleep(3600)  # Ждем час перед повторной попыткой
    
    async def reset_database(self):
        """Очищает таблицу записей и уведомляет админа"""
        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Проверяем количество записей перед удалением
            cursor.execute("SELECT COUNT(*) FROM appointments")
            count = cursor.fetchone()[0]

            if count > 0:
                cursor.execute("DELETE FROM appointments")
                conn.commit()
                logging.info(f"Cleared {count} appointments from database")

                if self.bot and ADMIN_ID:
                    try:
                        await self.bot.send_message(
                            chat_id=ADMIN_ID,
                            text=f"🔄 База очищена. Удалено {count} записей"
                        )
                    except Exception as e:
                        logging.error(f"Notification error: {e}")
            else:
                logging.info("No appointments to clear - database was empty")

        except Exception as e:
            logging.error(f"Error resetting database: {e}")
            if self.bot and ADMIN_ID:
                await self.bot.send_message(
                    chat_id=ADMIN_ID,
                    text=f"❌ Ошибка при очистке базы: {str(e)}"
                )
        finally:
            if conn:
                conn.close()

    def is_day_available(self, day_name: str) -> bool:
        """Проверяет доступность дня для записи"""
        try:
            today = datetime.now().weekday()

            # Если сейчас суббота (5) или воскресенье (6) - все дни доступны
            if today >= 5:
                return True

            # Проверяем, что день существует в нашем словаре
            if day_name not in self.day_map:
                return False

            return self.day_map[day_name] >= today

        except Exception as e:
            logging.error(f"Error in is_day_available: {e}")
            return False

    def get_current_weekday(self) -> str:
        """Возвращает текущий день недели на русском"""
        days = ["Понедельник", "Вторник", "Среда", "Четверг", "Пятница", "Суббота", "Воскресенье"]
        return days[datetime.now().weekday()]

# Глобальный экземпляр менеджера
week_manager = WeekManager()
