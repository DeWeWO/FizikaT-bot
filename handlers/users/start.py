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
            greeting_text = f"Assalomu Aleykum,\nTest ishlash uchun ro'yxatdan o'ting \\."
            
            await message.answer(
                greeting_text,
                parse_mode=ParseMode.MARKDOWN_V2,
                reply_markup=register_markup()
            )
            
    except Exception as error:
        logger.error(f"Registration check error: {error}")
        await message.answer(
            "Assalomu alaykum!",
            reply_markup=register_markup()
        )