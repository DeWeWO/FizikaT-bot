from aiogram import types, F, Router
from aiogram.enums import ChatType, ChatMemberStatus
from keyboards.inline.buttons import add_group
from loader import db, bot

admin_router = Router()

@admin_router.message(F.text == "👥 Guruhga qo'shish", F.chat.type.in_([ChatType.PRIVATE]))
async def start_register(message: types.Message):
    text = "Guruhga qo'shish uchun pastdagi tugmani bosib guruh tanlang!"
    await message.answer(text=text, reply_markup=add_group)
    
@admin_router.my_chat_member()
async def bot_added_to_group(event: types.ChatMemberUpdated):
    if event.chat.type not in [ChatType.GROUP, ChatType.SUPERGROUP]:
        return
    
    if event.new_chat_member.user.id != (await bot.get_me()).id:
        return
    
    if (event.old_chat_member.status in [ChatMemberStatus.LEFT, ChatMemberStatus.KICKED] and 
        event.new_chat_member.status in [ChatMemberStatus.MEMBER, ChatMemberStatus.ADMINISTRATOR]):
        
        title = event.chat.title
        group_id = event.chat.id
        
        # Bazadan adminlar ro‘yxatini olish
        admin_ids = await get_all_admin_ids()
        
        accept_text = f"🎉 Bot yangi guruhga qo'shildi!\n\n📋 Guruh: {title}\n🆔 ID: {group_id}"
        error_text = f"❗️❗️ Botni guruhga qo'shishda xatolik bo‘ldi.\nQaytadan urinib ko‘ring"
        
        try:
            # Har bir admin foydalanuvchiga xabar yuborish
            for admin_id in admin_ids:
                try:
                    await bot.send_message(chat_id=admin_id, text=accept_text)
                except Exception as e:
                    print(f"Admin {admin_id} ga xabar yuborilmadi: {e}")
            
            # Guruhni bazaga qo‘shish
            await db.add_group(group_id, title)
        except Exception as e:
            print(f"Xatolik: {e}")
            if admin_ids:
                await bot.send_message(chat_id=admin_ids[0], text=error_text)


async def get_all_admin_ids() -> list:
    """Bazadagi barcha admin telegram_id larini olish"""
    admin_ids = []
    try:
        custom_users = await db.select_all_custom_users()
        if isinstance(custom_users, list):
            for user in custom_users:
                if user.get("telegram_id"):
                    admin_ids.append(user.get("telegram_id"))
        elif isinstance(custom_users, dict):
            for user in custom_users.get("results", []):
                if user.get("telegram_id"):
                    admin_ids.append(user.get("telegram_id"))
    except Exception as e:
        print(f"Admin list error: {e}")
    return admin_ids
