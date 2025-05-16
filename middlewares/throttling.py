import time
from aiogram import BaseMiddleware
from aiogram.types import Message
from typing import Callable, Dict, Any, Awaitable

# Словарь для хранения времени последнего сообщения от каждого пользователя
user_message_times: Dict[int, float] = {}

class ThrottlingMiddleware(BaseMiddleware):
    def __init__(self, limit_seconds: int = 3):
        self.limit_seconds = limit_seconds
        super().__init__()

    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: Dict[str, Any]
    ) -> Any:
        user_id = event.from_user.id
        now = time.time()

        last_time = user_message_times.get(user_id, 0)
        if now - last_time < self.limit_seconds:
            await event.answer("🚫 Пожалуйста, не отправляйте сообщения слишком часто.")
            return  # не передаем управление дальше (сообщение блокируется)

        user_message_times[user_id] = now
        return await handler(event, data)