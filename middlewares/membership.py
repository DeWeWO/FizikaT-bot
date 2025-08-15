from typing import Callable, Dict, Any, Awaitable, Set
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message, CallbackQuery
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError
from aiogram.types import ReplyKeyboardRemove
import logging
from utils.db.postgres import api_client

logger = logging.getLogger(__name__)

class AdminGroupMiddleware(BaseMiddleware):
    def __init__(self):
        pass

    async def __call__(self, handler: Callable, event: TelegramObject, data: Dict[str, Any]) -> Any:
        if not isinstance(event, (Message, CallbackQuery)):
            return await handler(event, data)
        
        user_id = event.from_user.id
        chat_id = event.chat.id if isinstance(event, Message) else event.message.chat.id

        # Real-time admin tekshiruvi
        if await self._is_admin(user_id):
            return await handler(event, data)
        
        # Real-time guruh tekshiruvi
        group_ids = await self._get_group_ids()
        if chat_id in group_ids:
            return await handler(event, data)
        
        # Private chat - guruh a'zoligini tekshirish
        if chat_id == user_id:
            if await self._check_membership(user_id, group_ids, data['bot']):
                return await handler(event, data)
            else:
                await self._send_denied(event, data['bot'])
                return

        return await handler(event, data)

    async def _is_admin(self, user_id: int) -> bool:
        """Real-time admin tekshiruvi"""
        try:
            result = await api_client.request("GET", "custom-users/")
            if result and 'results' in result:
                return user_id in {
                    user['telegram_id'] for user in result['results']
                    if user.get('is_staff') and user.get('telegram_id') and user.get('is_active')
                }
        except Exception as e:
            logger.error(f"Admin tekshirishda xato: {e}")
        return False

    async def _get_group_ids(self) -> Set[int]:
        """Real-time guruh ID lari olish"""
        try:
            result = await api_client.request("GET", "telegram-groups/all-ids/")
            if result and 'group_ids' in result:
                return set(result['group_ids'])
        except Exception as e:
            logger.error(f"Guruh ID lari olishda xato: {e}")
        return set()

    async def _check_membership(self, user_id: int, group_ids: Set[int], bot) -> bool:
        for group_id in group_ids:
            try:
                member = await bot.get_chat_member(group_id, user_id)
                if member.status in {'member', 'administrator', 'creator'}:
                    return True
            except (TelegramBadRequest, TelegramForbiddenError):
                continue
        return False

    async def _send_denied(self, event, bot):
        try:
            if isinstance(event, Message):
                await bot.send_message(
                    event.chat.id,
                    "❌ Kechirasiz!\n\n"
                    "Siz bilan muloqot qilish menga taqiqlangan!",
                    reply_markup=ReplyKeyboardRemove()
                )
            elif isinstance(event, CallbackQuery):
                await bot.answer_callback_query(
                    event.id,
                    "❌ Siz bilan muloqot qilish menga taqiqlangan!",
                    show_alert=True, reply_markup=ReplyKeyboardRemove()
                )
        except Exception as e:
            logger.error(f"Xabar yuborishda xato: {e}")


def setup_middleware(dp):
    middleware = AdminGroupMiddleware()
    dp.message.middleware(middleware)
    dp.callback_query.middleware(middleware)