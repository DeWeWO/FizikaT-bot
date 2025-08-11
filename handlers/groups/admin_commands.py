# handlers/groups/admin_commands.py - TO'G'IRLANGAN VERSIYA
from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.enums import ChatType, ChatMemberStatus
from aiogram.exceptions import TelegramBadRequest
import logging

router = Router()

# Ruxsat berilgan foydalanuvchilar ro'yxati
ALLOWED_USERS = [5355824558]  # O'z Telegram ID'ingizni qo'shing

def is_authorized(user_id: int) -> bool:
    """Foydalanuvchining ruxsati borligini tekshiradi"""
    return user_id in ALLOWED_USERS

async def is_bot_admin(message: types.Message) -> bool:
    """Bot admin ekanligini tekshiradi"""
    try:
        bot_member = await message.bot.get_chat_member(
            chat_id=message.chat.id, 
            user_id=message.bot.id
        )
        return bot_member.status in [
            ChatMemberStatus.ADMINISTRATOR, 
            ChatMemberStatus.CREATOR
        ]
    except Exception:
        return False

# MAGIC FILTER bilan to'g'irlangan handlerlar
@router.message(
    Command("group_info"),
    F.chat.type.in_([ChatType.GROUP, ChatType.SUPERGROUP])
)
async def get_group_info(message: types.Message):
    """Guruh haqida to'liq ma'lumot olish"""
    
    # Ruxsat tekshirish
    if not is_authorized(message.from_user.id):
        await message.reply("❌ Sizda bu buyruqni ishlatish uchun ruxsat yo'q!")
        return
    
    try:
        # Guruh ma'lumotlarini olish
        chat = await message.bot.get_chat(message.chat.id)
        
        # Bot admin ekanligini tekshirish
        bot_admin = await is_bot_admin(message)
        
        # Adminlar ro'yxatini olish
        administrators = await message.bot.get_chat_administrators(message.chat.id)
        
        # Ma'lumotlarni formatlash
        info_text = f"📊 <b>Guruh Ma'lumotlari</b>\n\n"
        info_text += f"🏷 <b>Nom:</b> {chat.title}\n"
        info_text += f"🆔 <b>ID:</b> <code>{chat.id}</code>\n"
        info_text += f"👥 <b>Turi:</b> {chat.type}\n"
        
        if chat.username:
            info_text += f"🔗 <b>Username:</b> @{chat.username}\n"
        
        if chat.description:
            description = chat.description[:100] + '...' if len(chat.description) > 100 else chat.description
            info_text += f"📝 <b>Tavsif:</b> {description}\n"
        
        # A'zolar soni (supergroup uchun)
        if chat.type == ChatType.SUPERGROUP:
            try:
                member_count = await message.bot.get_chat_member_count(chat.id)
                info_text += f"👥 <b>A'zolar soni:</b> {member_count}\n"
            except Exception:
                info_text += f"👥 <b>A'zolar soni:</b> Aniqlab bo'lmadi\n"
        
        info_text += f"\n🤖 <b>Bot admin:</b> {'✅ Ha' if bot_admin else '❌ Yo\'q'}\n"
        
        # Adminlar ro'yxati
        info_text += f"\n👑 <b>Adminlar ro'yxati ({len(administrators)} ta):</b>\n"
        
        # Yaratuvchini birinchi ko'rsatish
        for admin in administrators:
            user = admin.user
            if admin.status == ChatMemberStatus.CREATOR:
                info_text += f"👑 {user.full_name}"
                if user.username:
                    info_text += f" (@{user.username})"
                info_text += f" - <b>Yaratuvchi</b>\n"
                break
        
        # Qolgan adminlar
        for admin in administrators:
            user = admin.user
            if admin.status == ChatMemberStatus.ADMINISTRATOR:
                info_text += f"⭐️ {user.full_name}"
                if user.username:
                    info_text += f" (@{user.username})"
                info_text += f"\n"
        
        # Bot huquqlari (agar admin bo'lsa)
        if bot_admin:
            try:
                bot_member = await message.bot.get_chat_member(message.chat.id, message.bot.id)
                if bot_member.status == ChatMemberStatus.ADMINISTRATOR:
                    info_text += f"\n🔐 <b>Bot huquqlari:</b>\n"
                    perms = bot_member
                    if hasattr(perms, 'can_delete_messages'):
                        info_text += f"🗑 Xabarlarni o'chirish: {'✅' if perms.can_delete_messages else '❌'}\n"
                    if hasattr(perms, 'can_restrict_members'):
                        info_text += f"🚫 A'zolarni cheklash: {'✅' if perms.can_restrict_members else '❌'}\n"
                    if hasattr(perms, 'can_promote_members'):
                        info_text += f"⬆️ Admin tayinlash: {'✅' if perms.can_promote_members else '❌'}\n"
                    if hasattr(perms, 'can_pin_messages'):
                        info_text += f"📌 Xabarni mahkamlash: {'✅' if perms.can_pin_messages else '❌'}\n"
            except Exception:
                pass
        
        await message.reply(info_text, parse_mode='HTML')
        
    except TelegramBadRequest as e:
        await message.reply(f"❌ Xatolik: {e}")
    except Exception as e:
        logging.error(f"Group info error: {e}")
        await message.reply("❌ Ma'lumotlarni olishda xatolik yuz berdi!")

