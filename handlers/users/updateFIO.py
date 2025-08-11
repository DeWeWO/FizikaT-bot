import logging
from aiogram import Router, types, F
from aiogram.types import ReplyKeyboardRemove
from aiogram.fsm.context import FSMContext
from loader import db
from keyboards.reply.buttons import get_confirm_button, register_markup, get_test
from states.UpdateState import UpdateFIOState
from aiogram.enums import ChatType

router = Router()

# Tahrirlashni boshlash
@router.message(F.text == "✏️ Ismni tahrirlash", F.chat.type.in_([ChatType.PRIVATE]))
async def start_update_fio(message: types.Message, state: FSMContext):
    telegram_id = message.from_user.id

    try:
        # Ro'yxatdan o'tganligini tekshirish
        check_result = await db.check_registration(telegram_id=telegram_id)
        is_registered = check_result and check_result.get('registered', False)
        
        if not is_registered:
            await message.answer(
                "❌ Siz hali ro'yxatdan o'tmagansiz. Avval ro'yxatdan o'ting.",
                reply_markup=register_markup()
            )
            logging.info(f"User {telegram_id} ro'yxatdan o'tmagan, FIO tahrirlash rad etildi")
            return

        current_fio = check_result.get('fio', 'Noma\'lum')
        
        await message.answer(
            f"📌 Mavjud FIO: <b>{current_fio}</b>\n\n"
            f"✏️ Yangi FIO kiriting:",
            reply_markup=ReplyKeyboardRemove()
        )
        await state.set_state(UpdateFIOState.new_fio)
        logging.info(f"User {telegram_id} FIO tahrirlashni boshladi. Mavjud FIO: {current_fio}")
        
    except Exception as error:
        logging.error(f"Start update FIO error: {error}")
        await message.answer(
            "❌ Ma'lumotni tekshirishda xatolik yuz berdi. Qaytadan urinib ko'ring.",
            reply_markup=register_markup()
        )

# Yangi FIO qabul qilish
@router.message(UpdateFIOState.new_fio, F.text)
async def get_new_fio(message: types.Message, state: FSMContext):
    try:
        new_fio = message.text.strip()
        
        # FIO validatsiyasi
        if len(new_fio) < 3:
            await message.answer(
                "❌ Ism va familiyani to'liq kiriting!\n\n<i>Na'muna: Abdullayev Abdulla</i>"
            )
            return
        
        if len(new_fio) > 100:
            await message.answer(
                "❌ Ism va familiya juda uzun!\n\nQisqaroq variant kiriting."
            )
            return
        
        await state.update_data({"new_fio": new_fio, "telegram_id": message.from_user.id})

        await message.answer(
            f"🔄 Yangi FIO: <b>{new_fio}</b>\n\n<b>Tasdiqlaysizmi?</b>",
            reply_markup=get_confirm_button()
        )
        await state.set_state(UpdateFIOState.confirm)
        logging.info(f"User {message.from_user.id} yangi FIO kiritdi: {new_fio}")
        
    except Exception as error:
        logging.error(f"Get new FIO error: {error}")
        await message.answer(
            "❌ Xatolik yuz berdi. Qaytadan urinib ko'ring.",
            reply_markup=register_markup()
        )
        await state.clear()

# Tasdiqlash
@router.callback_query(F.data == "confirm", UpdateFIOState.confirm)
async def confirm_update(call: types.CallbackQuery, state: FSMContext):
    try:
        data = await state.get_data()
        new_fio = data.get("new_fio")
        telegram_id = data.get("telegram_id")
        
        if not new_fio or not telegram_id:
            await call.message.answer(
                "❌ Ma'lumot topilmadi. Qaytadan tahrirlashni boshlang.",
                reply_markup=register_markup()
            )
            await state.clear()
            return

        # FIO ni yangilash
        try:
            result = await db.update_fio(new_fio, telegram_id)
            
            if result:
                try:
                    await call.message.edit_text(
                        "✅ FIO'ingiz yangilandi!",
                        reply_markup=None
                    )
                    await call.message.answer("", reply_markup=get_test())
                except Exception as edit_error:
                    logging.warning(f"Message edit error: {edit_error}")
                    await call.message.answer(
                        "✅ FIO'ingiz yangilandi!",
                        reply_markup=get_test()
                    )
                logging.info(f"User {telegram_id} FIO ni yangiladi: {new_fio}")
            else:
                await call.message.answer(
                    "❌ Ma'lumotni yangilashda xatolik yuz berdi. Qaytadan urinib ko'ring.",
                    reply_markup=register_markup()
                )
                logging.warning(f"FIO update failed for user {telegram_id}")
                
        except Exception as update_error:
            logging.error(f"Database update error: {update_error}")
            await call.message.answer(
                "❌ Ma'lumotni yangilashda xatolik yuz berdi. Qaytadan urinib ko'ring.",
                reply_markup=register_markup()
            )
        
        # Xabarni o'chirish
        try:
            await call.message.delete()
        except Exception as delete_error:
            logging.warning(f"Message delete error: {delete_error}")
            
    except Exception as error:
        logging.error(f"Confirm update general error: {error}")
        try:
            await call.message.answer(
                "❌ Xatolik yuz berdi. Qaytadan urinib ko'ring.",
                reply_markup=register_markup()
            )
        except Exception as response_error:
            logging.error(f"Error response failed: {response_error}")
    finally:
        await state.clear()

# Bekor qilish
@router.callback_query(F.data == "cancel", UpdateFIOState.confirm)
async def cancel_update(call: types.CallbackQuery, state: FSMContext):
    try:
        try:
            await call.message.delete()
        except Exception as delete_error:
            logging.warning(f"Cancel message delete error: {delete_error}")
            
        await call.message.answer("Asosiy menyu", reply_markup=register_markup())
        logging.info(f"User {call.from_user.id} FIO tahrirlashni bekor qildi")
        
    except Exception as error:
        logging.error(f"Cancel update error: {error}")
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
@router.message(UpdateFIOState.new_fio)
async def invalid_new_fio_format(message: types.Message, state: FSMContext):
    try:
        await message.answer(
            "❌ Faqat matn ko'rinishida ism va familiyangizni kiriting!\n\n<i>Na'muna: Abdullayev Abdulla</i>"
        )
    except Exception as error:
        logging.error(f"Invalid new FIO format error: {error}")
        await state.clear()