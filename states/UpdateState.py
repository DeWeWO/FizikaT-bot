from aiogram.fsm.state import StatesGroup, State

class UpdateFIOState(StatesGroup):
    new_fio = State()
    confirm = State()
