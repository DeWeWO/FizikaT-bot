from aiogram import types, F, Router
from aiogram.fsm.context import FSMContext
from keyboards.inline.statistic import (
    fetch_categories, generate_category_text, generate_category_buttons, 
    generate_results_text, generate_results_buttons
)
from aiogram.enums import ChatType
from utils.db.postgres import api_client

router = Router()

@router.message(F.text == "📊 Natijalar", F.chat.type.in_([ChatType.PRIVATE]))
async def handle_test_start(message: types.Message, state: FSMContext):
    categories = await fetch_categories()
    if not categories:
        await message.answer("❌ Natijalar topilmadi. Keyinroq qayta urinib ko'ring.")
        return
    
    await state.update_data(categories=categories)
    text = generate_category_text(categories, 0)
    keyboard = generate_category_buttons(categories, 0)
    await message.answer(f"📊 <b>Kerakli variantni tanlang va natijalarni ko'ring:</b>\n\n{text}", reply_markup=keyboard)

@router.callback_query(F.data.startswith("nav_page:"))
async def navigate_categories(callback: types.CallbackQuery, state: FSMContext):
    page = int(callback.data.split(":")[1])
    data = await state.get_data()
    categories = data.get("categories", [])
    
    if not categories:
        await callback.answer("❌ Natijalar topilmadi", show_alert=True)
        return
    
    total_pages = (len(categories) - 1) // 10 + 1
    if page < 0 or page >= total_pages:
        await callback.answer("❌ Bu sahifa mavjud emas", show_alert=True)
        return
    
    text = generate_category_text(categories, page)
    keyboard = generate_category_buttons(categories, page)
    await callback.message.edit_text(f"📊 Natijalar (sahifa {page+1}/{total_pages}):\n\n{text}", reply_markup=keyboard)
    await callback.answer()

@router.callback_query(F.data.startswith("result_category:"))
async def show_category_results(callback: types.CallbackQuery, state: FSMContext):
    slug = callback.data.split(":")[1]
    data = await state.get_data()
    categories = data.get("categories", [])
    
    category_name = next((cat['title'] for cat in categories if cat['slug'] == slug), "Noma'lum")
    
    results_data = await api_client.get_results(slug)
    
    if not results_data or not results_data.get('results'):
        await callback.message.edit_text(f"📊 {category_name}\n\n❌ Bunga natijalar topilmadi.", 
                                       reply_markup=generate_results_buttons(0, 0, True))
        await callback.answer()
        return
    
    results = results_data['results']
    
    await state.update_data(current_slug=slug, current_results=results, category_name=category_name)
    
    text = generate_results_text(results, 0, category_name)
    keyboard = generate_results_buttons(len(results), 0)
    await callback.message.edit_text(text, reply_markup=keyboard)
    await callback.answer()

@router.callback_query(F.data.startswith("results_page:"))
async def navigate_results(callback: types.CallbackQuery, state: FSMContext):
    page = int(callback.data.split(":")[1])
    data = await state.get_data()
    results = data.get("current_results", [])
    category_name = data.get("category_name", "Noma'lum")
    
    total_pages = (len(results) - 1) // 10 + 1
    if page < 0 or page >= total_pages:
        await callback.answer("❌ Bu sahifa mavjud emas", show_alert=False)
        return
    
    text = generate_results_text(results, page, category_name)
    keyboard = generate_results_buttons(len(results), page)
    await callback.message.edit_text(text, reply_markup=keyboard)
    await callback.answer()

@router.callback_query(F.data == "back_to_categories")
async def back_to_categories(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    categories = data.get("categories", [])
    
    if not categories:
        await callback.answer("❌ Natijalar topilmadi", show_alert=False)
        return
    
    text = generate_category_text(categories, 0)
    keyboard = generate_category_buttons(categories, 0)
    await callback.message.edit_text(f"📊 Natijalar:\n\n{text}", reply_markup=keyboard)
    await callback.answer()

@router.callback_query(F.data.startswith("nav_disabled:"))
async def nav_disabled(callback: types.CallbackQuery):
    direction = callback.data.split(":")[1]
    if direction == "prev":
        await callback.answer("❌ Bu birinchi sahifa", show_alert=False)
    else:
        await callback.answer("❌ Bu oxirgi sahifa", show_alert=False)

@router.callback_query(F.data.startswith("results_disabled:"))
async def results_nav_disabled(callback: types.CallbackQuery):
    direction = callback.data.split(":")[1]
    if direction == "prev":
        await callback.answer("❌ Bu birinchi sahifa", show_alert=False)
    else:
        await callback.answer("❌ Bu oxirgi sahifa", show_alert=False)

@router.callback_query(F.data == "cancel_statistic")
async def cancel_test(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("❌ Natijalarni ko'rish bekor qilindi.")
    await callback.answer()