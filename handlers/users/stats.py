from aiogram import types, F, Router
from utils.db.postgres import api_client

router = Router()

@router.message(F.text == "📊 Statistika")
async def handle_stats(message: types.Message):
    telegram_id = message.from_user.id
    
    # Foydalanuvchi statistikasini olish
    stats = await api_client.get_user_stats(telegram_id)
    
    if not stats:
        await message.answer("❌ Statistika ma'lumotlari topilmadi.")
        return
    
    if 'message' in stats:
        await message.answer("📊 Siz hali hech qanday test ishlamagansiz.")
        return
    
    total_tests = stats.get('total_tests', 0)
    avg_percentage = stats.get('average_percentage', 0)
    
    text = f"""
📊 <b>Sizning statistikangiz:</b>

🎯 Jami testlar: <b>{total_tests}</b>
📈 O'rtacha natija: <b>{avg_percentage}%</b>

📋 <b>Test natijalari:</b>
"""
    
    # Har bir test natijasini ko'rsatish
    results = stats.get('results', [])
    for i, result in enumerate(results[:10], 1):  # Faqat oxirgi 10 ta
        category_title = result.get('category_title', 'Noma\'lum')
        correct = result.get('correct_answers', 0)
        total = result.get('total_questions', 0)
        percentage = result.get('percentage', 0)
        date = result.get('completed_at', '')[:10]  # Faqat sana
        
        text += f"{i}. <b>{category_title}</b>\n"
        text += f"   ✅ {correct}/{total} ({percentage}%) - {date}\n\n"
    
    if len(results) > 10:
        text += f"... va yana {len(results) - 10} ta natija"
    
    await message.answer(text, parse_mode="HTML")

@router.message(F.text == "🏆 Mening natijalarim")
async def handle_my_results(message: types.Message):
    telegram_id = message.from_user.id
    
    # Foydalanuvchining barcha natijalarini olish
    results = await api_client.get_user_test_results(telegram_id)
    
    if not results:
        await message.answer("📊 Siz hali hech qanday test ishlamagansiz.")
        return
    
    text = "🏆 <b>Barcha natijalaringiz:</b>\n\n"
    
    for i, result in enumerate(results, 1):
        category_title = result.get('category_title', 'Noma\'lum')
        correct = result.get('correct_answers', 0)
        total = result.get('total_questions', 0)
        percentage = result.get('percentage', 0)
        date = result.get('completed_at', '')[:16].replace('T', ' ')  # Sana va vaqt
        
        # Emoji natijaga qarab
        if percentage >= 80:
            emoji = "🏆"
        elif percentage >= 60:
            emoji = "🥈"
        elif percentage >= 40:
            emoji = "🥉"
        else:
            emoji = "📝"
        
        text += f"{emoji} <b>{category_title}</b>\n"
        text += f"   ✅ {correct}/{total} savolga javob ({percentage}%)\n"
        text += f"   📅 {date}\n\n"
    
    await message.answer(text, parse_mode="HTML")