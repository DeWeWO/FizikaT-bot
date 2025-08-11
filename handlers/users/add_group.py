from aiogram import types, F, Router
from aiogram.enums import ChatType
from keyboards.inline.buttons import add_group

admin_router = Router()

@admin_router.message(F.text == "👥 Guruhga qo'shish", F.chat.type.in_([ChatType.PRIVATE]))
async def start_register(message: types.Message):
    text = "Guruhga qo'shish uchun pastdagi tugmani bosib guruh tanlang!"
    await message.answer(text=text, reply_markup=add_group)