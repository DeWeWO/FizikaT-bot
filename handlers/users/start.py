from aiogram import Router, types
from aiogram.filters import CommandStart
from aiogram.enums.parse_mode import ParseMode
from aiogram.client.session.middlewares.request_logging import logger
from loader import db, bot
from data.config import ADMINS
from utils.extra_datas import make_title
from keyboards.reply.buttons import register_markup, get_test

router = Router()


@router.message(CommandStart())
async def do_start(message: types.Message):
    telegram_id = message.from_user.id
    full_name = message.from_user.full_name
    username = message.from_user.username
    user = None
    try:
        user = await db.add_user(telegram_id=telegram_id, full_name=full_name, username=username)
    except Exception as error:
        logger.info(error)
    if user:
        count = await db.count_users()
        msg = (f"[{make_title(user['full_name'])}](tg://user?id={user['telegram_id']}) bazaga qo'shildi.\nBazada {count} ta foydalanuvchi bor.")
    else:
        msg = f"[{make_title(full_name)}](tg://user?id={telegram_id}) bazaga oldin qo'shilgan"
    for admin in ADMINS:
        try:
            await bot.send_message(
                chat_id=admin,
                text=msg,
                parse_mode=ParseMode.MARKDOWN_V2
            )
        except Exception as error:
            logger.info(f"Data did not send to admin: {admin}. Error: {error}")
            
        user = await db.get_user(message.from_user.id)
    
        if user:
            await message.answer(
                f"✅ Siz allaqachon ro‘yxatdan o‘tgansiz!\n\n"
                f"👤 <i>Ism</i>: <b>{user['full_name']}</b>\n"
                f"🗣 <i>Username:</i> @{user['username'] or 'Yo‘q'}",
                reply_markup=get_test()
            )
        else:
            await message.answer(f"Assalomu alaykum {make_title(full_name)}!", parse_mode=ParseMode.MARKDOWN_V2, reply_markup=register_markup())
