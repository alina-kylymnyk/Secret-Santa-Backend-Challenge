
import logging
from datetime import datetime

from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from ..database import get_session, GameRepository

logger = logging.getLogger(__name__)

router = Router(name="game_purge")


@router.message(Command("purge"))
async def cmd_purge(message):
    """
    Handle /purge command to delete a game permanently
    """
    user_id = message.from_user.id
    username = message.from_user.username or message.from_user.first_name
    
    # Parse command
    parts = message.text.split(maxsplit=1)
    
    if len(parts) < 2:
        error_text = (
            "❌ <b>Неправильний формат команди</b>\n\n"
            "Використовуйте: <code>/purge КОД_ГРИ</code>\n\n"
            "<b>Приклад:</b>\n"
            "<code>/purge SANTA42</code>\n\n"
            "⚠️ <b>Увага:</b> Ця дія незворотна!"
        )
        await message.answer(error_text, parse_mode="HTML")
        return
    
    game_code = parts[1].upper()
    
    logger.info(f"User {username} (ID: {user_id}) requesting purge for game {game_code}")
    
    try:
        async with get_session() as session:
            repository = GameRepository(session)
            
            # Check if game exists
            game = await repository.get_game_by_code(game_code)
            
            if not game:
                error_text = (
                    f"❌ <b>Гра не знайдена</b>\n\n"
                    f"Гра з кодом <code>{game_code}</code> не існує або вже видалена."
                )
                await message.answer(error_text, parse_mode="HTML")
                return
            
            # Check if user is the creator
            if game.creator_chat_id != user_id:
                error_text = (
                    "🚫 <b>Доступ заборонено</b>\n\n"
                    "Тільки організатор гри може видалити її."
                )
                await message.answer(error_text, parse_mode="HTML")
                return
            
            # Get game stats
            stats = await repository.get_game_stats(game.id)
            
            # Create confirmation keyboard
            keyboard = InlineKeyboardBuilder()
            keyboard.row(
                InlineKeyboardButton(
                    text="✅ Так, видалити",
                    callback_data=f"purge_confirm:{game_code}"
                ),
                InlineKeyboardButton(
                    text="❌ Скасувати",
                    callback_data=f"purge_cancel:{game_code}"
                )
            )
            
            # Auto-purge date info
            purge_date_text = ""
            if game.auto_purge_at:
                days_until_purge = (game.auto_purge_at - datetime.utcnow()).days
                purge_date_text = (
                    f"📅 Автоматичне видалення: через {days_until_purge} днів\n"
                )
            
            warning_text = (
                f"⚠️ <b>Підтвердження видалення</b>\n\n"
                f"🎮 Гра: <code>{game_code}</code>\n"
                f"👥 Учасників: {stats['participant_count']}\n"
                f"🎁 Результатів: {stats['draw_count']}\n"
                f"{purge_date_text}\n"
                f"<b>Ви впевнені що хочете видалити цю гру?</b>\n\n"
                f"⚠️ Ця дія <b>НЕЗВОРОТНА</b>!\n"
                f"Всі дані будуть видалені:\n"
                f"• Список учасників\n"
                f"• Результати жеребкування\n"
                f"• Налаштування гри\n\n"
                f"Відновити дані буде неможливо."
            )
            
            await message.answer(
                warning_text,
                parse_mode="HTML",
                reply_markup=keyboard.as_markup()
            )
    
    except Exception as e:
        logger.error(f"Error preparing purge for game {game_code}: {e}", exc_info=True)
        
        error_text = (
            "❌ <b>Помилка</b>\n\n"
            "Щось пішло не так. Спробуйте ще раз."
        )
        
        await message.answer(error_text, parse_mode="HTML")


@router.callback_query(F.data.startswith("purge_confirm:"))
async def callback_purge_confirm(callback):
    """
    Handle purge confirmation callback
    """
    game_code = callback.data.split(":")[1]
    user_id = callback.from_user.id
    username = callback.from_user.username or callback.from_user.first_name
    
    try:
        async with get_session() as session:
            repository = GameRepository(session)
            
            game = await repository.get_game_by_code(game_code)
            
            if not game:
                await callback.answer("❌ Гра не знайдена", show_alert=True)
                return
            
            if game.creator_chat_id != user_id:
                await callback.answer("🚫 Доступ заборонено", show_alert=True)
                return
            
            # Delete the game (CASCADE will delete related data)
            deleted = await repository.delete_game(game.id)
            
            if deleted:
                logger.info(
                    f"Game {game_code} purged by user {username} (ID: {user_id})"
                )
                
                # Update message
                await callback.message.edit_text(
                    f"🗑 <b>Гра видалена</b>\n\n"
                    f"Гра <code>{game_code}</code> та всі пов'язані дані видалені назавжди.\n\n"
                    f"✅ Операція виконана успішно.",
                    parse_mode="HTML"
                )
                
                await callback.answer("✅ Гра видалена")
            else:
                await callback.answer("❌ Помилка видалення", show_alert=True)
    
    except Exception as e:
        logger.error(f"Error confirming purge for game {game_code}: {e}", exc_info=True)
        await callback.answer("❌ Помилка видалення", show_alert=True)


