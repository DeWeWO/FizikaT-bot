from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from states.AdminRegistration import AdminRegistration
import re
from data import config
from keyboards.inline.buttons import keyboard, admin_panel
from keyboards.reply.buttons import for_admin
from loader import db
from aiogram.enums import ChatType

admin_router = Router()

DJANGO_API_URL = config.ADMIN_URL

@admin_router.message(Command("register_admin"), F.chat.type.in_([ChatType.PRIVATE]))
async def start_admin_registration(message: Message, state: FSMContext):
    """Admin ro'yxatdan o'tishni boshlash"""
    telegram_id = message.from_user.id
    is_admin = await check_existing_admin(telegram_id)
    
    if is_admin:
        await message.answer(
            "✅ Siz allaqachon admin sifatida ro'yxatdan o'tgansiz!\n"
            "Admin panelga kirish uchun <b>✏️ Test tuzish</b> tugmasini bosing."
        )
        return
    
    await message.answer(
        "🔐 Admin ro'yxatdan o'tish jarayonini boshlaymiz.\n\n"
        "Ismingizni kiriting:\n\n"
        "❌ Bekor qilish uchun /cancel"
    )
    await state.set_state(AdminRegistration.waiting_for_first_name)

@admin_router.message(AdminRegistration.waiting_for_first_name)
async def process_first_name(message: Message, state: FSMContext):
    """Ism qabul qilish"""
    first_name = message.text.strip()
    
    if len(first_name) < 2:
        await message.answer("❌ Ism kamida 2 ta belgidan iborat bo'lishi kerak. Qaytadan kiriting:")
        return
    
    if not re.match(r'^[a-zA-Zа-яА-ЯёЁ\s]+$', first_name):
        await message.answer("❌ Ism faqat harflardan iborat bo'lishi kerak. Qaytadan kiriting:")
        return
    
    await state.update_data(first_name=first_name)
    await message.answer("Familiyangizni kiriting:")
    await state.set_state(AdminRegistration.waiting_for_last_name)

@admin_router.message(AdminRegistration.waiting_for_last_name)
async def process_last_name(message: Message, state: FSMContext):
    """Familiya qabul qilish"""
    last_name = message.text.strip()
    username = message.from_user.id
    
    if len(last_name) < 2:
        await message.answer("❌ Familiya kamida 2 ta belgidan iborat bo'lishi kerak. Qaytadan kiriting:")
        return
    
    if not re.match(r'^[a-zA-Zа-яА-ЯёЁ\s]+$', last_name):
        await message.answer("❌ Familiya faqat harflardan iborat bo'lishi kerak. Qaytadan kiriting:")
        return
    
    await state.update_data(last_name=last_name, username=username)
    
    await message.answer(
        f"👤 Username: {username}\n\n"
        f"Endi xavfsiz parol yarating:\n\n"
        f"🔒 Parol talablari:\n"
        f"• Kamida 8 ta belgi\n"
        f"• Kamida 1 ta katta harf (A-Z)\n"
        f"• Kamida 1 ta kichik harf (a-z)\n"
        f"• Kamida 1 ta raqam (0-9)\n"
        f"• Kamida 1 ta maxsus belgi (!@#$%^&*)\n\n"
        f"⚠️ Parolni xavfsiz joyda saqlang!\n"
        f"Parolni kiriting:"
    )
    await state.set_state(AdminRegistration.waiting_for_password)

@admin_router.message(AdminRegistration.waiting_for_password)
async def process_password(message: Message, state: FSMContext):
    """Parolni qabul qilish va validatsiya qilish"""
    password = message.text.strip()
    
    # Parol validatsiyasi
    validation_result = validate_password(password)
    if not validation_result['valid']:
        await message.answer(f"❌ {validation_result['message']}")
        return
    
    # Xavfsizlik uchun parol xabarini darhol o'chirish
    try:
        await message.delete()
    except Exception:
        pass
    
    # Parolni vaqtincha saqlash
    await state.update_data(temp_password=password)
    
    await message.answer(
        "✅ Parol qabul qilindi!\n\n"
        "🔄 Xavfsizlik uchun parolni qayta kiriting:"
    )
    await state.set_state(AdminRegistration.waiting_for_password_confirmation)

@admin_router.message(AdminRegistration.waiting_for_password_confirmation)
async def process_password_confirmation(message: Message, state: FSMContext):
    """Parol tasdiqlashni qabul qilish"""
    confirmation_password = message.text.strip()
    
    # Xavfsizlik uchun parol xabarini darhol o'chirish
    try:
        await message.delete()
    except Exception:
        pass
    
    # Oldingi parolni olish
    data = await state.get_data()
    original_password = data.get('temp_password')
    
    # Parollarni solishtirish
    if confirmation_password != original_password:
        await message.answer(
            "❌ Parollar mos kelmadi!\n\n"
            "🔒 Iltimos, parolni qaytadan kiriting:"
        )
        # Vaqtincha parolni o'chirish va qayta parol kiritishni so'rash
        await state.update_data(temp_password=None)
        await state.set_state(AdminRegistration.waiting_for_password)
        return
    
    await state.update_data(password=original_password)
    await state.update_data(temp_password=None)
    
    await message.answer("✅ Parol muvaffaqiyatli tasdiqlandi!")
    data = await state.get_data()
    username = data.get('username', message.from_user.id)
    
    await message.answer(
        f"📝 Ma'lumotlaringizni tekshiring:\n\n"
        f"👤 Ism: {data['first_name']}\n"
        f"👤 Familiya: {data['last_name']}\n"
        f"🔐 Username: {username}\n"
        f"🔒 Parol: {'*' * len(confirmation_password)}\n\n"
        f"⚠️ Ma'lumotlar to'g'rimi?",
        reply_markup=keyboard
    )
    await state.set_state(AdminRegistration.waiting_for_confirmation)

