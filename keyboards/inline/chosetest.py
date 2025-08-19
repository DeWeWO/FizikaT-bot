from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from utils.db.postgres import api_client

PAGE_SIZE = 10

async def fetch_categories():
    try:
        result = await api_client.get_categories()
        if result and 'results' in result:
            return result['results']
        return result if result else []
    except:
        return []

def generate_category_text(categories, page):
    start = page * PAGE_SIZE
    end = start + PAGE_SIZE
    selected = categories[start:end]

    lines = []
    for i, cat in enumerate(selected, start=1):
        title = cat.get("title", "Noma'lum")
        description = cat.get("description", "")
        
        short_desc = (description[:20] + "...") if len(description) > 20 else description
        lines.append(f"{i}. <b>{title}</b> | <i>{short_desc}</i>")

    return "\n".join(lines)

def generate_category_buttons(categories, page):
    start = page * PAGE_SIZE
    end = start + PAGE_SIZE
    selected = categories[start:end]

    keyboard = InlineKeyboardMarkup(inline_keyboard=[])

    # Kategoriya tugmalari
    row = []
    for i, cat in enumerate(selected, start=1):
        btn = InlineKeyboardButton(
            text=str(i),
            callback_data=f"select_category:{cat['slug']}"
        )
        row.append(btn)
        if i % 5 == 0:
            keyboard.inline_keyboard.append(row)
            row = []

    if row:
        keyboard.inline_keyboard.append(row)

    # Navigatsiya tugmalari
    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton(text="⬅️ Orqaga", callback_data=f"nav_page:{page-1}"))
    else:
        nav.append(InlineKeyboardButton(text="⬅️ Orqaga", callback_data="nav_page_disabled:prev"))
    
    nav.append(InlineKeyboardButton(text="❌ Bekor qilish", callback_data="cancel_statistic"))
    if end < len(categories):
        nav.append(InlineKeyboardButton(text="Oldinga ➡️", callback_data=f"nav_page:{page+1}"))
    else:
        nav.append(InlineKeyboardButton(text="Oldinga ➡️", callback_data="nav_page_disabled:next"))

    keyboard.inline_keyboard.append(nav)
    return keyboard