import logging
import asyncio
from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from loader import db, bot
from keyboards.inline.buttons import are_you_sure_markup
from states.test import AdminState
from filters.admin import IsBotAdminFilter
from data.config import ADMINS
from utils.pgtoexcel import export_to_excel
from aiogram.enums import ChatType


router = Router()


# @router.message(Command('allusers'), IsBotAdminFilter(ADMINS))
# async def get_all_users(message: types.Message):
#     users = await db.select_all_custom_users()

#     file_path = f"data/users_list.xlsx"
#     await export_to_excel(data=users, headings=['ID', 'USERNAME', 'Telegram username'], filepath=file_path)

#     await message.answer_document(types.input_file.FSInputFile(file_path))


@router.message(Command('cleandb'), IsBotAdminFilter(ADMINS), F.chat.type.in_([ChatType.PRIVATE]))
async def ask_are_you_sure(message: types.Message, state: FSMContext):
    msg = await message.reply("Haqiqatdan ham bazani tozalab yubormoqchimisiz?", reply_markup=are_you_sure_markup)
    await state.update_data(msg_id=msg.message_id)
    await state.set_state(AdminState.are_you_sure)


@router.callback_query(AdminState.are_you_sure, IsBotAdminFilter(ADMINS))
async def clean_db(call: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    msg_id = data.get('msg_id')
    if call.data == 'yes':
        await db.delete_users()
        text = "Baza tozalandi!"
    elif call.data == 'no':
        text = "Bekor qilindi."
    await bot.edit_message_text(text=text, chat_id=call.message.chat.id, message_id=msg_id)
    await state.clear()

@router.message(Command('admin_reklama'), IsBotAdminFilter(ADMINS), F.chat.type.in_([ChatType.PRIVATE]))
async def ask_admin_ad_content(message: types.Message, state: FSMContext):
    """CustomUser jadvalidagi admin foydalanuvchilarga reklama yuborish"""
    await message.answer(
        "📢 ADMIN FOYDALANUVCHILARGA REKLAMA\n\n"
        "Admin panel foydalanuvchilariga yuborish uchun post yuboring:\n"
        "📝 Matn, rasm, video, audio - barcha formatlar qo'llab-quvvatlanadi\n\n"
        "❌ Bekor qilish uchun /cancel"
    )
    await state.set_state(AdminState.ask_admin_ad_content)

@router.message(AdminState.ask_admin_ad_content, IsBotAdminFilter(ADMINS))
async def send_ad_to_custom_users(message: types.Message, state: FSMContext):
    """CustomUser jadvalidagi barcha foydalanuvchilarga reklama yuborish"""
    
    # Reklama yuborishni boshlash xabari
    process_message = await message.answer("📤 CustomUser foydalanuvchilariga reklama yuborish boshlandi...")
    
    # CustomUser foydalanuvchilarni olish
    custom_users = await db.select_all_custom_users()
    
    if not custom_users:
        await process_message.edit_text("❌ CustomUser jadvalida hech qanday foydalanuvchi topilmadi!")
        await state.clear()
        return
    
    total_users = len(custom_users)
    success_count = 0
    failed_count = 0
    
    await process_message.edit_text(f"📊 Jami {total_users} ta CustomUser foydalanuvchiga yuborish boshlandi...")
    
    for user in custom_users:
        # user dict dan telegram_id ni olish
        telegram_id = user.get('telegram_id')
        username = user.get('username', 'N/A')
        
        if not telegram_id:
            failed_count += 1
            logging.warning(f"CustomUser {username} da telegram_id mavjud emas")
            continue
            
        try:
            await message.send_copy(chat_id=telegram_id)
            success_count += 1
            
            # Rate limiting uchun kutish
            await asyncio.sleep(0.05)
            
            # Har 50 ta yuborilganda progress ko'rsatish
            if success_count % 50 == 0:
                await process_message.edit_text(
                    f"📤 Yuborilmoqda...\n"
                    f"✅ Yuborildi: {success_count}\n"
                    f"❌ Xatolik: {failed_count}\n"
                    f"📊 Jami: {total_users}"
                )
                
        except Exception as error:
            failed_count += 1
            logging.info(f"CustomUser reklama yuborilmadi: {telegram_id} ({username}). Xatolik: {error}")
    
    # Yakuniy natija
    await process_message.edit_text(
        f"📢 CUSTOMUSER REKLAMA YUBORISH YAKUNLANDI\n\n"
        f"📊 Statistika:\n"
        f"✅ Muvaffaqiyatli yuborildi: {success_count}\n"
        f"❌ Yuborilmadi: {failed_count}\n"
        f"📈 Jami foydalanuvchilar: {total_users}\n"
        f"📍 Muvaffaqiyat foizi: {round((success_count/total_users)*100, 2)}%"
    )
    await state.clear()

@router.message(Command('telegram_reklama'), IsBotAdminFilter(ADMINS), F.chat.type.in_([ChatType.PRIVATE]))
async def ask_register_ad_content(message: types.Message, state: FSMContext):
    """Register jadvalidagi foydalanuvchilarga reklama yuborish"""
    await message.answer(
        "📢 REGISTER FOYDALANUVCHILARGA REKLAMA\n\n"
        "Register ro'yxatidagi foydalanuvchilarga yuborish uchun post yuboring:\n"
        "📝 Matn, rasm, video, audio - barcha formatlar qo'llab-quvvatlanadi\n\n"
        "❌ Bekor qilish uchun /cancel"
    )
    await state.set_state(AdminState.ask_register_ad_content)

@router.message(AdminState.ask_register_ad_content, IsBotAdminFilter(ADMINS))
async def send_ad_to_register_users(message: types.Message, state: FSMContext):
    """Register jadvalidagi barcha foydalanuvchilarga reklama yuborish"""
    
    # Reklama yuborishni boshlash xabari
    process_message = await message.answer("📤 Register foydalanuvchilariga reklama yuborish boshlandi...")
    
    # Register foydalanuvchilarni olish
    register_users = await db.select_all_register_users()
    
    if not register_users:
        await process_message.edit_text("❌ Register jadvalida hech qanday foydalanuvchi topilmadi!")
        await state.clear()
        return
    
    total_users = len(register_users)
    success_count = 0
    failed_count = 0
    
    await process_message.edit_text(f"📊 Jami {total_users} ta Register foydalanuvchiga yuborish boshlandi...")
    
    for user in register_users:
        # Register modeliga mos - telegram_id ni olish
        telegram_id = user.get('telegram_id')
        fio = user.get('fio', 'N/A')
        
        if not telegram_id:
            failed_count += 1
            logging.warning(f"Register user {fio} da telegram_id mavjud emas")
            continue
            
        try:
            await message.send_copy(chat_id=telegram_id)
            success_count += 1
            
            # Rate limiting uchun kutish
            await asyncio.sleep(0.05)
            
            # Har 50 ta yuborilganda progress ko'rsatish
            if success_count % 50 == 0:
                await process_message.edit_text(
                    f"📤 Yuborilmoqda...\n"
                    f"✅ Yuborildi: {success_count}\n"
                    f"❌ Xatolik: {failed_count}\n"
                    f"📊 Jami: {total_users}"
                )
                
        except Exception as error:
            failed_count += 1
            logging.info(f"Register reklama yuborilmadi: {telegram_id} ({fio}). Xatolik: {error}")
    
    # Yakuniy natija
    await process_message.edit_text(
        f"📢 REGISTER REKLAMA YUBORISH YAKUNLANDI\n\n"
        f"📊 Statistika:\n"
        f"✅ Muvaffaqiyatli yuborildi: {success_count}\n"
        f"❌ Yuborilmadi: {failed_count}\n"
        f"📈 Jami Register foydalanuvchilar: {total_users}\n"
        f"📍 Muvaffaqiyat foizi: {round((success_count/total_users)*100, 2)}%"
    )
    await state.clear()
