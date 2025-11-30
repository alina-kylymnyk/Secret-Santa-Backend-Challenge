import logging

from aiogram import Router, types
from aiogram.filters import Command

from src.database import get_session, GameRepository
from services.draw_service import DrawService

logger = logging.getLogger(__name__)

router = Router(name="game_lock")


@router.message(Command("lock"))
async def cmd_lock(message):
    """
    Handle /lock command to lock a game and prevent new participants

    """
    user_id = message.from_user.id
    username = message.from_user.username or message.from_user.first_name
    
    # Parse command
    parts = message.text.split(maxsplit=1)
    
    if len(parts) < 2:
        error_text = (
            "❌ <b>Неправильний формат команди</b>\n\n"
            "Використовуйте: <code>/lock КОД_ГРИ</code>\n\n"
            "<b>Приклад:</b>\n"
            "<code>/lock SANTA42</code>"
        )
        await message.answer(error_text, parse_mode="HTML")
        return
    
    game_code = parts[1].upper()
    
    logger.info(f"User {username} (ID: {user_id}) attempting to lock game {game_code}")
    
    try:
        async with get_session() as session:
            repository = GameRepository(session)
            
            # Check if game exists
            game = await repository.get_game_by_code(game_code)
            
            if not game:
                error_text = (
                    f"❌ <b>Гра не знайдена</b>\n\n"
                    f"Гра з кодом <code>{game_code}</code> не існує."
                )
                await message.answer(error_text, parse_mode="HTML")
                return
            
            # Check if user is the creator
            if game.creator_chat_id != user_id:
                error_text = (
                    "🚫 <b>Доступ заборонено</b>\n\n"
                    "Тільки організатор гри може заблокувати набір учасників.\n\n"
                    "Якщо ви організатор, переконайтеся що використовуєте "
                    "той самий обліковий запис, з якого створили гру."
                )
                await message.answer(error_text, parse_mode="HTML")
                return
            
            # Check if already locked
            if game.is_locked:
                error_text = (
                    f"🔒 <b>Гра вже заблокована</b>\n\n"
                    f"Гра <code>{game_code}</code> вже закрила набір учасників.\n\n"
                    "Наступний крок - провести жеребкування:\n"
                    f"<code>/draw {game_code}</code>"
                )
                await message.answer(error_text, parse_mode="HTML")
                return
            
            # Get participants and check minimum count
            participants = await repository.get_participants(game.id)
            participant_count = len(participants)
            
            if participant_count < DrawService.MIN_PARTICIPANTS:
                error_text = (
                    f"⚠️ <b>Недостатньо учасників</b>\n\n"
                    f"Поточна кількість: <b>{participant_count}</b>\n"
                    f"Мінімум потрібно: <b>{DrawService.MIN_PARTICIPANTS}</b>\n\n"
                    f"Ще потрібно: <b>{DrawService.MIN_PARTICIPANTS - participant_count}</b> "
                    f"{'учасник' if DrawService.MIN_PARTICIPANTS - participant_count == 1 else 'учасники'}\n\n"
                    "Запросіть більше друзів приєднатися:\n"
                    f"<code>/join {game_code} Ім'я</code>"
                )
                await message.answer(error_text, parse_mode="HTML")
                return
            
            # Lock the game
            await repository.lock_game(game.id)
            
            logger.info(
                f"Game {game_code} locked by user {username}. "
                f"Participants: {participant_count}"
            )
            
            # Prepare participant list
            participant_list = "\n".join(
                f"{i}. {p.name}" 
                for i, p in enumerate(participants, 1)
            )
            
            # Send success message
            response_text = (
                f"🔒 <b>Гра {game_code} заблокована!</b>\n\n"
                f"👥 Учасників: <b>{participant_count}</b>\n\n"
                "📋 <b>Список учасників:</b>\n"
                f"{participant_list}\n\n"
                "✅ Новi учасники більше не можуть приєднатися.\n\n"
                "🎲 <b>Наступний крок - жеребкування:</b>\n"
                f"<code>/draw {game_code}</code>\n\n"
                "⚠️ Після жеребкування результати неможливо змінити!"
            )
            
            await message.answer(response_text, parse_mode="HTML")
    
    except Exception as e:
        logger.error(f"Error locking game {game_code}: {e}", exc_info=True)
        
        error_text = (
            "❌ <b>Помилка блокування гри</b>\n\n"
            "Щось пішло не так. Спробуйте ще раз."
        )
        
        await message.answer(error_text, parse_mode="HTML")


@router.message(Command("unlock"))
async def cmd_unlock(message):
    """
    Handle /unlock command to unlock a game (allow new participants again)
    """
    user_id = message.from_user.id
    username = message.from_user.username or message.from_user.first_name
    
    # Parse command
    parts = message.text.split(maxsplit=1)
    
    if len(parts) < 2:
        error_text = (
            "❌ <b>Неправильний формат команди</b>\n\n"
            "Використовуйте: <code>/unlock КОД_ГРИ</code>\n\n"
            "<b>Приклад:</b>\n"
            "<code>/unlock SANTA42</code>"
        )
        await message.answer(error_text, parse_mode="HTML")
        return
    
    game_code = parts[1].upper()
    
    logger.info(f"User {username} (ID: {user_id}) attempting to unlock game {game_code}")
    
    try:
        async with get_session() as session:
            repository = GameRepository(session)
            
            # Check if game exists
            game = await repository.get_game_by_code(game_code)
            
            if not game:
                error_text = (
                    f"❌ <b>Гра не знайдена</b>\n\n"
                    f"Гра з кодом <code>{game_code}</code> не існує."
                )
                await message.answer(error_text, parse_mode="HTML")
                return
            
            # Check if user is the creator
            if game.creator_chat_id != user_id:
                error_text = (
                    "🚫 <b>Доступ заборонено</b>\n\n"
                    "Тільки організатор гри може розблокувати гру."
                )
                await message.answer(error_text, parse_mode="HTML")
                return
            
            # Check if draw has been performed
            if game.is_drawn:
                error_text = (
                    "❌ <b>Неможливо розблокувати</b>\n\n"
                    "Жеребкування вже проведено. Змінити склад учасників неможливо.\n\n"
                    "Створіть нову гру якщо потрібно почати заново."
                )
                await message.answer(error_text, parse_mode="HTML")
                return
            
            # Check if already unlocked
            if not game.is_locked:
                error_text = (
                    f"🔓 <b>Гра вже розблокована</b>\n\n"
                    f"Гра <code>{game_code}</code> і так відкрита для нових учасників."
                )
                await message.answer(error_text, parse_mode="HTML")
                return
            
            # Unlock the game
            from sqlalchemy import update
            from ..database.models import Game
            
            stmt = update(Game).where(Game.id == game.id).values(is_locked=False)
            await session.execute(stmt)
            await session.commit()
            
            logger.info(f"Game {game_code} unlocked by user {username}")
            
            response_text = (
                f"🔓 <b>Гра {game_code} розблокована!</b>\n\n"
                "✅ Нові учасники знову можуть приєднатися:\n"
                f"<code>/join {game_code} Ім'я</code>\n\n"
                "Коли всі приєдналися, заблокуйте гру знову:\n"
                f"<code>/lock {game_code}</code>"
            )
            
            await message.answer(response_text, parse_mode="HTML")
    
    except Exception as e:
        logger.error(f"Error unlocking game {game_code}: {e}", exc_info=True)
        error_text = "❌ Помилка розблокування гри."
        await message.answer(error_text, parse_mode="HTML")