@admin_router.callback_query(F.data == "confirm_admin_reg", AdminRegistration.waiting_for_confirmation)
async def confirm_registration(callback: CallbackQuery, state: FSMContext):
    """Ro'yxatdan o'tishni tasdiqlash"""
    await callback.message.edit_text("⏳ Admin akkauntini yaratyapman...")
    
    data = await state.get_data()
    telegram_id = callback.from_user.id
    
    # Custom user jadvalga qo'shish uchun ma'lumotlar
    custom_user_data = {
        "telegram_id": telegram_id,
        "first_name": data['first_name'],
        "last_name": data['last_name'],
        "username": data['username'],
        "password": data['password']
    }
    
    try:
        # Custom user jadvalga admin ma'lumotlarini qo'shish
        success = await add_custom_user(custom_user_data)
        
        if success:
            await callback.message.edit_text(
                f"🎉 Admin ro'yxatdan o'tish muvaffaqiyatli yakunlandi!\n\n"
                f"👤 Ism-familiya: {data['first_name']} {data['last_name']}\n"
                f"🔐 Username: {data['username']}\n\n"
                f"✅ Ma'lumotlaringiz saqlandi!\n\n"
                f"🔗 Admin panelga kirish uchun: <b>✏️ Test tuzish</b> tugmasini bosing\n\n"
                f"⚠️ Login ma'lumotlarini xavfsiz saqlang!",
                reply_markup=for_admin()
            )
        else:
            await callback.message.edit_text(
                f"❌ Ro'yxatdan o'tishda xatolik yuz berdi!\n\n"
                f"🔄 Qaytadan urinish: /register_admin"
            )
    except Exception as e:
        await callback.answer("❌ Xatolik yuz berdi. Qaytadan urinib ko'ring.")
        print(f"Registration confirmation error: {e}")
    
    await state.clear()

@admin_router.callback_query(F.data == "cancel_admin_reg")
async def cancel_registration(callback: CallbackQuery, state: FSMContext):
    """Ro'yxatdan o'tishni bekor qilish"""
    await callback.message.edit_text(
        "❌ Admin ro'yxatdan o'tish bekor qilindi.\n\n"
        "🔄 Qaytadan boshlash: /register_admin"
    )
    await state.clear()

@admin_router.message(Command("cancel"))
async def cancel_any_process(message: Message, state: FSMContext):
    """Har qanday jarayonni bekor qilish"""
    current_state = await state.get_state()
    
    if current_state is None:
        await message.answer("❌ Hech qanday faol jarayon yo'q.")
        return
    
    await state.clear()
    await message.answer(
        "❌ Jarayon bekor qilindi.\n\n"
        "🔄 Qaytadan boshlash: /register_admin"
    )

@admin_router.message(F.text == "✏️ Test tuzish")
async def open_site(message: Message):
    await message.answer("Tugmani bosib web sahifaga o'ting", reply_markup=admin_panel)


@admin_router.message(Command("admin_help"))
async def admin_help_command(message: Message):
    """Admin buyruqlari haqida yordam"""
    help_text = """
🔧 ADMIN BUYRUQLARI:

🆕 Ro'yxatdan o'tish:
/register_admin - Admin sifatida ro'yxatdan o'tish

🔗 Kirish:
/admin_login - Admin panel login ma'lumotlarini olish

🆘 Yordam:
/admin_help - Bu yordam ma'lumoti
/cancel - Faol jarayonni bekor qilish

📋 Ro'yxatdan o'tish jarayoni:
1️⃣ Ism-familiyangizni kiriting
2️⃣ Xavfsiz parol yarating
3️⃣ Ma'lumotlarni tasdiqlang
4️⃣ Admin panelga kiring!

⚠️ Eslatma: Login ma'lumotlarini xavfsiz saqlang!
    """
    await message.answer(help_text)