@router.callback_query(F.data.startswith("purge_cancel:"))
async def callback_purge_cancel(callback):
    """
    Handle purge cancellation callback
    """
    game_code = callback.data.split(":")[1]
    
    await callback.message.edit_text(
        f"✅ <b>Відмінено</b>\n\n"
        f"Гра <code>{game_code}</code> не була видалена.",
        parse_mode="HTML"
    )
    
    await callback.answer("Видалення скасовано")


async def auto_purge_expired_games():
    """
    Automatically purge games that have passed their auto_purge_at date
    """
    logger.info("Starting auto-purge process...")
    
    try:
        async with get_session() as session:
            repository = GameRepository(session)
            
            # Get expired games
            expired_games = await repository.get_expired_games(datetime.utcnow())
            
            if not expired_games:
                logger.info("No expired games found")
                return 0
            
            logger.info(f"Found {len(expired_games)} expired games")
            
            purged_count = 0
            
            for game in expired_games:
                try:
                    await repository.delete_game(game.id)
                    purged_count += 1
                    logger.info(
                        f"Auto-purged game {game.game_code} "
                        f"(created: {game.created_at}, purge date: {game.auto_purge_at})"
                    )
                except Exception as e:
                    logger.error(
                        f"Error auto-purging game {game.game_code}: {e}",
                        exc_info=True
                    )
            
            logger.info(f"Auto-purge completed: {purged_count}/{len(expired_games)} games purged")
            return purged_count
    
    except Exception as e:
        logger.error(f"Error in auto-purge process: {e}", exc_info=True)
        return 0


@router.message(Command("info"))
async def cmd_info(message: types.Message) -> None:
    """
    Handle /info command to show game information
    """
    parts = message.text.split(maxsplit=1)
    
    if len(parts) < 2:
        error_text = (
            "❌ <b>Неправильний формат команди</b>\n\n"
            "Використовуйте: <code>/info КОД_ГРИ</code>\n\n"
            "<b>Приклад:</b>\n"
            "<code>/info SANTA42</code>"
        )
        await message.answer(error_text, parse_mode="HTML")
        return
    
    game_code = parts[1].upper()
    
    try:
        async with get_session() as session:
            repository = GameRepository(session)
            
            game = await repository.get_game_by_code(game_code)
            
            if not game:
                error_text = (
                    f"❌ <b>Гра не знайдена</b>\n\n"
                    f"Гра з кодом <code>{game_code}</code> не існує."
                )
                await message.answer(error_text, parse_mode="HTML")
                return
            
            stats = await repository.get_game_stats(game.id)
            
            # Format dates
            created_date = game.created_at.strftime("%d.%m.%Y %H:%M")
            
            purge_info = "Не встановлено"
            if game.auto_purge_at:
                purge_date = game.auto_purge_at.strftime("%d.%m.%Y")
                days_until_purge = (game.auto_purge_at - datetime.utcnow()).days
                purge_info = f"{purge_date} (через {days_until_purge} днів)"
            
            # Status icons
            lock_status = "🔒 Заблокована" if game.is_locked else "🔓 Відкрита"
            draw_status = "✅ Проведено" if game.is_drawn else "⏳ Не проведено"
            
            info_text = (
                f"ℹ️ <b>Інформація про гру</b>\n\n"
                f"🎮 <b>Код:</b> <code>{game_code}</code>\n"
                f"📅 <b>Створена:</b> {created_date}\n"
                f"🗑 <b>Автовидалення:</b> {purge_info}\n\n"
                f"<b>Статус:</b>\n"
                f"• Набір учасників: {lock_status}\n"
                f"• Жеребкування: {draw_status}\n\n"
                f"<b>Статистика:</b>\n"
                f"👥 Учасників: {stats['participant_count']}\n"
                f"🎁 Результатів: {stats['draw_count']}\n"
            )
            
            # Add action hints
            if not game.is_locked and stats['participant_count'] >= 3:
                info_text += (
                    f"\n💡 <b>Доступна дія:</b>\n"
                    f"Можна заблокувати гру: <code>/lock {game_code}</code>"
                )
            elif game.is_locked and not game.is_drawn:
                info_text += (
                    f"\n💡 <b>Доступна дія:</b>\n"
                    f"Можна провести жеребкування: <code>/draw {game_code}</code>"
                )
            elif game.is_drawn:
                info_text += (
                    f"\n💡 <b>Доступні дії:</b>\n"
                    f"• Експортувати результати: <code>/export {game_code}</code>\n"
                    f"• Видалити гру: <code>/purge {game_code}</code>"
                )
            
            await message.answer(info_text, parse_mode="HTML")
    
    except Exception as e:
        logger.error(f"Error getting info for game {game_code}: {e}")
        error_text = "❌ Помилка отримання інформації."
        await message.answer(error_text, parse_mode="HTML")