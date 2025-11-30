import asyncio
import logging
import sys
from datetime import datetime, timedelta

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from .config import settings
from .database import init_db, create_tables, close_db
from .handlers import (
    creation_router,
    join_router,
    lock_router,
    draw_router,
    export_router,
    purge_router,
    button_router,
)
from .handlers.game_purge import auto_purge_expired_games

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('bot.log')
    ]
)

logger = logging.getLogger(__name__)


async def auto_purge_task():
    """
    Background task for auto-purging expired games
    Runs once per day at midnight
    """
    while True:
        try:
            # Calculate time until next midnight
            now = datetime.now()
            tomorrow = now + timedelta(days=1)
            midnight = datetime(tomorrow.year, tomorrow.month, tomorrow.day, 0, 0, 0)
            seconds_until_midnight = (midnight - now).total_seconds()
            
            # Wait until midnight
            logger.info(f"Auto-purge scheduled in {seconds_until_midnight/3600:.1f} hours")
            await asyncio.sleep(seconds_until_midnight)
            
            # Run auto-purge
            logger.info("Running scheduled auto-purge...")
            purged_count = await auto_purge_expired_games()
            logger.info(f"Auto-purge completed: {purged_count} games removed")
            
        except Exception as e:
            logger.error(f"Error in auto-purge task: {e}", exc_info=True)
            # Wait 1 hour before retrying
            await asyncio.sleep(3600)


async def on_startup(bot):
    """
    Actions to perform on bot startup
    """
    logger.info("Starting Secret Santa Bot...")
    
    # Initialize database
    init_db(settings.database_url, echo=settings.debug)
    
    # Create tables if they don't exist
    await create_tables()
    
    # Get bot info
    bot_info = await bot.get_me()
    logger.info(f"Bot started: @{bot_info.username}")
    logger.info(f"Bot ID: {bot_info.id}")
    
    # Check initial auto-purge
    logger.info("Checking for expired games on startup...")
    purged_count = await auto_purge_expired_games()
    if purged_count > 0:
        logger.info(f"Startup auto-purge: {purged_count} games removed")


async def on_shutdown(bot):
    """
    Actions to perform on bot shutdown
    """
    logger.info("Shutting down Secret Santa Bot...")
    
    # Close database connection
    await close_db()
    
    logger.info("Bot stopped successfully")


async def main():
    """
    Main function to run the bot
    """
    # Create bot instance
    bot = Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    
    # Create dispatcher with FSM storage
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)
    
    # Register routers
    # Button router should be first to handle button presses before commands
    dp.include_router(button_router)
    dp.include_router(creation_router)
    dp.include_router(join_router)
    dp.include_router(lock_router)
    dp.include_router(draw_router)
    dp.include_router(export_router)
    dp.include_router(purge_router)
    
    # Register startup and shutdown handlers
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)
    
    # Start auto-purge background task
    if settings.enable_auto_purge:
        logger.info("Auto-purge task enabled")
        asyncio.create_task(auto_purge_task())
    else:
        logger.info("Auto-purge task disabled")
    
    try:
        # Start polling
        logger.info("Starting polling...")
        await dp.start_polling(
            bot,
            allowed_updates=dp.resolve_used_update_types()
        )
    except Exception as e:
        logger.error(f"Critical error: {e}", exc_info=True)
    finally:
        await bot.session.close()


def run():
    """
    Entry point function to run the bot
    """
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    run()