from typing import Union, List
from aiogram.enums import ChatType
from aiogram.filters import BaseFilter
from aiogram.types import Message

class ChatGroupFilter(BaseFilter):
    def __init__(self, chat_types: Union[str, List[str], None] = None):
        if chat_types is None:
            self.chat_types = [ChatType.GROUP, ChatType.SUPERGROUP]
        elif isinstance(chat_types, str):
            self.chat_types = [chat_types]
        else:
            self.chat_types = chat_types
    
    async def __call__(self, message: Message) -> bool:
        return message.chat.type in self.chat_types