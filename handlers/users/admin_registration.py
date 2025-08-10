from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from states.AdminRegistration import AdminRegistration
import aiohttp
import re
from data import config

admin_router = Router()

DJANGO_API_URL = config.API_BASE_URL

@admin_router.message(Command("register_admin"))
async def start_admin_registration(message: Message, state: FSMContext):
    """Admin ro'yxatdan o'tishni boshlash"""
    telegram_id = message.from_user.id
    is_admin = await check_existing_admin(telegram_id)
    
    if is_admin:
        await message.answer(
            "✅ Siz allaqachon admin sifatida ro'yxatdan o'tgansiz!\n"
            "Admin panelga kirish uchun /admin_login buyrug'ini ishlating."
        )
        return
    
    await message.answer(
        "🔐 Admin ro'yxatdan o'tish jarayonini boshlaymiz.\n\n"
        "Ismingizni kiriting:\n"
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
    
    if len(last_name) < 2:
        await message.answer("❌ Familiya kamida 2 ta belgidan iborat bo'lishi kerak. Qaytadan kiriting:")
        return
    
    if not re.match(r'^[a-zA-Zа-яА-ЯёЁ\s]+$', last_name):
        await message.answer("❌ Familiya faqat harflardan iborat bo'lishi kerak. Qaytadan kiriting:")
        return
    
    await state.update_data(last_name=last_name)
    
    await message.answer(
        "Django admin paneli uchun username (login) kiriting:\n\n"
        "📝 Username talablari:\n"
        "• Kamida 3 ta belgi\n"
        "• Faqat harflar, raqamlar va _ belgisi\n"
        "• Masalan: admin_john, user123, my_admin\n\n"
        "Username kiriting:"
    )
    await state.set_state(AdminRegistration.waiting_for_username)

@admin_router.message(AdminRegistration.waiting_for_username)
async def process_username(message: Message, state: FSMContext):
    """Username qabul qilish va tekshirish"""
    username = message.text.strip().lower()
    
    # Username validatsiyasi
    if len(username) < 3:
        await message.answer("❌ Username kamida 3 ta belgidan iborat bo'lishi kerak!")
        return
    
    if not re.match(r'^[a-z0-9_]+$', username):
        await message.answer("❌ Username faqat kichik harflar, raqamlar va _ belgisini o'z ichiga olishi mumkin!")
        return
    
    # Username mavjudligini tekshirish
    is_available = await check_username_availability(username)
    if not is_available:
        await message.answer(f"❌ '{username}' username allaqachon band! Boshqa username tanlang:")
        return
    
    await state.update_data(username=username)
    
    await message.answer(
        f"✅ Username: {username}\n\n"
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
    
    await state.update_data(password=password)
    data = await state.get_data()
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Tasdiqlash", callback_data="confirm_admin_reg"),
            InlineKeyboardButton(text="❌ Bekor qilish", callback_data="cancel_admin_reg")
        ]
    ])
    
    await message.answer(
        f"📝 Ma'lumotlaringizni tekshiring:\n\n"
        f"👤 Ism: {data['first_name']}\n"
        f"👤 Familiya: {data['last_name']}\n"
        f"🔐 Username: {data['username']}\n"
        f"🔒 Parol: {'*' * len(password)}\n"
        f"📱 Telegram: @{message.from_user.username or 'Username yo\'q'}\n"
        f"🆔 Telegram ID: {message.from_user.id}\n\n"
        f"⚠️ Ma'lumotlar to'g'rimi?",
        reply_markup=keyboard
    )
    await state.set_state(AdminRegistration.waiting_for_confirmation)

