from config import BOT_TOKEN
import asyncio
import logging
import sys
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.types import Message
from aiogram.fsm.storage.memory import MemoryStorage
from db import create_users_table, add_new_user, create_new_registered_user_table, add_new_registered_user
from buttons import main_markup
from register import router

TOKEN = BOT_TOKEN
dp = Dispatcher(storage=MemoryStorage())
# create_users_table()
# create_new_registered_user_table()

@dp.message(CommandStart())
async def command_start(message: Message) -> None:
    try:
        telegram_id = message.from_user.id
        first_name = message.from_user.first_name
        last_name = message.from_user.last_name
        username = message.from_user.username
        add_new_user(telegram_id, first_name, last_name, username)
    except Exception as error:
        logging.error(error)
    finally:
        await message.answer(f"Hello, {first_name}!\n\nSizing id: {telegram_id}", reply_markup=main_markup())



async def main() -> None:
    dp.include_router(router)
    bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        logging.basicConfig(level=logging.INFO, stream=sys.stdout)
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("Bot to'xtadi!")