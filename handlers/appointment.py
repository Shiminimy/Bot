# Импорт необходимых модулей из Aiogram и других библиотек
from aiogram import types, F, Router
from aiogram.fsm.context import FSMContext  # Контекст FSM-состояний
from aiogram.fsm.state import State, StatesGroup  # Описание состояний
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup  # Инлайн кнопки
from config.settings import WORK_HOURS, WORK_MINUTES  # Временные слоты
from keyboard.appointment import (  # Клавиатуры для записи
    days_keyboard,
    times_keyboard,
    doctor_keyboard,
    confirm_keyboard
)
from models.user import save_user  # Функция для сохранения пользователя
from models.appointment import save_appointment  # Функция для сохранения записи
import logging
import sqlite3
from contextlib import closing  # Для безопасной работы с БД

# Функция создания роутера записи на приём
def create_appointment_router(week_manager=None):
    router = Router()

    # Класс состояний FSM
    class AppointmentStates(StatesGroup):
        waiting_for_name = State()
        waiting_for_day = State()
        waiting_for_time = State()
        waiting_for_doctor = State()

    # Обработка команды "Записаться на приём" через текст
    @router.message(F.text == "Записаться на прием")
    async def start_appointment_text(message: types.Message, state: FSMContext):
        try:
            await state.set_state(AppointmentStates.waiting_for_name)
            await message.answer("✏️ Введите ваше имя и фамилию через пробел:")
        except Exception as e:
            logging.error(f"Error in start_appointment_text: {e}")
            await message.answer("⚠️ Не удалось начать запись. Попробуйте позже.")

    # Обработка нажатия на кнопку "Записаться на приём"
    @router.callback_query(F.data == "sign_up")
    async def start_appointment_callback(callback: types.CallbackQuery, state: FSMContext):
        try:
            await state.set_state(AppointmentStates.waiting_for_name)
            await callback.message.answer("✏️ Введите ваше имя и фамилию через пробел:")
            await callback.answer()
        except Exception as e:
            logging.error(f"Error in start_appointment_callback: {e}")
            await callback.answer("⚠️ Ошибка при запуске записи", show_alert=True)

    # Обработка ввода имени и фамилии пользователем
    @router.message(AppointmentStates.waiting_for_name)
    async def process_name(message: types.Message, state: FSMContext):
        try:
            first_name, last_name = message.text.strip().split(maxsplit=1)
            await state.update_data(
                first_name=first_name,
                last_name=last_name,
                user_id=message.from_user.id
            )

            try:
                # Сохраняем пользователя в БД
                save_user(message.from_user.id, first_name, last_name)
                await state.set_state(AppointmentStates.waiting_for_day)
                await message.answer("📅 Выберите день недели:", reply_markup=days_keyboard(week_manager))
            except sqlite3.IntegrityError:
                # Пользователь уже есть — продолжаем
                await state.set_state(AppointmentStates.waiting_for_day)
                await message.answer("📅 Выберите день недели:", reply_markup=days_keyboard(week_manager))
            except sqlite3.Error as e:
                logging.error(f"Database error: {e}")
                await message.answer("⚠️ Ошибка базы данных. Попробуйте позже.")
                await state.clear()

        except ValueError:
            await message.answer("ℹ️ Пожалуйста, введите имя и фамилию через один пробел.\nПример: Иван Иванов")
        except Exception as e:
            logging.error(f"Unexpected error: {e}")
            await message.answer("⚠️ Произошла ошибка. Начните запись заново.")
            await state.clear()

    # Обработка выбора дня недели
    @router.callback_query(F.data.startswith("day_"), AppointmentStates.waiting_for_day)
    async def process_day(callback: types.CallbackQuery, state: FSMContext):
        try:
            day = callback.data.split("_")[1]

            # Проверка: доступен ли день для записи
            if week_manager and hasattr(week_manager, 'is_day_available'):
                if not week_manager.is_day_available(day):
                    await callback.answer("❌ Этот день уже прошел! Новые записи доступны с понедельника.", show_alert=True)
                    return

            await state.update_data(day=day)
            await state.set_state(AppointmentStates.waiting_for_doctor)
            await callback.message.edit_text(f"📅 Выбран день: {day}\n\n👨‍⚕️ Выберите врача:", reply_markup=doctor_keyboard())
        except Exception as e:
            logging.error(f"Error in process_day: {e}")
            await callback.answer("⚠️ Ошибка при выборе дня", show_alert=True)
        finally:
            await callback.answer()

    # Обработка выбора врача
    @router.callback_query(F.data.startswith("doctor_"), AppointmentStates.waiting_for_doctor)
    async def process_doctor(callback: types.CallbackQuery, state: FSMContext):
        try:
            doctor = callback.data.split("_")[1]
            await state.update_data(doctor=doctor)
            data = await state.get_data()

            # Получаем занятые слоты из БД
            with closing(sqlite3.connect('clinic.db')) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT time FROM appointments WHERE doctor=? AND day=?", (doctor, data['day']))
                busy_times = {row[0] for row in cursor.fetchall()}

            # Формируем список доступных и занятых слотов
            buttons = []
            for hour in WORK_HOURS:
                for minute in WORK_MINUTES:
                    time_str = f"{hour}:{minute}"
                    status = "⛔ занято" if time_str in busy_times else "🕒"
                    buttons.append([
                        InlineKeyboardButton(
                            text=f"{status} {time_str}",
                            callback_data=f"time_{time_str}_{doctor}"
                        )
                    ])

            # Добавляем кнопки "Назад"
            buttons.append([
                InlineKeyboardButton(text="◀️ Назад к врачам", callback_data="back_to_doctors")
            ])
            buttons.append([
                InlineKeyboardButton(text="◀️ Назад к дням", callback_data="back_to_days")
            ])

            await callback.message.edit_text(
                f"📅 День: {data.get('day', 'не указан')}\n👨‍⚕️ Врач: {doctor}",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons)
            )
            await state.set_state(AppointmentStates.waiting_for_time)
        except Exception as e:
            logging.error(f"Error in process_doctor: {e}")
            await callback.answer("⚠️ Ошибка при выборе врача", show_alert=True)
        finally:
            await callback.answer()

    # Обработка выбора времени
    @router.callback_query(F.data.startswith("time_"), AppointmentStates.waiting_for_time)
    async def process_time(callback: types.CallbackQuery, state: FSMContext):
        try:
            time, doctor = callback.data.split("_")[1:3]
            await state.update_data(time=time, doctor=doctor)
            data = await state.get_data()

            # Проверка занятости времени
            with closing(sqlite3.connect('clinic.db')) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT 1 FROM appointments WHERE day=? AND time=? AND doctor=?", (data['day'], time, doctor))
                if cursor.fetchone():
                    await callback.answer("⚠️ Этот слот уже занят для выбранного врача.", show_alert=True)
                    return

            # Подтверждение записи
            await callback.message.edit_text(
                "🔍 Подтвердите запись:\n\n"
                f"📅 День: {data.get('day', 'не указан')}\n"
                f"🕒 Время: {time}\n"
                f"👤 Пациент: {data.get('first_name', '')} {data.get('last_name', '')}\n"
                f"👨‍⚕️ Врач: {doctor}",
                reply_markup=confirm_keyboard()
            )
            await state.set_state(AppointmentStates.waiting_for_doctor)
        except Exception as e:
            logging.error(f"Error in process_time: {e}")
            await callback.answer("⚠️ Ошибка при выборе времени", show_alert=True)
        finally:
            await callback.answer()

    # Подтверждение записи пользователем
    @router.callback_query(F.data == "confirm", AppointmentStates.waiting_for_doctor)
    async def confirm_appointment(callback: types.CallbackQuery, state: FSMContext):
        try:
            data = await state.get_data()
            save_appointment(
                user_id=data['user_id'],
                day=data['day'],
                time=data['time'],
                doctor=data['doctor']
            )

            await callback.message.edit_text(
                "✅ Запись успешно создана!\n\n"
                f"📅 День: {data['day']}\n"
                f"🕒 Время: {data['time']}\n"
                f"👤 Пациент: {data['first_name']} {data['last_name']}\n"
                f"👨‍⚕️ Врач: {data['doctor']}\n\n"
                "Мы ждем вас в указанное время!"
            )
        except Exception as e:
            logging.error(f"Error in confirm_appointment: {e}")
            await callback.answer("⚠️ Ошибка при подтверждении записи", show_alert=True)
        finally:
            await state.clear()
            await callback.answer()

    # Отмена записи пользователем
    @router.callback_query(F.data == "cancel", AppointmentStates.waiting_for_doctor)
    async def cancel_appointment(callback: types.CallbackQuery, state: FSMContext):
        try:
            data = await state.get_data()
            await callback.message.edit_text(
                f"❌ Запись отменена\n\nБудем рады видеть вас в другой раз, {data.get('first_name', '')}!"
            )
        except Exception as e:
            logging.error(f"Error in cancel_appointment: {e}")
            await callback.answer("⚠️ Ошибка при отмене записи", show_alert=True)
        finally:
            await state.clear()
            await callback.answer()

    # Возврат на шаг выбора врача
    @router.callback_query(F.data == "back_to_doctors", AppointmentStates.waiting_for_time)
    async def back_to_doctors(callback: types.CallbackQuery, state: FSMContext):
        data = await state.get_data()
        await state.set_state(AppointmentStates.waiting_for_doctor)
        await callback.message.edit_text(
            f"📅 День: {data.get('day', 'не указан')}\n👨‍⚕️ Выберите врача:",
            reply_markup=doctor_keyboard()
        )
        await callback.answer()

    # Возврат к выбору дня
    @router.callback_query(F.data == "back_to_days", AppointmentStates.waiting_for_doctor)
    async def back_to_days(callback: types.CallbackQuery, state: FSMContext):
        await state.set_state(AppointmentStates.waiting_for_day)
        await callback.message.edit_text(
            "📅 Выберите день недели:",
            reply_markup=days_keyboard(week_manager)
        )
        await callback.answer()

    # Возврат к вводу имени
    @router.callback_query(F.data == "back_to_name", AppointmentStates.waiting_for_day)
    async def back_to_name(callback: types.CallbackQuery, state: FSMContext):
        await state.set_state(AppointmentStates.waiting_for_name)
        await callback.message.edit_text("✏️ Введите ваше имя и фамилию через пробел:")
        await callback.answer()

    return router