@router.message(
    Command("admin_check"),
    F.chat.type.in_([ChatType.GROUP, ChatType.SUPERGROUP])
)
async def check_admin_status(message: types.Message):
    """Bot admin yoki yo'qligini tekshirish"""
    
    if not is_authorized(message.from_user.id):
        await message.reply("❌ Sizda bu buyruqni ishlatish uchun ruxsat yo'q!")
        return
    
    try:
        bot_member = await message.bot.get_chat_member(message.chat.id, message.bot.id)
        
        status_mapping = {
            ChatMemberStatus.CREATOR: "👑 Bot guruh yaratuvchisi",
            ChatMemberStatus.ADMINISTRATOR: "⭐️ Bot admin", 
            ChatMemberStatus.MEMBER: "👤 Bot oddiy a'zo",
            ChatMemberStatus.RESTRICTED: "🚫 Bot cheklangan",
            ChatMemberStatus.LEFT: "👋 Bot guruhni tark etgan",
            ChatMemberStatus.KICKED: "⛔️ Bot guruhdan chiqarilgan"
        }
        
        status_text = status_mapping.get(bot_member.status, f"❓ Noma'lum holat: {bot_member.status}")
        
        await message.reply(f"🤖 <b>Bot holati:</b>\n{status_text}", parse_mode='HTML')
        
    except Exception as e:
        logging.error(f"Admin check error: {e}")
        await message.reply("❌ Bot holatini tekshirishda xatolik!")

@router.message(
    Command("admins"),
    F.chat.type.in_([ChatType.GROUP, ChatType.SUPERGROUP])
)
async def get_admins_list(message: types.Message):
    """Adminlar ro'yxatini olish"""
    
    if not is_authorized(message.from_user.id):
        await message.reply("❌ Sizda bu buyruqni ishlatish uchun ruxsat yo'q!")
        return
    
    try:
        administrators = await message.bot.get_chat_administrators(message.chat.id)
        
        admin_text = f"👑 <b>Adminlar ro'yxati ({len(administrators)} ta):</b>\n\n"
        
        # Yaratuvchini birinchi ko'rsatish
        for admin in administrators:
            user = admin.user
            if admin.status == ChatMemberStatus.CREATOR:
                admin_text += f"👑 {user.full_name}"
                if user.username:
                    admin_text += f" (@{user.username})"
                admin_text += f" - <b>Yaratuvchi</b>\n"
                break
        
        # Qolgan adminlar
        for admin in administrators:
            user = admin.user
            if admin.status == ChatMemberStatus.ADMINISTRATOR:
                admin_text += f"⭐️ {user.full_name}"
                if user.username:
                    admin_text += f" (@{user.username})"
                admin_text += f" - Admin\n"
        
        await message.reply(admin_text, parse_mode='HTML')
        
    except Exception as e:
        logging.error(f"Admins list error: {e}")
        await message.reply("❌ Adminlar ro'yxatini olishda xatolik!")

@router.message(
    Command("help"),
    F.chat.type.in_([ChatType.GROUP, ChatType.SUPERGROUP])
)
async def show_help(message: types.Message):
    """Yordam xabari"""
    
    if not is_authorized(message.from_user.id):
        await message.reply("❌ Sizda bu buyruqni ishlatish uchun ruxsat yo'q!")
        return
    
    help_text = """
🤖 <b>Guruh Buyruqlari:</b>

📊 /group_info - Guruh haqida to'liq ma'lumot
🔍 /admin_check - Bot admin yoki yo'qligini tekshirish  
👑 /admins - Adminlar ro'yxati
❓ /help - Bu yordam xabari

<i>Eslatma: Bu buyruqlar faqat guruhlarda ishlaydi va ruxsat berilgan foydalanuvchilar uchun.</i>
"""
    
    await message.reply(help_text, parse_mode='HTML')