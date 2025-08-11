import logging
from aiogram import types, F, Router
from aiogram.types import ReplyKeyboardRemove
from aiogram.fsm.context import FSMContext
from loader import db
from keyboards.reply.buttons import register_markup, get_confirm_button, get_test
from states import RegisterState
from aiogram.enums import ChatType


router = Router()

# Ro'yxatdan o'tishni boshlash
@router.message(F.text == "👤Ro'yxatdan o'tish", F.chat.type.in_([ChatType.PRIVATE]))
async def start_register(message: types.Message, state: FSMContext):
    try:
        await message.answer(
            "<b>👤 Ism va familiyangizni to'liq kiriting:</b>\n\n<i>Na'muna: Abdullayev Abdulla</i>",
            reply_markup=ReplyKeyboardRemove()
        )
        await state.set_state(RegisterState.fio)
        logging.info(f"User {message.from_user.id} ro'yxatdan o'tishni boshladi")
    except Exception as error:
        logging.error(f"Start register error: {error}")
        await message.answer(
            "Xatolik yuz berdi. Qaytadan urinib ko'ring.",
            reply_markup=register_markup()
        )

# FIO qabul qilish
@router.message(RegisterState.fio, F.text)
async def get_fio(message: types.Message, state: FSMContext):
    try:
        fio = message.text.strip()
        
        # FIO uzunligini tekshirish
        if len(fio) < 3:
            await message.answer(
                "❌ Ism va familiyani to'liq kiriting!\n\n<i>Na'muna: Abdullayev Abdulla</i>"
            )
            return
        
        if len(fio) > 100:
            await message.answer(
                "❌ Ism va familiya juda uzun!\n\nQisqaroq variant kiriting."
            )
            return
        
        await state.update_data({"fio": fio, "telegram_id": message.from_user.id})
        text = f"👤 FIO: {fio}"
        
        await message.answer(
            f"{text}\n\n<b>Ma'lumotingizni tasdiqlang ✅</b>",
            reply_markup=get_confirm_button()
        )
        await state.set_state(RegisterState.confirm)
        logging.info(f"User {message.from_user.id} FIO kiritdi: {fio}")
        
    except Exception as error:
        logging.error(f"Get FIO error: {error}")
        await message.answer(
            "Xatolik yuz berdi. Qaytadan urinib ko'ring.",
            reply_markup=register_markup()
        )
        await state.clear()

# Tasdiqlash tugmasi bosilganda ma'lumotni bazaga yozish
@router.callback_query(F.data == 'confirm', RegisterState.confirm)
async def save_register_user(call: types.CallbackQuery, state: FSMContext):
    try:
        data = await state.get_data()
        fio = data.get('fio')
        telegram_id = data.get('telegram_id')
        
        if not fio or not telegram_id:
            await call.message.answer(
                "❌ Ma'lumot topilmadi. Qaytadan ro'yxatdan o'tishni boshlang.",
                reply_markup=register_markup()
            )
            await state.clear()
            return

        # Ro'yxatdan o'tgan foydalanuvchini tekshirish
        try:
            check_result = await db.check_registration(telegram_id=telegram_id)
            is_registered = check_result and check_result.get('registered', False)
            
            if is_registered:
                try:
                    await call.message.edit_text(
                        "✅ Siz allaqachon ro'yxatdan o'tgan ekansiz.",
                        reply_markup=None
                    )
                    await call.message.answer("", reply_markup=get_test())
                except Exception as edit_error:
                    logging.warning(f"Message edit error: {edit_error}")
                    await call.message.answer(
                        "✅ Siz allaqachon ro'yxatdan o'tgan ekansiz.",
                        reply_markup=get_test()
                    )
                logging.info(f"User {telegram_id} allaqachon ro'yxatdan o'tgan")
            else:
                # Foydalanuvchini bazaga qo'shamiz
                result = await db.registered_user(fio, telegram_id)
                
                if result and (result.get('created') or result.get('register')):
                    try:
                        await call.message.edit_text(
                            "✅ Ma'lumotingiz saqlandi!",
                            reply_markup=None
                        )
                        await call.message.answer("", reply_markup=get_test())
                    except Exception as edit_error:
                        logging.warning(f"Success message edit error: {edit_error}")
                        await call.message.answer(
                            "✅ Ma'lumotingiz saqlandi!",
                            reply_markup=get_test()
                        )
                    logging.info(f"User {telegram_id} muvaffaqiyatli ro'yxatdan o'tdi")
                else:
                    await call.message.answer(
                        "❌ Ma'lumotingizni bazaga yozishda xatolik yuz berdi.\nQaytadan urinib ko'ring.",
                        reply_markup=register_markup()
                    )
                    logging.error(f"Database register failed for {telegram_id}")
                    
        except Exception as db_error:
            logging.error(f"Database operation error: {db_error}")
            await call.message.answer(
                "❌ Ma'lumotingizni bazaga yozishda xatolik yuz berdi.\nQaytadan urinib ko'ring.",
                reply_markup=register_markup()
            )
        
        # Xabarni o'chirish
        try:
            await call.message.delete()
        except Exception as delete_error:
            logging.warning(f"Message delete error: {delete_error}")
            
    except Exception as error:
        logging.error(f"Register save general error: {error}")
        try:
            await call.message.answer(
                "❌ Xatolik yuz berdi. Qaytadan urinib ko'ring.",
                reply_markup=register_markup()
            )
        except Exception as response_error:
            logging.error(f"Error response failed: {response_error}")
    finally:
        await state.clear()

# Bekor qilish tugmasi bosilganda
@router.callback_query(F.data == 'cancel', RegisterState.confirm)
async def cancel_register(call: types.CallbackQuery, state: FSMContext):
    try:
        try:
            await call.message.delete()
        except Exception as delete_error:
            logging.warning(f"Cancel message delete error: {delete_error}")
            
        await call.message.answer("Asosiy menyu", reply_markup=register_markup())
        logging.info(f"User {call.from_user.id} ro'yxatdan o'tishni bekor qildi")
        
    except Exception as error:
        logging.error(f"Cancel register error: {error}")
        try:
            await call.message.answer(
                "Asosiy menyu",
                reply_markup=register_markup()
            )
        except Exception as fallback_error:
            logging.error(f"Cancel fallback error: {fallback_error}")
    finally:
        await state.clear()

# Noto'g'ri formatdagi xabarlar uchun
@router.message(RegisterState.fio)
async def invalid_fio_format(message: types.Message, state: FSMContext):
    try:
        await message.answer(
            "❌ Faqat matn ko'rinishida ism va familiyangizni kiriting!\n\n<i>Na'muna: Abdullayev Abdulla</i>"
        )
    except Exception as error:
        logging.error(f"Invalid FIO format error: {error}")
        await state.clear()