@admin_router.callback_query(F.data == "confirm_admin_reg", AdminRegistration.waiting_for_confirmation)
async def confirm_registration(callback: CallbackQuery, state: FSMContext):
    """Ro'yxatdan o'tishni tasdiqlash"""
    await callback.message.edit_text("⏳ Admin akkauntini yaratyapman...")
    
    data = await state.get_data()
    
    registration_data = {
        "telegram_id": callback.from_user.id,
        "first_name": data['first_name'],
        "last_name": data['last_name'],
        "username": data['username'],
        "password": data['password'],
        "telegram_username": callback.from_user.username,
        "is_superuser": True,  # yoki False qilib qo'yishingiz mumkin
        "is_staff": True
    }
    
    success = await register_admin_api(registration_data)
    
    try:
        if success.get('success'):
            await callback.message.edit_text(
                f"🎉 Admin ro'yxatdan o'tish muvaffaqiyatli yakunlandi!\n\n"
                f"👤 Ism-familiya: {data['first_name']} {data['last_name']}\n"
                f"🔐 Username: {data['username']}\n"
                f"📱 Telegram: @{callback.from_user.username or 'N/A'}\n\n"
                f"✅ Django admin panelga kirish huquqingiz faollashtirildi!\n\n"
                f"🔗 Admin panelga kirish uchun: /admin_login\n\n"
                f"⚠️ Login ma'lumotlarini xavfsiz saqlang!"
            )
        else:
            error_message = success.get('message', 'Noma\'lum xatolik')
            await callback.message.edit_text(
                f"❌ Ro'yxatdan o'tishda xatolik:\n\n"
                f"{error_message}\n\n"
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

@admin_router.message(Command("admin_login"))
async def admin_login_command(message: Message):
    """Admin panelga kirish havolasi"""
    telegram_id = message.from_user.id
    
    await message.answer("🔍 Admin huquqlaringizni tekshiryapman...")
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{DJANGO_API_URL}/get-admin-token/{telegram_id}/",
                headers={"ngrok-skip-browser-warning": "true"}
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get('success'):
                        token = data.get('session_token')
                        admin_url = f"{DJANGO_API_URL}/telegram-login/{token}/"
                        username = data.get('username', 'N/A')
                        
                        superuser_text = "🔥 Superuser" if data.get('is_superuser') else "👤 Admin"
                        
                        await message.answer(
                            f"✅ {superuser_text} huquqlari tasdiqlandi!\n\n"
                            f"👤 Username: {username}\n"
                            f"🔗 <a href='{admin_url}'>Django Admin Panelga kirish</a>\n\n"
                            f"⚠️ Bu havola faqat siz uchun!\n"
                            f"🔒 Havola 10 daqiqadan so'ng yaroqsiz bo'ladi.\n"
                            f"🚫 Hech kim bilan ulashmang!",
                            parse_mode="HTML",
                            disable_web_page_preview=True
                        )
                    else:
                        await message.answer(
                            "❌ Sizda admin huquqlari yo'q!\n\n"
                            "🔐 Admin bo'lish uchun: /register_admin"
                        )
                else:
                    await message.answer(
                        "❌ Server bilan bog'lanishda muammo!\n\n"
                        "🔄 Qaytadan urinib ko'ring: /admin_login"
                    )
    except Exception as e:
        print(f"Admin login error: {e}")
        await message.answer(
            "❌ Xatolik yuz berdi!\n\n"
            "🔄 Qaytadan urinish: /admin_login"
        )

@admin_router.message(Command("admin_help"))
async def admin_help_command(message: Message):
    """Admin buyruqlari haqida yordam"""
    help_text = """
🔧 ADMIN BUYRUQLARI:

🆕 Ro'yxatdan o'tish:
/register_admin - Admin sifatida ro'yxatdan o'tish

🔗 Kirish:
/admin_login - Admin panel linkini olish

🆘 Yordam:
/admin_help - Bu yordam ma'lumoti
/cancel - Faol jarayonni bekor qilish

📋 Ro'yxatdan o'tish jarayoni:
1️⃣ Ism-familiyangizni kiriting
2️⃣ Django uchun username tanlang
3️⃣ Xavfsiz parol yarating
4️⃣ Ma'lumotlarni tasdiqlang
5️⃣ Admin panelga kiring!

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
    """Mavjud admin ekanligini tekshirish"""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{DJANGO_API_URL}/check-telegram-admin/{telegram_id}/",
                headers={"ngrok-skip-browser-warning": "true"}
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get('is_admin', False)
                return False
    except Exception as e:
        print(f"Admin check error: {e}")
        return False

async def check_username_availability(username: str) -> bool:
    """Username mavjudligini tekshirish"""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{DJANGO_API_URL}/check-username/{username}/",
                headers={"ngrok-skip-browser-warning": "true"}
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get('available', False)
                return False
    except Exception as e:
        print(f"Username check error: {e}")
        return False

async def register_admin_api(registration_data: dict) -> dict:
    """Django API orqali admin ro'yxatdan o'tkazish"""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{DJANGO_API_URL}/telegram-admin-register/",
                json=registration_data,
                headers={"ngrok-skip-browser-warning": "true"}
            ) as response:
                return await response.json()
    except Exception as e:
        print(f"Registration API error: {e}")
        return {
            'success': False,
            'message': f'Server bilan bog\'lanishda xatolik: {str(e)}'
        }