from .private_chat import ChatPrivateFilter
from .admin import IsBotAdminFilter
from .group_chat import ChatGroupFilter
from aiogram import F
from aiogram.enums import ChatType

ChatPrivateFilter = lambda: F.chat.type == ChatType.PRIVATE
ChatGroupFilter = lambda: F.chat.type.in_([ChatType.GROUP, ChatType.SUPERGROUP])
