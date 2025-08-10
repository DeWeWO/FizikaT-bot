from aiogram.fsm.state import State, StatesGroup

class AdminRegistration(StatesGroup):
    waiting_for_first_name = State()
    waiting_for_last_name = State()
    waiting_for_password = State()
    waiting_for_password_confirmation = State()
    waiting_for_confirmation = State()

class AdminToken(StatesGroup):
    final_confirmation = State()