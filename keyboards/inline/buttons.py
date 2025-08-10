from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


inline_keyboard = [[
    InlineKeyboardButton(text="✅ Yes", callback_data='yes'),
    InlineKeyboardButton(text="❌ No", callback_data='no')
]]
are_you_sure_markup = InlineKeyboardMarkup(inline_keyboard=inline_keyboard)

keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Tasdiqlash", callback_data="confirm_admin_reg"),
            InlineKeyboardButton(text="❌ Bekor qilish", callback_data="cancel_admin_reg")
        ]
    ])