# Utility functions
def validate_password(password: str) -> dict:
    """Parol kuchliligini tekshirish"""
    if len(password) < 8:
        return {"valid": False, "message": "Parol kamida 8 ta belgidan iborat bo'lishi kerak!"}
    
    if not re.search(r'[A-Z]', password):
        return {"valid": False, "message": "Parol kamida 1 ta katta harf o'z ichiga olishi kerak!"}
    
    if not re.search(r'[a-z]', password):
        return {"valid": False, "message": "Parol kamida 1 ta kichik harf o'z ichiga olishi kerak!"}
    
    if not re.search(r'[0-9]', password):
        return {"valid": False, "message": "Parol kamida 1 ta raqam o'z ichiga olishi kerak!"}
    
    if not re.search(r'[!@#$%^&*()_+\-=\[\]{};\':"\\|,.<>\/?]', password):
        return {"valid": False, "message": "Parol kamida 1 ta maxsus belgi (!@#$%^&*) o'z ichiga olishi kerak!"}
    
    return {"valid": True, "message": "Parol kuchli!"}

# API functions
async def check_existing_admin(telegram_id: int) -> bool:
    """Custom user jadvalidan admin ekanligini tekshirish"""
    try:
        custom_users = await db.select_all_custom_users()
        if custom_users:
            for user in custom_users:
                if user.get('telegram_id') == telegram_id:
                    return True
        return False
    except Exception as e:
        print(f"Admin check error: {e}")
        return False

import aiohttp
import json
import logging

logger = logging.getLogger(__name__)

async def create_admin_user_fixed(user_data: dict, base_url: str = "http://localhost:8000"):
    """To'g'ri URL bilan admin user yaratish"""
    
    # URL ni to'g'ri yig'ish - slash muammosini hal qilish
    if base_url.endswith('/'):
        base_url = base_url.rstrip('/')
    
    # URL pattern ga mos ravishda
    api_url = f"{base_url}/api/telegram-admin-register/"  # path pattern: 'api/telegram-admin-register/'
    
    logger.info(f"=== API SO'ROV ===")
    logger.info(f"URL: {api_url}")
    logger.info(f"Ma'lumotlar: {user_data}")
    
    try:
        headers = {
            'Content-Type': 'application/json; charset=utf-8',
            'Accept': 'application/json',
        }
        
        # Ma'lumotlarni JSON ga aylantirish
        json_payload = json.dumps(user_data, ensure_ascii=False)
        logger.info(f"JSON payload: {json_payload}")
        
        timeout = aiohttp.ClientTimeout(total=30)
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                api_url,
                data=json_payload,  # data= ishlatish (json= emas)
                headers=headers,
                timeout=timeout
            ) as response:
                
                logger.info(f"Response status: {response.status}")
                
                # Response textini olish
                response_text = await response.text()
                logger.info(f"Response text: {response_text}")
                
                # Status kodiga qarab javob berish
                if response.status == 200:
                    try:
                        result = json.loads(response_text)
                        return result
                    except json.JSONDecodeError:
                        return {
                            'success': False,
                            'message': f'Noto\'g\'ri JSON javob: {response_text}'
                        }
                
                elif response.status == 400:
                    try:
                        error_data = json.loads(response_text)
                        return error_data
                    except json.JSONDecodeError:
                        return {
                            'success': False,
                            'message': f'400 Error: {response_text}'
                        }
                
                else:
                    return {
                        'success': False,
                        'message': f'HTTP {response.status}: {response_text}'
                    }
    
    except aiohttp.ClientError as e:
        logger.error(f"Client xatoligi: {e}")
        return {
            'success': False,
            'message': f'Connection xatoligi: {str(e)}'
        }
    except Exception as e:
        logger.error(f"Kutilmagan xatolik: {e}")
        return {
            'success': False,
            'message': f'Kutilmagan xatolik: {str(e)}'
        }

# Yangilangan add_custom_user funksiyasi
async def add_custom_user(user_data: dict) -> bool:
    """Custom user jadvalga admin qo'shish - yangilangan"""
    try:
        # Ma'lumotlarni validatsiya qilish
        required_fields = ['telegram_id', 'first_name', 'last_name', 'username', 'password']
        for field in required_fields:
            if not user_data.get(field):
                logger.error(f"Majburiy maydon yo'q: {field}")
                return False
        
        # Ma'lumotlarni to'g'ri formatga keltirish
        complete_user_data = {
            "telegram_id": int(user_data['telegram_id']),
            "first_name": str(user_data['first_name']).strip(),
            "last_name": str(user_data['last_name']).strip(),
            "username": str(user_data['username']).strip().lower(),
            "password": str(user_data['password']),
            "telegram_username": user_data.get('telegram_username', ''),
            "is_staff": True,
            "is_superuser": True
        }
        
        logger.info(f"Admin user yaratish uchun so'rov: {complete_user_data['username']}")
        
        # API ga so'rov yuborish
        result = await create_admin_user_fixed(complete_user_data)
        
        # Natijani tekshirish
        if result and result.get('success'):
            logger.info("Admin user muvaffaqiyatli yaratildi")
            return True
        else:
            error_msg = result.get('message', 'Noma\'lum xatolik') if result else 'Server javob bermadi'
            logger.error(f"Admin user yaratishda xatolik: {error_msg}")
            print(f"Xatolik: {error_msg}")  # Debug uchun
            return False
            
    except Exception as e:
        logger.error(f"add_custom_user xatoligi: {e}")
        return False
