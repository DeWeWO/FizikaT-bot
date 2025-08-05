from config import BOT_TOKEN
import asyncio
import logging
import sys
from os import getenv

from aiogram import Bot, Dispatcher, html, types, F
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart, Command
from aiogram.types import Message

TOKEN = BOT_TOKEN

dp = Dispatcher()

@dp.message(CommandStart())
async def command_start(message: Message) -> None:
    telegram_id = message.from_user.id
    first_name = message.from_user.first_name
    await message.answer(f"Hello, {first_name}!\nSizing id: {telegram_id}")
    
@dp.message(Command('help'))
async def do_help(message: types.Message):
    await message.reply("Qanday yordam berishim mumkin?")

@dp.message(Command('photo'))
async def send_photo(message: types.Message):
    await message.answer_photo(photo="https://docs.aiogram.dev/en/v3.21.0/_static/logo.png", caption="Aiogram bn qurilgan bot!")

@dp.message(F.text == "salom")
async def send_answer(message: types.Message):
    await message.answer("Voleykum assalom")

@dp.message()
async def echo(message: Message) -> None:
    try:
        await message.send_copy(chat_id=message.chat.id)
    except TypeError:
        await message.answer("Nice try!")

async def main() -> None:
    bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        logging.basicConfig(level=logging.INFO, stream=sys.stdout)
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("Bot to'xtadi!")