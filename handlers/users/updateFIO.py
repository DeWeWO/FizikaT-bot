import logging
from aiogram import Router, types, F
from aiogram.types import ReplyKeyboardRemove
from aiogram.fsm.context import FSMContext
from loader import db
from keyboards.reply.buttons import get_confirm_button, register_markup, get_test
from states.UpdateState import UpdateFIOState

router = Router()

# Tahrirlashni boshlash
@router.message(F.text == "✏️ Ismni tahrirlash")
async def start_update_fio(message: types.Message, state: FSMContext):
    telegram_id = message.from_user.id
    reg_user = await db.execute(
        "SELECT fio FROM register WHERE telegram_id = $1",
        telegram_id,
        fetchrow=True
    )

    if not reg_user:
        await message.answer(
            "❌ Siz hali ro‘yxatdan o‘tmagansiz. Avval ro‘yxatdan o‘ting.",
            reply_markup=register_markup()
        )
        return

    await message.answer(
        f"📌 Mavjud FIO: <b>{reg_user['fio']}</b>\n\n"
        f"✏️ Yangi FIO kiriting:",
        reply_markup=ReplyKeyboardRemove()
    )
    await state.set_state(UpdateFIOState.new_fio)

# Yangi FIO qabul qilish
@router.message(UpdateFIOState.new_fio, F.text)
async def get_new_fio(message: types.Message, state: FSMContext):
    new_fio = str(message.text).strip()
    await state.update_data({"new_fio": new_fio, "telegram_id": message.from_user.id})

    await message.answer(
        f"🔄 Yangi FIO: <b>{new_fio}</b>\n\n<b>Tasdiqlaysizmi?</b>",
        reply_markup=get_confirm_button()
    )
    await state.set_state(UpdateFIOState.confirm)

# Tasdiqlash
@router.callback_query(F.data == "confirm", UpdateFIOState.confirm)
async def confirm_update(call: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    new_fio = data.get("new_fio")
    telegram_id = data.get("telegram_id")

    try:
        await db.update_fio(new_fio, telegram_id)
        await call.message.delete()
        await call.message.answer(
            "✅ FIO'ingiz yangilandi!",
            reply_markup=get_test()
        )
    except Exception as error:
        logging.error(error)
        await call.message.answer(
            "❌ Ma'lumotni yangilashda xatolik yuz berdi.",
            reply_markup=register_markup()
        )
    finally:
        await state.clear()

# Bekor qilish
@router.callback_query(F.data == "cancel", UpdateFIOState.confirm)
async def cancel_update(call: types.CallbackQuery, state: FSMContext):
    await call.message.delete()
    await call.message.answer("Asosiy menyu", reply_markup=register_markup())
    await state.clear()
