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

    # Foydalanuvchini users jadvaliga qo'shish/yangilash
    user = None
    try:
        # Yangi API endpoint ishlatamiz
        user_result = await db.add_user(
            first_name=first_name,
            last_name=last_name,
            username=username,
            telegram_id=telegram_id
        )
        
        if user_result and 'user' in user_result:
            user = user_result['user']
            created = user_result.get('created', False)
            logger.info(f"Foydalanuvchi {'yaratildi' if created else 'yangilandi'}: {telegram_id}")
        else:
            logger.error(f"User add/update failed for {telegram_id}")
            
    except Exception as error:
        logger.error(f"User add/get error: {error}")

    if user:
        try:
            count = await db.count_users()
            logger.info(f"Jami foydalanuvchilar soni: {count}")
        except Exception as error:
            logger.error(f"Count users error: {error}")
            count = "Noma'lum"

        # Xabar matnini to'g'ri shakllantirish
        try:
            full_name = f"{user.get('first_name', '')} {user.get('last_name', '')}".strip()
            if not full_name:
                full_name = f"User_{user.get('telegram_id', telegram_id)}"
            
            msg = (f"[{make_title(full_name)}](tg://user?id={user.get('telegram_id', telegram_id)}) "
                   f"bazaga qo'shildi\\.\nBazada {count} ta foydalanuvchi bor\\.")
        except Exception as error:
            logger.error(f"Message formatting error: {error}")
            msg = f"Foydalanuvchi bazaga qo'shildi\\. Bazada {count} ta foydalanuvchi bor\\."

        # Adminlarga xabar yuborish
        for admin in ADMINS:
            try:
                await bot.send_message(
                    chat_id=admin,
                    text=msg,
                    parse_mode=ParseMode.MARKDOWN_V2
                )
                logger.info(f"Admin {admin} ga xabar yuborildi")
            except Exception as error:
                logger.warning(f"Admin {admin} ga xabar yuborilmadi. Error: {error}")

    # Ro'yxatdan o'tganligini tekshirish
    try:
        # Yangi API endpoint ishlatamiz
        check_result = await db.check_registration(telegram_id=telegram_id)
        is_registered = check_result and check_result.get('registered', False)
        
        if is_registered:
            fio = check_result.get('fio', 'Noma\'lum')
            await message.answer(
                f"✅ Siz allaqachon ro'yxatdan o'tgansiz.\n\n"
                f"👤 <i>FIO</i>: <b>{fio}</b>\n"
                f"🆔 <i>Telegram ID:</i> <code>{telegram_id}</code>",
                reply_markup=get_test(),
                parse_mode=ParseMode.HTML
            )
            logger.info(f"Ro'yxatdan o'tgan foydalanuvchiga javob yuborildi: {telegram_id}")
        else:
            # Salomlashish xabari
            full_name = f"{first_name} {last_name}".strip()
            if not full_name:
                full_name = "Foydalanuvchi"
            
            greeting_text = f"Assalomu alaykum {make_title(full_name)}\\."
            
            await message.answer(
                greeting_text,
                parse_mode=ParseMode.MARKDOWN_V2,
                reply_markup=register_markup()
            )
            logger.info(f"Yangi foydalanuvchiga salomlashish yuborildi: {telegram_id}")
            
    except Exception as error:
        logger.error(f"Registration check error: {error}")
        # Fallback - oddiy salomlashish
        await message.answer(
            "Assalomu alaykum!",
            reply_markup=register_markup()
        )