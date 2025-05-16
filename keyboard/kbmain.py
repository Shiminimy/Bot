from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

main_kb = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="📝 Записаться на прием", callback_data="sign_up")],
        [InlineKeyboardButton(text="💬 Консультация", callback_data="consultation")],
        [InlineKeyboardButton(text="🛟 Поддержка", callback_data="support")],
    ]
)