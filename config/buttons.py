from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder

def main_markup(): 
    return ReplyKeyboardMarkup(resize_keyboard=True, keyboard=[
        [
            KeyboardButton(text="👤Ro'yxatdan o'tish")
        ]
    ])
    
def get_confirm_button():
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="Tasdiqlash ✅", callback_data="correct"))
    builder.add(InlineKeyboardButton(text="Bekor qilish ❌", callback_data="correct"))
    return builder.as_markup()