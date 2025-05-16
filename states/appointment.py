from aiogram.fsm.state import State, StatesGroup

class AppointmentStates(StatesGroup):
    choosing_day = State()
    choosing_time = State()
    choosing_doctor = State()  # Переносим выбор врача после времени
    confirming = State()
