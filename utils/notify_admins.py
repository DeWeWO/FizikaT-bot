import logging
from aiogram import Bot
from data.config import ADMINS, CREATOR_ID
from keyboards.reply.buttons import for_admin


async def on_startup_notify(bot: Bot):
    # Creator ga xabar yuborish
    if CREATOR_ID is not None:
        try:
            bot_properties = await bot.me()
            message = ["👑 <b>Bot ishga tushdi (Creator)</b>\n",
                       f"<b>Bot ID:</b> {bot_properties.id}",
                       f"<b>Bot Username:</b> {bot_properties.username}"]
            await bot.send_message(int(CREATOR_ID), "\n".join(message), reply_markup=for_admin())
        except Exception as err:
            logging.exception(err)
    
    # Adminlarga xabar yuborish
    for admin in ADMINS:
        # Creator ni takrorlamaslik uchun
        if CREATOR_ID is not None and int(admin) == int(CREATOR_ID):
            continue
        try:
            bot_properties = await bot.me()
            message = ["<b>Bot ishga tushdi.</b>\n",
                       f"<b>Bot ID:</b> {bot_properties.id}",
                       f"<b>Bot Username:</b> {bot_properties.username}"]
            await bot.send_message(int(admin), "\n".join(message), reply_markup=for_admin())
        except Exception as err:
            logging.exception(err)
