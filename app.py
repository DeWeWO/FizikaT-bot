import asyncio
import logging
import signal
import sys

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

# Global o'zgaruvchilar
bot: Bot = None
dispatcher: Dispatcher = None


def setup_handlers(dispatcher: Dispatcher) -> None:
    """HANDLERS"""
    from handlers import setup_routers
    dispatcher.include_router(setup_routers())


def setup_middlewares(dispatcher: Dispatcher, bot: Bot) -> None:
    """MIDDLEWARE"""
    try:
        from middlewares.throttling import ThrottlingMiddleware
        dispatcher.message.middleware(ThrottlingMiddleware(slow_mode_delay=0.5))
    except ImportError:
        pass


def setup_filters(dispatcher: Dispatcher) -> None:
    """FILTERS - Magic Filter ishlatiladi, custom filterlar emas"""
    # Magic Filter (F) ishlatiladi, alohida filter setup kerak emas
    # Filterlar to'g'ridan-to'g'ri handler fayllarida qo'llanadi
    pass


async def setup_aiogram(dispatcher: Dispatcher, bot: Bot) -> None:
    """Aiogram konfiguratsiyasi"""
    setup_handlers(dispatcher=dispatcher)
    setup_middlewares(dispatcher=dispatcher, bot=bot)
    setup_filters(dispatcher=dispatcher)


async def database_connected():
    """Database connection tekshiruvi"""
    try:
        from utils.db.postgres import api_client
        await api_client.health_check()
    except:
        pass


async def setup_bot_commands(bot: Bot) -> None:
    """Bot komandalarini o'rnatish"""
    try:
        from utils.set_bot_commands import set_default_commands
        await set_default_commands(bot=bot)
    except ImportError:
        pass


async def notify_admins_startup(bot: Bot) -> None:
    """Adminlarga bot ishga tushgani haqida xabar"""
    try:
        from utils.notify_admins import on_startup_notify
        await on_startup_notify(bot=bot)
    except ImportError:
        pass


async def aiogram_on_startup_polling(dispatcher: Dispatcher, bot: Bot) -> None:
    """Bot ishga tushganda bajariluvchi funksiyalar"""
    print("🚀 Bot ishga tushmoqda...")
    
    await database_connected()
    await bot.delete_webhook(drop_pending_updates=True)
    await setup_aiogram(bot=bot, dispatcher=dispatcher)
    await setup_bot_commands(bot)
    await notify_admins_startup(bot)
    
    print("✅ Bot ishga tushdi!")


async def aiogram_on_shutdown_polling(dispatcher: Dispatcher, bot: Bot):
    """Bot to'xtaganda bajariluvchi funksiyalar"""
    print("🛑 Bot to'xtatilmoqda...")
    
    try:
        from utils.db.postgres import api_client
        await api_client.close()
    except:
        pass
    
    # Session yopish - aiogram 3.x uchun to'g'ri usul
    try:
        if hasattr(bot, 'session') and bot.session:
            # aiogram 3.x da session.closed yo'q, shuning uchun to'g'ridan-to'g'ri yopamiz
            await bot.session.close()
    except Exception as e:
        print(f"Session yopishda xatolik: {e}")
    
    # Storage yopish
    try:
        if hasattr(dispatcher, 'storage') and dispatcher.storage:
            await dispatcher.storage.close()
    except Exception as e:
        print(f"Storage yopishda xatolik: {e}")
    
    print("✅ Bot to'xtatildi")


def setup_logging():
    """Minimal logging sozlamalari"""
    logging.basicConfig(
        level=logging.WARNING,
        format='%(levelname)s - %(message)s',
        handlers=[logging.StreamHandler(sys.stdout)]
    )
    
    # Barcha loglarni minimal darajaga tushirish
    logging.getLogger('aiohttp').setLevel(logging.ERROR)
    logging.getLogger('aiogram').setLevel(logging.ERROR)
    logging.getLogger().setLevel(logging.ERROR)


async def main():
    """Asosiy funksiya"""
    setup_logging()
    
    bot = None
    dispatcher = None
    
    def signal_handler(signum, frame):
        """Signal handler"""
        print(f"\n🛑 Signal {signum} qabul qilindi. Bot to'xtatilmoqda...")
        raise KeyboardInterrupt()
    
    # Signal handlerlarni o'rnatish
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        # Konfiguratsiya yuklash
        from data.config import BOT_TOKEN
        
        # Bot va dispatcher yaratish
        bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
        storage = MemoryStorage()
        dispatcher = Dispatcher(storage=storage)
        
        # Startup/shutdown eventlar
        dispatcher.startup.register(aiogram_on_startup_polling)
        dispatcher.shutdown.register(aiogram_on_shutdown_polling)
        
        # Polling boshlatish - aiogram 3.x uchun optimallashtirilgan
        await dispatcher.start_polling(
            bot,
            close_bot_session=False,  # Biz o'zimiz yopamiz
            allowed_updates=['message', 'callback_query', 'inline_query'],
            handle_signals=False  # Signal handlingni o'zimiz qilamiz
        )
        
    except KeyboardInterrupt:
        print("🛑 Keyboard Interrupt - Bot to'xtatildi")
    except Exception as e:
        print(f"❌ Xatolik: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # To'g'ri cleanup - aiogram 3.x uchun
        if bot and hasattr(bot, 'session') and bot.session:
            try:
                await bot.session.close()
            except Exception as e:
                print(f"Session yopishda xatolik: {e}")
        
        if dispatcher and hasattr(dispatcher, 'storage') and dispatcher.storage:
            try:
                await dispatcher.storage.close()
            except Exception as e:
                print(f"Storage yopishda xatolik: {e}")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Bot to'xtatildi!")
    except Exception as e:
        print(f"Dastur xatolik bilan tugadi: {e}")
        sys.exit(1)