import logging
from aiogram import types, F, Router
from aiogram.types import ReplyKeyboardRemove
from aiogram.fsm.context import FSMContext
from loader import db
from keyboards.reply.buttons import register_markup, get_confirm_button, get_test
from states import RegisterState

router = Router()

# Ro'yxatdan o'tishni boshlash
@router.message(F.text == "👤Ro'yxatdan o'tish")
async def start_register(message: types.Message, state: FSMContext):
    await message.answer(
        "<b>👤 Ism va familiyangizni to'liq kiriting:</b>\n\n<i>Na'muna: Abdullayev Abdulla</i>",
        reply_markup=ReplyKeyboardRemove()
    )
    await state.set_state(RegisterState.fio)

# FIO qabul qilish
@router.message(RegisterState.fio, F.text)
async def get_fio(message: types.Message, state: FSMContext):
    fio = message.text.strip()
    await state.update_data({"fio": fio, "telegram_id": message.from_user.id})
    text = f"👤 FIO: {fio}"
    await message.answer(
        f"{text}\n\n<b>Ma'lumotingizni tasdiqlang ✅</b>",
        reply_markup=get_confirm_button()
    )
    await state.set_state(RegisterState.confirm)

# Tasdiqlash tugmasi bosilganda ma'lumotni bazaga yozish
@router.callback_query(F.data == 'confirm', RegisterState.confirm)
async def save_register_user(call: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    fio = data.get('fio')
    telegram_id = data.get('telegram_id')

    try:
        await db.registered_user(fio, telegram_id)
        await call.message.delete()
        await call.message.answer("✅ Ma'lumotingiz saqlandi!", reply_markup=get_test())
    except Exception as error:
        logging.error(error)
        await call.message.answer(
            "❌ Ma'lumotingizni bazaga yozishda xatolik yuz berdi.\nQaytadan urinib ko‘ring.",
            reply_markup=register_markup()
        )
    finally:
        await state.clear()

# Bekor qilish tugmasi bosilganda
@router.callback_query(F.data == 'cancel', RegisterState.confirm)
async def cancel_register(call: types.CallbackQuery, state: FSMContext):
    await call.message.delete()
    await call.message.answer("Asosiy menyu", reply_markup=register_markup())
    await state.clear()
