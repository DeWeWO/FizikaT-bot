import logging
from aiogram import types, F, Router
from aiogram.types import Message, ReplyKeyboardRemove
from aiogram.fsm.context import FSMContext
from db import add_new_registered_user
from buttons import main_markup, get_confirm_button
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
    await message.answer("<b>✅ Yo'nalishingizni kiriting:</b>\n\n<i>Na'muna: Axborot xavfsizligi</i>")
    await state.set_state(state=RegisterState.discipline)

@router.message(RegisterState.discipline, F.text)
async def get_discipline(message: types.Message, state: FSMContext):
    discipline = message.text
    if discipline:
        await state.update_data({"discipline": discipline})
        await message.answer("<b>👥 guruhingizni kiriting:</b>\n\n<i>Na'muna: 401</i>")
        await state.set_state(state=RegisterState.user_group)
    else:
        await message.answer("Yo'nalishingizni to'g'ri kiriting")

@router.message(RegisterState.user_group, F.text)
async def get_group(message: types.Message, state: FSMContext):
    user_group = message.text
    await state.update_data({"user_group": user_group})
    data = await state.get_data()
    text = f"👤FISH: {data.get('fio')}\n⤴️Yo'nalish: {data.get('discipline')}\n👥Guruh: {data.get('user_group')}"
    await message.answer(f"{text}\n\n<b>Ma'lumotlaringiz to'g'riligini tasdiqlang</b>", reply_markup=get_confirm_button())
    await state.set_state(state=RegisterState.confirm)

@router.callback_query(F.data == 'confirm', RegisterState.confirm)
async def save_register_user(call: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    
    try:
        fio = data.get('fio')
        discipline = data.get('discipline')
        user_group = data.get('user_group')
        add_new_registered_user(fio, discipline, user_group)
    except Exception as error:
        logging.error(error)
        await call.message.answer(f"Ma'lumotlarni bazaga yozishda xatolik yuz berdi.\nQaytadan urinib ko'ring", reply_markup=main_markup())
      
    await call.message.delete()
    await call.message.answer("Ma'lumotlar saqlandi!", reply_markup=main_markup())
    await state.clear()

@router.callback_query(F.data == 'cancel', RegisterState.confirm)
async def cancel_register(call: types.CallbackQuery, state: FSMContext):
    await call.message.delete()
    await call.message.answer("Asosiy menyu", reply_markup=main_markup())
    await state.clear()