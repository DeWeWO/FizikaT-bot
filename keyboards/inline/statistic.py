from datetime import datetime
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
    for i, cat in enumerate(selected, 1):
        title = cat.get("title", "Noma'lum")
        description = cat.get("description", "")
        
        short_desc = (description[:30] + "...") if len(description) > 20 else description
        lines.append(f"{i}. <b>{title}</b> | <i>{short_desc}</i>")

    return "\n".join(lines)

def generate_category_buttons(categories, page):
    start = page * PAGE_SIZE
    end = start + PAGE_SIZE
    selected = categories[start:end]
    total_pages = (len(categories) - 1) // PAGE_SIZE + 1

    keyboard = []

    # Kategoriya tugmalari
    row = []
    for i, cat in enumerate(selected, 1):
        row.append(InlineKeyboardButton(text=str(i), callback_data=f"result_category:{cat['slug']}"))
        if i % 5 == 0:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)

    # Navigatsiya tugmalari
    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton(text="⬅️ Orqaga", callback_data=f"nav_page:{page-1}"))
    else:
        nav.append(InlineKeyboardButton(text="⬅️ Orqaga", callback_data="nav_disabled:prev"))
    
    nav.append(InlineKeyboardButton(text="❌ Bekor qilish", callback_data="cancel_statistic"))
    
    if page + 1 < total_pages:
        nav.append(InlineKeyboardButton(text="Oldinga ➡️", callback_data=f"nav_page:{page+1}"))
    else:
        nav.append(InlineKeyboardButton(text="Oldinga ➡️", callback_data="nav_disabled:next"))

    keyboard.append(nav)
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

STATIC_SIZE = 30

def generate_results_text(results, page, category_name):
    start = page * STATIC_SIZE
    end = start + STATIC_SIZE
    selected = results[start:end]
    
    lines = [f"📊 <b>{category_name}</b> natijalari:\n"]
    
    for i, result in enumerate(selected, start + 1):
        fio = result.get("fio", "Noma'lum")
        correct = result.get("correct_answers", 0)
        total = result.get("total_questions", 1)
        percentage = (correct / total * 100) if total > 0 else 0
        
        # Vaqtni formatlash
        completed_at = result.get("completed_at", "")
        if completed_at:
            dt = datetime.fromisoformat(completed_at.replace('Z', '+00:00'))
            date_str = dt.strftime("%d.%m.%Y %H:%M")
        else:
            date_str = "Noma'lum"
        
        emoji = "🟢" if percentage >= 86 else "🟡" if percentage >= 71 else "🔴"
        lines.append(f"{i}. {emoji} <b>{fio}</b>  "
                    f"   📝 {correct}/{total} ({percentage:.1f}%)  "
                    f"   🕐 {date_str}")
    
    return "\n".join(lines)

def generate_results_buttons(total_results, page, empty=False):
    if empty:
        return InlineKeyboardMarkup(inline_keyboard=[[
            InlineKeyboardButton(text="🔙 Variantlar", callback_data="back_to_categories")
        ]])
    
    total_pages = (total_results - 1) // STATIC_SIZE + 1
    nav = []
    
    if page > 0:
        nav.append(InlineKeyboardButton(text="⬅️ Orqaga", callback_data=f"results_page:{page-1}"))
    else:
        nav.append(InlineKeyboardButton(text="⬅️ Orqaga", callback_data="results_disabled:prev"))
    
    nav.append(InlineKeyboardButton(text="🔙 Variantlar", callback_data="back_to_categories"))
    
    if page + 1 < total_pages:
        nav.append(InlineKeyboardButton(text="Oldinga ➡️", callback_data=f"results_page:{page+1}"))
    else:
        nav.append(InlineKeyboardButton(text="Oldinga ➡️", callback_data="results_disabled:next"))

    return InlineKeyboardMarkup(inline_keyboard=[nav])