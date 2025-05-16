from aiogram import F, Router, types
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from config.settings import ADMIN_ID
import logging

router = Router()

class SupportStates(StatesGroup):
    waiting_for_fullname = State()  # Шаг для ввода ФИО
    waiting_for_support_message = State()  # Шаг для ввода сообщения
    waiting_for_admin_reply = State()  # Шаг для ответа администратора

# Обработка кнопки "🛟 Поддержка" из инлайн-клавиатуры
@router.callback_query(F.data == "support")
async def handle_support_button(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(SupportStates.waiting_for_fullname)
    await callback.message.edit_text("👤 Пожалуйста, введите ваше имя и фамилию:")
    await callback.answer()

# Также обработка текстовой команды "поддержка"
@router.message(F.text.lower() == "поддержка")
async def support_text_command(message: types.Message, state: FSMContext):
    await state.set_state(SupportStates.waiting_for_fullname)
    await message.answer("👤 Пожалуйста, введите ваше имя и фамилию:")

# Пользователь вводит имя и фамилию
@router.message(SupportStates.waiting_for_fullname)
async def receive_fullname(message: types.Message, state: FSMContext):
    full_name_input = message.text.strip()
    if not full_name_input or len(full_name_input.split()) < 2:
        await message.answer("⚠️ Пожалуйста, введите **имя и фамилию**, например: `Иван Иванов`.")
        return

    username = f"(@{message.from_user.username})" if message.from_user.username else ""
    full_name = f"{full_name_input} {username}"

    await state.update_data(
        user_id=message.from_user.id,
        user_name=full_name
    )

    await state.set_state(SupportStates.waiting_for_support_message)
    await message.answer("✍️ Теперь, пожалуйста, введите ваше сообщение для поддержки:")

# Пользователь отправляет сообщение в поддержку
@router.message(SupportStates.waiting_for_support_message)
async def receive_support_message(message: types.Message, state: FSMContext):
    data = await state.get_data()
    full_name = data.get('user_name')

    try:
        await message.bot.send_message(
            chat_id=ADMIN_ID,
            text=f"📩 Сообщение в поддержку от {full_name}:\n\n{message.text}",
            reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[
                [types.InlineKeyboardButton(
                    text="Ответить",
                    callback_data=f"reply_{message.from_user.id}"
                )]
            ])
        )
        await message.answer("✅ Ваше сообщение отправлено в поддержку. Ожидайте ответа.")
        await state.clear()
    except Exception as e:
        logging.error(f"Error sending support message to admin: {e}")
        await message.answer("⚠️ Произошла ошибка при отправке. Попробуйте позже.")
        await state.clear()

# Админ нажимает "Ответить"
@router.callback_query(F.data.startswith("reply_"))
async def admin_reply_button(callback: types.CallbackQuery, state: FSMContext):
    user_id = int(callback.data.split("_")[1])
    await state.update_data(reply_user_id=user_id)
    await state.set_state(SupportStates.waiting_for_admin_reply)
    await callback.message.answer("✍️ Введите сообщение для ответа пользователю:")
    await callback.answer()

# Админ отправляет ответ пользователю
@router.message(SupportStates.waiting_for_admin_reply)
async def send_admin_reply(message: types.Message, state: FSMContext):
    data = await state.get_data()
    user_id = data.get("reply_user_id")

    try:
        await message.bot.send_message(
            chat_id=user_id,
            text=f"💬 Ответ от поддержки:\n\n{message.text}"
        )
        await message.answer("✅ Ответ отправлен пользователю.")
    except Exception as e:
        logging.error(f"Error sending reply to user: {e}")
        await message.answer("⚠️ Не удалось отправить ответ.")
    finally:
        await state.clear()
