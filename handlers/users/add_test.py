from aiogram import Router, F, types
from aiogram.types import Message, ReplyKeyboardRemove
from aiogram.fsm.context import FSMContext
from states.createTest import TestCreation
from loader import db

router = Router()

@router.message(F.text == "📝 Test tuzish")
async def start_register(message: types.Message, state: FSMContext):
    await message.answer("Savol matnini yuboring:", reply_markup=ReplyKeyboardRemove())
    await state.set_state(state=TestCreation.questionText)

@router.message(TestCreation.questionText, F.text)
async def get_question_text(message: Message, state: FSMContext):
    await state.update_data(question_text=message.text)
    await message.answer("Agar rasm bo‘lsa, yuboring. Bo‘lmasa 'yoq' deb yozing.")
    await state.set_state(state=TestCreation.questionImage)

@router.message(TestCreation.questionImage, F.text)
async def get_question_image(message: Message, state: FSMContext):
    if message.text and message.text.lower() == "yoq":
        await state.update_data(image_file_id=None)
    elif message.photo:
        file_id = message.photo[-1].file_id
        await state.update_data(image_file_id=file_id)
    else:
        await message.answer("Rasm yuboring yoki 'yoq' deb yozing.")
        return

    await message.answer("Endi 4 ta variantni yuboring. To‘g‘ri javob oxiriga '*' qo‘ying.")
    await state.set_state(state=TestCreation.questionOptions)

@router.message(TestCreation.questionOptions, F.text)
async def get_question_options(message: Message, state: FSMContext):
    lines = [l.strip() for l in message.text.strip().split("\n") if l]
    if len(lines) != 4:
        await message.answer("Aynan 4 ta variant yuboring.")
        return

    options = []
    correct_index = None

    for i, line in enumerate(lines):
        if line.endswith("*"):
            correct_index = i
            options.append(line.rstrip("*").strip())
        else:
            options.append(line.strip())

    if correct_index is None:
        await message.answer("To‘g‘ri javob belgilanmagan. Bittasini '*' bilan belgilang.")
        return

    data = await state.get_data()
    await db.add_question(
        text=data["question_text"],
        image_id=data["image_file_id"],
        options=options,
        correct_index=correct_index
    )

    await message.answer("✅ Savol muvaffaqiyatli saqlandi.")
    await state.clear()
