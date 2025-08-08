from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, WebAppInfo
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder

def register_markup(): 
    return ReplyKeyboardMarkup(resize_keyboard=True, keyboard=[
        [
            KeyboardButton(text="👤Ro'yxatdan o'tish")
        ]
    ])
    
def get_confirm_button():
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="Tasdiqlash ✅", callback_data="confirm"))
    builder.add(InlineKeyboardButton(text="Bekor qilish ❌", callback_data="cancel"))
    return builder.as_markup()

def get_test():
    murkup = ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text='📝 Test ishlash')],
        [KeyboardButton(text='✏️ Ismni tahrirlash')],
        [KeyboardButton(text="📊 Statistika"), KeyboardButton(text="🏆 Mening natijalarim")]
    ], resize_keyboard=True, one_time_keyboard=False)
    return murkup
