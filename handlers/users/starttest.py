from aiogram import types, F, Router
from aiogram.fsm.context import FSMContext
from keyboards.inline.chosetest import fetch_categories, generate_category_text, generate_category_buttons

router = Router()


@router.message(F.text == "📝 Test ishlash")
async def handle_test_start(message: types.Message, state: FSMContext):
    categories = await fetch_categories()
    await state.update_data(categories=categories)
    page = 0

    text = generate_category_text(categories, page)
    keyboard = generate_category_buttons(categories, page)

    await message.answer(f"🧪 So‘nggi 10 kategoriya:\n\n{text}", reply_markup=keyboard)

@router.callback_query(F.data.startswith("nav_page:"))
async def navigate_categories(callback: types.CallbackQuery, state: FSMContext):
    page = int(callback.data.split(":")[1])
    data = await state.get_data()
    categories = data.get("categories", [])

    text = generate_category_text(categories, page)
    keyboard = generate_category_buttons(categories, page)

    await callback.message.edit_text(f"🧪 Kategoriyalar (sahifa {page+1}):\n\n{text}", reply_markup=keyboard)
    await callback.answer()

@router.callback_query(F.data == "cancel_test")
async def cancel_test(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text(text="❌ Test yechish bekor qilindi.")
    await callback.answer()

@router.callback_query(F.data.startswith("select_category:"))
async def select_category(callback: types.CallbackQuery):
    slug = callback.data.split(":")[1]
    await callback.message.answer(f"✅ Siz `{slug}` kategoriyasini tanladingiz.", parse_mode="Markdown")
    await callback.answer()

