from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message
import asyncio
from datetime import datetime, timedelta
from aiogram.fsm.context import FSMContext
from typing import Optional
import jwt
import secrets
from states.AdminRegistration import AdminToken
from .admin_registration import check_existing_admin

admin_router = Router()

# Token konfiguratsiyasi
TOKEN_EXPIRY_HOURS = 24  # Token 24 soat amal qiladi
SECRET_KEY = "your_secret_key_here"  # Bu kalitni .env faylida saqlang

class TokenManager:
    """Admin token larni boshqarish uchun klass"""
    
    def __init__(self):
        self.active_tokens = {}  # {user_id: {"token": str, "expires_at": datetime}}
    
    def generate_token(self, user_id: int, username: str = None) -> dict:
        """Yangi token yaratish"""
        expires_at = datetime.now() + timedelta(hours=TOKEN_EXPIRY_HOURS)
        
        # JWT token yaratish
        payload = {
            'user_id': user_id,
            'username': username,
            'exp': expires_at.timestamp(),
            'iat': datetime.now().timestamp(),
            'type': 'admin_registration'
        }
        
        token = jwt.encode(payload, SECRET_KEY, algorithm='HS256')
        
        # Tokenni saqlash
        self.active_tokens[user_id] = {
            'token': token,
            'expires_at': expires_at,
            'created_at': datetime.now()
        }
        
        return {
            'token': token,
            'expires_at': expires_at,
            'expires_in_hours': TOKEN_EXPIRY_HOURS
        }
    
    def verify_token(self, token: str) -> Optional[dict]:
        """Tokenni tekshirish"""
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
            user_id = payload.get('user_id')
            
            # Tokenni active tokens dan tekshirish
            if user_id in self.active_tokens:
                stored_token = self.active_tokens[user_id]
                if stored_token['token'] == token:
                    # Muddatni tekshirish
                    if datetime.now() < stored_token['expires_at']:
                        return payload
                    else:
                        # Muddati tugagan tokenni o'chirish
                        del self.active_tokens[user_id]
                        return None
            return None
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None
    
    def refresh_token(self, user_id: int) -> Optional[dict]:
        """Tokenni yangilash"""
        if user_id in self.active_tokens:
            old_token_info = self.active_tokens[user_id]
            # Eski tokenni o'chirish
            del self.active_tokens[user_id]
            
            # Yangi token yaratish
            return self.generate_token(user_id)
        return None
    
    def revoke_token(self, user_id: int) -> bool:
        """Tokenni bekor qilish"""
        if user_id in self.active_tokens:
            del self.active_tokens[user_id]
            return True
        return False
    
    def get_token_info(self, user_id: int) -> Optional[dict]:
        """Token haqida ma'lumot olish"""
        if user_id in self.active_tokens:
            token_info = self.active_tokens[user_id]
            time_left = token_info['expires_at'] - datetime.now()
            
            return {
                'token': token_info['token'][:20] + "...",  # Xavfsizlik uchun qisqartirilgan
                'created_at': token_info['created_at'],
                'expires_at': token_info['expires_at'],
                'time_left_hours': max(0, time_left.total_seconds() / 3600),
                'is_expired': datetime.now() > token_info['expires_at']
            }
        return None
    
    def cleanup_expired_tokens(self):
        """Muddati tugagan tokenlarni tozalash"""
        expired_users = []
        current_time = datetime.now()
        
        for user_id, token_info in self.active_tokens.items():
            if current_time > token_info['expires_at']:
                expired_users.append(user_id)
        
        for user_id in expired_users:
            del self.active_tokens[user_id]
        
        return len(expired_users)

# Global token manager
token_manager = TokenManager()

# Admin ro'yxatdan o'tish tugagach token berish
@admin_router.message(AdminToken.final_confirmation)
async def finalize_registration(message: Message, state: FSMContext):
    """Ro'yxatdan o'tishni yakunlash va token berish"""
    if message.text.lower() in ['ha', 'yes', 'to\'g\'ri', 'tasdiqlash']:
        data = await state.get_data()
        user_id = message.from_user.id
        
        try:
            # Ma'lumotlarni bazaga saqlash
            # save_admin_to_database(data)  # Bu funktsiyani o'zingiz yozing
            
            # Token yaratish
            token_info = token_manager.generate_token(
                user_id=user_id,
                username=data.get('username', str(user_id))
            )
            
            await message.answer(
                f"🎉 Admin sifatida muvaffaqiyatli ro'yxatdan o'tdingiz!\n\n"
                f"🔑 Sizning admin tokeningiz:\n"
                f"<code>{token_info['token']}</code>\n\n"
                f"⏰ Token amal qilish muddati: {token_info['expires_in_hours']} soat\n"
                f"📅 Tugash sanasi: {token_info['expires_at'].strftime('%Y-%m-%d %H:%M')}\n\n"
                f"⚠️ Bu tokenni xavfsiz joyda saqlang!\n"
                f"💡 Token yangilash uchun: /refresh_token\n"
                f"📊 Token holati: /token_status",
                parse_mode="HTML"
            )
            
            await state.clear()
            
        except Exception as e:
            await message.answer(f"❌ Xatolik yuz berdi: {str(e)}")
    else:
        await message.answer("❌ Ro'yxatdan o'tish bekor qilindi.")
        await state.clear()

