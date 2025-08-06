from aiogram.fsm.state import StatesGroup, State

class RegisterState(StatesGroup):
    fio = State()
    discipline = State()
    user_group = State()
    confirm = State()