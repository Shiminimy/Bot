from aiogram import F, Router, types
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from config.settings import DOCTORS
import logging

router = Router()

class ConsultationStates(StatesGroup):
    waiting_for_doctor = State()
    waiting_for_fullname = State()
    waiting_for_question = State()
    waiting_for_answer = State()

# Клавиатура выбора врача
def doctors_keyboard():
    return types.InlineKeyboardMarkup(
        inline_keyboard=[
            [types.InlineKeyboardButton(text="👩‍⚕️ Педиатр", callback_data="consult_pediatrician")],
            [types.InlineKeyboardButton(text="👨‍⚕️ Хирург", callback_data="consult_surgeon")],
            [types.InlineKeyboardButton(text="👩‍⚕️ Гинеколог", callback_data="consult_gynecologist")]
        ]
    )

# Обработка кнопки "💬 Консультация" из инлайн-клавиатуры
@router.callback_query(F.data == "consultation")
async def handle_consultation_button(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(ConsultationStates.waiting_for_doctor)
    await callback.message.edit_text("Выберите врача для консультации:", reply_markup=doctors_keyboard())
    await callback.answer()

# Также поддержка текстовой команды "Консультация"
@router.message(F.text == "Консультация")
async def start_consultation(message: types.Message, state: FSMContext):
    await state.set_state(ConsultationStates.waiting_for_doctor)
    await message.answer("Выберите врача:", reply_markup=doctors_keyboard())

# Выбор врача
@router.callback_query(F.data.startswith("consult_"), ConsultationStates.waiting_for_doctor)
async def select_doctor(callback: types.CallbackQuery, state: FSMContext):
    doctor_type = callback.data.split("_")[1]
    await state.update_data(doctor_type=doctor_type, doctor_id=DOCTORS[doctor_type])
    await state.set_state(ConsultationStates.waiting_for_fullname)
    await callback.message.edit_text("👤 Пожалуйста, введите ваше имя и фамилию:")
    await callback.answer()

# Получение ФИО
@router.message(ConsultationStates.waiting_for_fullname)
async def receive_fullname(message: types.Message, state: FSMContext):
    full_name_input = message.text.strip()
    if not full_name_input or len(full_name_input.split()) < 2:
        await message.answer("⚠️ Пожалуйста, введите **имя и фамилию**, например: `Иван Иванов`.")
        return

    username = f"(@{message.from_user.username})" if message.from_user.username else ""
    full_name = f"{full_name_input} {username}"

    await state.update_data(patient_name=full_name, patient_id=message.from_user.id)
    await state.set_state(ConsultationStates.waiting_for_question)
    await message.answer("✍️ Теперь введите ваш вопрос врачу:")

# Получение вопроса от пациента
@router.message(ConsultationStates.waiting_for_question)
async def process_question(message: types.Message, state: FSMContext):
    data = await state.get_data()

    await state.update_data(question=message.text)

    try:
        await message.bot.send_message(
            chat_id=data['doctor_id'],
            text=f"❓ Новый вопрос от {data['patient_name']}:\n\n{message.text}",
            reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[
                [types.InlineKeyboardButton(
                    text="Ответить",
                    callback_data=f"answer_{message.from_user.id}_{data['doctor_type']}"
                )]
            ])
        )
        await message.answer("✅ Ваш вопрос отправлен врачу. Ожидайте ответа.")
        await state.clear()
    except Exception as e:
        logging.error(f"Error sending to doctor: {e}")
        await message.answer("⚠️ Не удалось отправить вопрос. Попробуйте позже.")
        await state.clear()

# Ответ врача
@router.callback_query(F.data.startswith("answer_"))
async def answer_consultation(callback: types.CallbackQuery, state: FSMContext):
    parts = callback.data.split("_")
    patient_id = int(parts[1])
    doctor_type = parts[2] if len(parts) > 2 else "врач"
    await state.update_data(patient_id=patient_id, doctor_type=doctor_type)
    await state.set_state(ConsultationStates.waiting_for_answer)
    await callback.message.answer("Напишите ответ пациенту:")
    await callback.answer()

# Отправка ответа пациенту
@router.message(ConsultationStates.waiting_for_answer)
async def send_answer(message: types.Message, state: FSMContext):
    data = await state.get_data()

    doctor_labels = {
        "pediatrician": "👩‍⚕️ Педиатр",
        "surgeon": "👨‍⚕️ Хирург",
        "gynecologist": "👩‍⚕️ Гинеколог"
    }
    doctor_label = doctor_labels.get(data.get("doctor_type"), "👩‍⚕️ Врач")

    try:
        await message.bot.send_message(
            chat_id=data['patient_id'],
            text=f"{doctor_label} ответил(а):\n\n{message.text}"
        )
        await message.answer("✅ Ответ отправлен пациенту.")
    except Exception as e:
        logging.error(f"Error sending answer: {e}")
        await message.answer("⚠️ Не удалось отправить ответ.")
    finally:
        await state.clear()