# Token yangilash komandasi
@admin_router.message(Command("refresh_token"))
async def refresh_admin_token(message: Message):
    """Admin tokenni yangilash"""
    telegram_id = message.from_user.id
    is_admin = await check_existing_admin(telegram_id)
    user_id = message.from_user.id
    
    # Foydalanuvchi admin ekanligini tekshirish
    if not is_admin(user_id):  # Bu funktsiyani o'zingiz yozing
        await message.answer("❌ Sizda admin huquqi yo'q!")
        return
    
    token_info = token_manager.refresh_token(user_id)
    
    if token_info:
        await message.answer(
            f"🔄 Token muvaffaqiyatli yangilandi!\n\n"
            f"🔑 Yangi tokeningiz:\n"
            f"<code>{token_info['token']}</code>\n\n"
            f"⏰ Amal qilish muddati: {token_info['expires_in_hours']} soat\n"
            f"📅 Tugash sanasi: {token_info['expires_at'].strftime('%Y-%m-%d %H:%M')}\n\n"
            f"⚠️ Eski token avtomatik bekor qilindi!",
            parse_mode="HTML"
        )
    else:
        await message.answer("❌ Token yangilashda xatolik yuz berdi.")

# Token holati komandasi
@admin_router.message(Command("token_status"))
async def check_token_status(message: Message):
    """Token holati haqida ma'lumot"""
    telegram_id = message.from_user.id
    is_admin = await check_existing_admin(telegram_id)
    user_id = message.from_user.id
    
    if not is_admin(user_id):
        await message.answer("❌ Sizda admin huquqi yo'q!")
        return
    
    token_info = token_manager.get_token_info(user_id)
    
    if token_info:
        status_emoji = "❌" if token_info['is_expired'] else "✅"
        
        await message.answer(
            f"📊 Token holati:\n\n"
            f"{status_emoji} Holat: {'Muddati tugagan' if token_info['is_expired'] else 'Faol'}\n"
            f"🔑 Token: {token_info['token']}\n"
            f"📅 Yaratilgan: {token_info['created_at'].strftime('%Y-%m-%d %H:%M')}\n"
            f"⏰ Tugash vaqti: {token_info['expires_at'].strftime('%Y-%m-%d %H:%M')}\n"
            f"⏳ Qolgan vaqt: {token_info['time_left_hours']:.1f} soat\n\n"
            f"💡 Tokenni yangilash: /refresh_token"
        )
    else:
        await message.answer(
            "❌ Faol tokeningiz topilmadi!\n"
            "🔄 Yangi token olish uchun: /register_admin"
        )

# Token bekor qilish komandasi
@admin_router.message(Command("revoke_token"))
async def revoke_admin_token(message: Message):
    """Admin tokenni bekor qilish"""
    user_id = message.from_user.id
    
    if token_manager.revoke_token(user_id):
        await message.answer(
            "🚫 Tokeningiz muvaffaqiyatli bekor qilindi!\n"
            "🔄 Yangi token olish uchun: /register_admin"
        )
    else:
        await message.answer("❌ Bekor qilinadigan token topilmadi.")

# Muddati tugagan tokenlarni avtomatik tozalash (background task)
async def token_cleanup_task():
    """Muddati tugagan tokenlarni muntazam tozalash"""
    while True:
        try:
            cleaned_count = token_manager.cleanup_expired_tokens()
            if cleaned_count > 0:
                print(f"Tozalandi: {cleaned_count} ta muddati tugagan token")
        except Exception as e:
            print(f"Token tozalashda xatolik: {e}")
        
        # Har soatda tekshirish
        await asyncio.sleep(3600)  # 1 soat

# Bot ishga tushganda background taskni boshlash
async def start_background_tasks():
    """Background tasklarni ishga tushirish"""
    asyncio.create_task(token_cleanup_task())