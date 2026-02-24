from aiogram.filters import BaseFilter
from aiogram.types import Message, CallbackQuery
from data.config import CREATOR_ID


class IsBotAdminFilter(BaseFilter):
    def __init__(self, user_ids: list):
        self.user_ids = user_ids

    async def __call__(self, obj: Message | CallbackQuery) -> bool:
        # Creator tekshiruvi - har qanday holatda creator o'tadi
        if CREATOR_ID is not None:
            user_id = obj.from_user.id if isinstance(obj, Message) else obj.from_user.id
            if int(user_id) == int(CREATOR_ID):
                return True
        
        # Admin tekshiruvi
        user_id = obj.from_user.id if isinstance(obj, Message) else obj.from_user.id
        admin_ids_int = [int(id) for id in self.user_ids]
        return int(user_id) in admin_ids_int
