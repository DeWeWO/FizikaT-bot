from aiogram import Router, types, F
from aiogram.filters import CommandStart
from aiogram.enums import ChatType

router = Router()

@router.message(CommandStart(), F.chat.type.in_([ChatType.GROUP, ChatType.SUPERGROUP]))
async def group_start(message: types.Message):
    await message.reply("👋 Salom, guruh a'zolari!")
