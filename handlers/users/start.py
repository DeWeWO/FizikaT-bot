from aiogram import Router, types, F
from aiogram.filters import CommandStart
from aiogram.enums.parse_mode import ParseMode
from aiogram.client.session.middlewares.request_logging import logger
from loader import db
from aiogram import Bot
from aiogram.enums import ChatType
from keyboards.reply.buttons import register_markup, get_test, for_admin
from data.config import CREATOR_ID

router = Router()


@router.message(CommandStart(), F.chat.type.in_([ChatType.PRIVATE]))
async def do_start(message: types.Message, bot: Bot):
    telegram_id = message.from_user.id
    username = message.from_user.username or message.from_user.full_name

    # Creator tekshiruvi - har qanday holatda creator o'tadi
    if CREATOR_ID is not None and int(telegram_id) == int(CREATOR_ID):
        await message.answer(
            "💻 <b>Creator</b> sifatida tizimga kirdingiz.\n\n"
            "🔗 Admin panelga kirish uchun: <b>✏️ Test tuzish</b> tugmasini bosing\n\n",
            reply_markup=for_admin(),
            parse_mode=ParseMode.HTML
        )
        logger.info(f"Creator foydalanuvchiga javob yuborildi: {telegram_id}")
        return

    # Admin tekshiruvi
    try:
        admin_result = await db.check_telegram_admin(telegram_id=telegram_id)
        is_admin = bool(admin_result and admin_result.get("success") and admin_result.get("is_admin"))

        if is_admin:
            login_hint = admin_result.get("username") or username or telegram_id
            await message.answer(
                "✅ Admin sifatida tizimga kirdingiz.\n\n"
                "🔗 Admin panelga kirish uchun: <b>✏️ Test tuzish</b> tugmasini bosing\n\n"
                f"Sizni loginingiz: <code>{login_hint}</code>",
                reply_markup=for_admin(),
                parse_mode=ParseMode.HTML
            )
            logger.info(f"Admin foydalanuvchiga javob yuborildi: {telegram_id}")
            return

    except Exception as error:
        logger.error(f"Admin check error: {error}")
        # Admin tekshiruvida xatolik bo'lsa, oddiy foydalanuvchi sifatida davom etish

    # Ro'yxatdan o'tganligini tekshirish
    try:
        check_result = await db.check_registration(telegram_id=telegram_id)
        is_registered = check_result and check_result.get('registered', False)
        
        if is_registered:
            fio = check_result.get('fio', 'Noma\'lum')
            await message.answer(
                f"✅ Siz allaqachon ro'yxatdan o'tgansiz.\n\n"
                f"👤 <i>FIO</i>: <b>{fio}</b>\n",
                reply_markup=get_test(),
                parse_mode=ParseMode.HTML
            )
            logger.info(f"Ro'yxatdan o'tgan foydalanuvchiga javob yuborildi: {telegram_id}")
        else:
            # Salomlashish xabari
            greeting_text = f"Assalomu Aleykum,\nTest ishlash uchun ro'yxatdan o'ting\\."
            
            await message.answer(
                greeting_text,
                parse_mode=ParseMode.MARKDOWN_V2,
                reply_markup=register_markup()
            )
            
    except Exception as error:
        logger.error(f"Registration check error: {error}")
        await message.answer("Assalomu alaykum!", reply_markup=register_markup())