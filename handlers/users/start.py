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
    first_name = message.from_user.first_name or ""
    last_name = message.from_user.last_name or ""
    username = message.from_user.username or ""

    # Foydalanuvchini users jadvaliga qo‘shish
    user = None
    try:
        user = await db.add_user(
            first_name=first_name,
            last_name=last_name,
            username=username,
            telegram_id=telegram_id
        )
    except Exception as error:
        logger.info(error)

    if user:
        count = await db.count_users()
        msg = (f"[{make_title(user['first_name'] + ' ' + user['last_name'])}](tg://user?id={user['telegram_id']}) "
               f"bazaga qo'shildi.\nBazada {count} ta foydalanuvchi bor.")
    else:
        msg = f"[{make_title(first_name + ' ' + last_name)}](tg://user?id={telegram_id}) bazaga oldin qo'shilgan"

    # Adminlarga xabar yuborish
    for admin in ADMINS:
        try:
            await bot.send_message(
                chat_id=admin,
                text=msg,
                parse_mode=ParseMode.MARKDOWN_V2
            )
        except Exception as error:
            logger.info(f"Data did not send to admin: {admin}. Error: {error}")

    # Ro'yxatdan o‘tgan-o‘tmaganini tekshirish
    reg_user = await db.execute(
        "SELECT * FROM register WHERE telegram_id = $1",
        telegram_id,
        fetchrow=True
    )

    if reg_user:
        await message.answer(
            f"✅ Siz allaqachon ro‘yxatdan o‘tgansiz!\n\n"
            f"👤 <i>FIO</i>: <b>{reg_user['fio']}</b>\n"
            f"🆔 <i>Telegram ID:</i> <code>{reg_user['telegram_id']}</code>",
            reply_markup=get_test()
        )
    else:
        await message.answer(
            f"Assalomu alaykum {make_title(first_name + ' ' + last_name)}\!",
            parse_mode=ParseMode.MARKDOWN_V2,
            reply_markup=register_markup()
        )
