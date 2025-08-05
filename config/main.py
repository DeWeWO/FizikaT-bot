from config import BOT_TOKEN
import asyncio
import logging
import sys
from aiogram import Bot, Dispatcher, html, types, F
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, ReplyKeyboardRemove
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.context import FSMContext
from db import create_users_table, add_new_user, create_new_registered_user_table
from buttons import main_markup, get_confirm_button
from states import RegisterState

TOKEN = BOT_TOKEN
dp = Dispatcher(storage=MemoryStorage())
# db = create_users_table()
create_new_registered_user_table()

@dp.message(CommandStart())
async def command_start(message: Message) -> None:
    try:
        telegram_id = message.from_user.id
        first_name = message.from_user.first_name
        last_name = message.from_user.last_name
        username = message.from_user.username
        add_new_user(telegram_id, first_name, last_name, username, '', '')
    except Exception as error:
        logging.error(error)
    finally:
        await message.answer(f"Hello, {first_name}!\n\nSizing id: {telegram_id}", reply_markup=main_markup())

@dp.message(F.text == "👤Ro'yxatdan o'tish")
async def start_register(message: types.Message, state: FSMContext):
    await message.answer("<b>👤 Ism va familiyangizni to'liq kiriting:</b>\n\n<i>Na'muna: Abudllayev Abdulla</i>", reply_markup=ReplyKeyboardRemove())
    await state.set_state(state=RegisterState.fio)

@dp.message(RegisterState.fio, F.text)
async def get_fio(message: types.Message, state: FSMContext):
    fio = message.text
    await state.set_data({"fio": fio})
    await message.answer("<b>✅ Yo'nalishingizni kiriting:</b>\n\n<i>Na'muna: Axborot xavfsizligi</i>")
    await state.set_state(state=RegisterState.discipline)

@dp.message(RegisterState.discipline, F.text)
async def get_discipline(message: types.Message, state: FSMContext):
    discipline = message.text
    if discipline:
        await state.set_data({"discipline": discipline})
        await message.answer("<b>👥 guruhingizni kiriting:</b>\n\n<i>Na'muna: 401</i>")
        await state.set_state(state=RegisterState.user_group)
    else:
        await message.answer("Yo'nalishingizni to'g'ri kiriting")

@dp.message(RegisterState.user_group, F.text)
async def get_group(message: types.Message, state: FSMContext):
    user_group = message.text
    await state.set_data({"user_group": user_group})
    data = await state.get_data()
    text = f"👤FISH: {data.get('fio')}\n⤴️Yo'nalish: {data.get('discipline')}\n👥Guruh: {data.get('user_group')}"
    await message.answer(f"{text}\n\n<b>Ma'lumotlaringiz to'g'riligini tasdiqlang</b>", reply_markup=get_confirm_button())
    await state.set_state(state=RegisterState.confirm)


async def main() -> None:
    bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        logging.basicConfig(level=logging.INFO, stream=sys.stdout)
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("Bot to'xtadi!")