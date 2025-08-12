from aiogram import Router, types, F
from aiogram.filters import CommandStart
from aiogram.enums.parse_mode import ParseMode
from aiogram.client.session.middlewares.request_logging import logger
from loader import db
from aiogram import Bot
from aiogram.enums import ChatType
from keyboards.reply.buttons import register_markup, get_test, for_admin

router = Router()


@router.message(CommandStart(), F.chat.type.in_([ChatType.PRIVATE]))
async def do_start(message: types.Message, bot: Bot):
    telegram_id = message.from_user.id
    
    # Admin tekshiruvi (custom user jadvalidan)
    try:
        custom_users = await db.select_all_custom_users()
        is_admin = False
        if custom_users:
            # Custom user jadvalida telegram_id mavjudligini tekshirish
            for user in custom_users:
                if user.get('telegram_id') == telegram_id:
                    is_admin = True
                    break
        
        if is_admin:
            await message.answer(
                "✅ Admin sifatida tizimga kirdingiz.\n\n🔗 Admin panelga kirish uchun: <b>✏️ Test tuzish</b> tugmasini bosing",
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
        # API endpoint ishlatamiz
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