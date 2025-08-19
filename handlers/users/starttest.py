from aiogram import types, F, Router
from aiogram.fsm.context import FSMContext
from keyboards.inline.chosetest import fetch_categories, generate_category_text, generate_category_buttons
from aiogram.enums import ChatType

router = Router()

@router.message(F.text == "📝 Test ishlash", F.chat.type.in_([ChatType.PRIVATE]))
async def handle_test_start(message: types.Message, state: FSMContext):
    categories = await fetch_categories()
    if not categories:
        await message.answer("❌ Testlar yuklanmadi. Keyinroq qayta urinib ko'ring.")
        return
    
    await state.update_data(categories=categories)
    page = 0
    text = generate_category_text(categories, page)
    keyboard = generate_category_buttons(categories, page)
    await message.answer(f"📜 Mavjud variantlar:\n\n{text}", reply_markup=keyboard)

@router.callback_query(F.data.startswith("nav_page:"))
async def navigate_categories(callback: types.CallbackQuery, state: FSMContext):
    page = int(callback.data.split(":")[1])
    data = await state.get_data()
    categories = data.get("categories", [])
    
    if not categories:
        await callback.answer("❌ Testlar topilmadi", show_alert=True)
        return
    
    text = generate_category_text(categories, page)
    keyboard = generate_category_buttons(categories, page)
    await callback.message.edit_text(f"📜 Mavjud variantlar (sahifa {page+1}):\n\n{text}", reply_markup=keyboard)
    await callback.answer()

@router.callback_query(F.data == "cancel_test")
async def cancel_test(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text(text="❌ Test yechish bekor qilindi.")
    await callback.answer()

@router.callback_query(F.data.startswith("nav_page_disabled:"))
async def results_nav_disabled(callback: types.CallbackQuery):
    direction = callback.data.split(":")[1]
    if direction == "prev":
        await callback.answer("❌ Bu birinchi sahifa", show_alert=False)
    else:
        await callback.answer("❌ Bu oxirgi sahifa", show_alert=False)
