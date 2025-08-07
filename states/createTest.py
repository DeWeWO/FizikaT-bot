from aiogram.fsm.state import StatesGroup, State

class TestCreation(StatesGroup):
    questionText = State()
    questionImage = State()
    v1 = State()
    v2 = State()
    v3 = State()
    v4 = State()
    confirm = State()

