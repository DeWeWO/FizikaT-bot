from aiogram import Router
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import aiohttp

router = Router()

API_CATEGORIES_URL = "https://dd2b680720c7.ngrok-free.app/api/categories/"  # sizning DRF API manzilingiz
PAGE_SIZE = 10

async def fetch_categories():
    async with aiohttp.ClientSession() as session:
        async with session.get(API_CATEGORIES_URL) as resp:
            return await resp.json()

def generate_category_text(categories, page):
    PAGE_SIZE = 10  # yoki tashqarida aniqlangan bo‘lsa, olib tashlang
    start = page * PAGE_SIZE
    end = start + PAGE_SIZE
    selected = categories[start:end]

    lines = []
    for i, cat in enumerate(selected, start=1):
        title = cat.get("title", "Noma'lum")
        description = cat.get("description", "")

        # Description ni 50 belgigacha qisqartiramiz (oxiriga "..." qo‘shamiz agar uzun bo‘lsa)
        short_desc = (description[:20] + "...") if len(description) > 50 else description

        lines.append(f"{i}. <b>{title}.</b>\n<i>{short_desc}</i>")

    return "\n".join(lines)


def generate_category_buttons(categories, page):
    start = page * PAGE_SIZE
    end = start + PAGE_SIZE
    selected = categories[start:end]

    keyboard = InlineKeyboardMarkup(inline_keyboard=[])

    # Har bir category uchun [1], [2], [3], ... tugma — 5 tadan 2 qatorga ajratiladi
    row = []
    for i, cat in enumerate(selected, start=1):
        btn = InlineKeyboardButton(
            text=str(i),
            callback_data=f"select_category:{cat['slug']}"
        )
        row.append(btn)
        if i % 5 == 0:  # har 5 tadan keyin yangi qator
            keyboard.inline_keyboard.append(row)
            row = []

    if row:  # agar oxirida 5 tadan kam tugma qolgan bo‘lsa, ularni ham qo‘shamiz
        keyboard.inline_keyboard.append(row)


    # Navigatsiya tugmalari
    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton(text="⬅ Orqaga", callback_data=f"nav_page:{page-1}"))
    nav.append(InlineKeyboardButton(text="❌ Bekor qilish", callback_data="cancel_test"))
    if end < len(categories):
        nav.append(InlineKeyboardButton(text="Oldinga ➡", callback_data=f"nav_page:{page+1}"))

    keyboard.inline_keyboard.append(nav)
    return keyboard
