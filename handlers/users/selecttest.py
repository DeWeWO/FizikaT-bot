from aiogram import types, F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from data import config

router = Router()
WEBAPP_BASE_URL = f"{config.API_BASE_URL}/categories/"

@router.callback_query(F.data.startswith("select_category:"))
async def select_category(callback: types.CallbackQuery, state: FSMContext):
    slug = callback.data.split(":")[1]

    # FSMContext'dan kategoriyalarni olish
    data = await state.get_data()
    categories = data.get("categories", [])

    # Slug bo'yicha title topish
    category_title = next(
        (cat["title"] for cat in categories if cat["slug"] == slug),
        slug  # agar topilmasa, slugni o'zini ishlatadi
    )
    telegram_id = callback.from_user.id
    # WebApp tugma
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🚀 Testni boshlash",
                    web_app=WebAppInfo(url=f"{WEBAPP_BASE_URL}{slug}/questions/?telegram_id={telegram_id}")
                )
            ]
        ]
    )

    await callback.message.delete()
    await callback.message.answer(
        f"✅ Siz <b>{category_title}</b> ni tanladingiz.",
        parse_mode="HTML",
        reply_markup=keyboard
    )
    await callback.answer()