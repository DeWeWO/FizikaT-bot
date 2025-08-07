from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder

def make_test(): 
    return ReplyKeyboardMarkup(resize_keyboard=True, keyboard=[
        [
            KeyboardButton(text="📝 Test tuzish")
        ]
    ])
    
# def get_confirm_button():
#     builder = InlineKeyboardBuilder()
#     builder.add(InlineKeyboardButton(text="Tasdiqlash ✅", callback_data="confirm"))
#     builder.add(InlineKeyboardButton(text="Bekor qilish ❌", callback_data="cancel"))
#     return builder.as_markup()
