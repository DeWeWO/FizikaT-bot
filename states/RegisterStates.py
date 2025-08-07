from aiogram.fsm.state import StatesGroup, State

class RegisterState(StatesGroup):
    fio = State()
    confirm = State()