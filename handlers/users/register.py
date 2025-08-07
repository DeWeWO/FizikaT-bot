import logging
from aiogram import types, F, Router
from aiogram.types import Message, ReplyKeyboardRemove
from aiogram.fsm.context import FSMContext
from loader import db
from keyboards.reply.buttons import register_markup, get_confirm_button, get_test
from states import RegisterState

router = Router()

@router.message(F.text == "👤Ro'yxatdan o'tish")
async def start_register(message: types.Message, state: FSMContext):
    await message.answer("<b>👤 Ism va familiyangizni to'liq kiriting:</b>\n\n<i>Na'muna: Abudllayev Abdulla</i>", reply_markup=ReplyKeyboardRemove())
    await state.set_state(state=RegisterState.fio)

@router.message(RegisterState.fio, F.text)
async def get_fio(message: types.Message, state: FSMContext):
    fio = message.text
    await state.update_data({"fio": fio})
    data = await state.get_data()
    text = f"👤FISH: {data.get('fio')}"
    await message.answer(f"{text}\n\n<b>Ma'lumotingizni tasdiqlang ✅</b>", reply_markup=get_confirm_button())
    await state.set_state(state=RegisterState.confirm)

@router.callback_query(F.data == 'confirm', RegisterState.confirm)
async def save_register_user(call: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    
    try:
        fio = data.get('fio')
        await db.registered_user(fio)
        await call.message.delete()
        await call.message.answer("Ma'lumotingiz saqlandi!", reply_markup=get_test())
    except Exception as error:
        logging.error(error)
        await call.message.answer(f"Ma'lumotingizni bazaga yozishda xatolik yuz berdi.\nQaytadan urinib ko'ring", reply_markup=register_markup())
    finally:
        await state.clear()

@router.callback_query(F.data == 'cancel', RegisterState.confirm)
async def cancel_register(call: types.CallbackQuery, state: FSMContext):
    await call.message.delete()
    await call.message.answer("Asosiy menyu", reply_markup=register_markup())
    await state.clear()