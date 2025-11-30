import logging

from aiogram import Router, types
from aiogram.filters import Command

from src.database import get_session, GameRepository
from services.draw_service import DrawService, DrawError, InsufficientParticipantError

logger = logging.getLogger(__name__)

router = Router(name="game_draw")


@router.message(Command("draw"))
async def cmd_draw(message) :
    """
    Handle /draw command to perform Secret Santa draw
    """
    user_id = message.from_user.id
    username = message.from_user.username or message.from_user.first_name
    
    # Parse command
    parts = message.text.split(maxsplit=1)
    
    if len(parts) < 2:
        error_text = (
            "❌ <b>Неправильний формат команди</b>\n\n"
            "Використовуйте: <code>/draw КОД_ГРИ</code>\n\n"
            "<b>Приклад:</b>\n"
            "<code>/draw SANTA42</code>"
        )
        await message.answer(error_text, parse_mode="HTML")
        return
    
    game_code = parts[1].upper()
    
    logger.info(f"User {username} (ID: {user_id}) attempting to draw game {game_code}")
    
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
                    "Тільки організатор гри може провести жеребкування.\n\n"
                    "Якщо ви організатор, переконайтеся що використовуєте "
                    "той самий обліковий запис."
                )
                await message.answer(error_text, parse_mode="HTML")
                return
            
            # Check if game is locked
            if not game.is_locked:
                error_text = (
                    "🔓 <b>Гра не заблокована</b>\n\n"
                    "Перед жеребкуванням потрібно заблокувати набір учасників:\n"
                    f"<code>/lock {game_code}</code>\n\n"
                    "Це гарантує, що всі учасники вже приєдналися."
                )
                await message.answer(error_text, parse_mode="HTML")
                return
            
            # Check if draw already performed
            if game.is_drawn:
                error_text = (
                    "✅ <b>Жеребкування вже проведено</b>\n\n"
                    f"Гра <code>{game_code}</code> вже має результати жеребкування.\n\n"
                    "Отримати результати:\n"
                    f"<code>/export {game_code}</code>"
                )
                await message.answer(error_text, parse_mode="HTML")
                return
            
            # Get participants
            participants = await repository.get_participants(game.id)
            participant_names = [p.name for p in participants]
            
            logger.info(
                f"Performing draw for game {game_code} with {len(participant_names)} participants"
            )
            
            # Send processing message
            processing_msg = await message.answer(
                "🎲 <b>Проводжу жеребкування...</b>\n\n"
                "Зачекайте кілька секунд...",
                parse_mode="HTML"
            )
            
            try:
                # Perform the draw
                draw_service = DrawService()
                draw_result = draw_service.perform_draw(participant_names)
                
                # Verify draw properties
                properties = draw_service.verify_draw_properties(draw_result)
                
                if not all(properties.values()):
                    raise DrawError("Draw verification failed")
                
                # Save results to database
                await repository.save_draw_results(game.id, draw_result)
                
                logger.info(
                    f"Draw completed successfully for game {game_code}. "
                    f"Results saved: {len(draw_result)} pairs"
                )
                
                # Delete processing message
                await processing_msg.delete()
                
                # Send success message
                response_text = (
                    "🎲 <b>Жеребкування завершено!</b>\n\n"
                    f"🎮 Гра: <code>{game_code}</code>\n"
                    f"👥 Учасників: <b>{len(participant_names)}</b>\n"
                    f"🎁 Пар створено: <b>{len(draw_result)}</b>\n\n"
                    "✅ Всі учасники розподілені!\n"
                    "🔒 Результати збережено в базі даних.\n\n"
                    "📤 <b>Отримати результати:</b>\n"
                    f"<code>/export {game_code}</code>\n\n"
                    "⚠️ <b>Важливо:</b>\n"
                    "• Зберігайте результати в безпечному місці\n"
                    "• Не діліться результатами з учасниками\n"
                    "• Повідомте кожному особисто, кому він дарує\n"
                    "• Після завершення видаліть гру: <code>/purge {game_code}</code>"
                )
                
                await message.answer(response_text, parse_mode="HTML")
            
            except InsufficientParticipantError as e:
                await processing_msg.delete()
                
                error_text = (
                    f"⚠️ <b>Недостатньо учасників</b>\n\n"
                    f"{str(e)}\n\n"
                    "Розблокуйте гру і додайте більше учасників:\n"
                    f"<code>/unlock {game_code}</code>"
                )
                await message.answer(error_text, parse_mode="HTML")
            
            except DrawError as e:
                await processing_msg.delete()
                
                logger.error(f"Draw error for game {game_code}: {e}")
                
                error_text = (
                    "❌ <b>Помилка жеребкування</b>\n\n"
                    f"{str(e)}\n\n"
                    "Спробуйте ще раз або зв'яжіться з підтримкою."
                )
                await message.answer(error_text, parse_mode="HTML")
    
    except Exception as e:
        logger.error(f"Error performing draw for game {game_code}: {e}", exc_info=True)
        
        error_text = (
            "❌ <b>Критична помилка</b>\n\n"
            "Щось пішло не так під час жеребкування.\n"
            "Спробуйте ще раз або створіть нову гру."
        )
        
        await message.answer(error_text, parse_mode="HTML")


@router.message(Command("redraw"))
async def cmd_redraw(message):
    """
    Handle /redraw command to perform draw again (admin/debug feature).
    """
    user_id = message.from_user.id
    
    # Parse command
    parts = message.text.split(maxsplit=1)
    
    if len(parts) < 2:
        error_text = (
            "❌ <b>Неправильний формат команди</b>\n\n"
            "Використовуйте: <code>/redraw КОД_ГРИ</code>\n\n"
            "⚠️ <b>Увага:</b> Ця команда перезапише існуючі результати!"
        )
        await message.answer(error_text, parse_mode="HTML")
        return
    
    game_code = parts[1].upper()
    
    try:
        async with get_session() as session:
            repository = GameRepository(session)
            
            game = await repository.get_game_by_code(game_code)
            
            if not game:
                error_text = f"❌ Гра <code>{game_code}</code> не знайдена."
                await message.answer(error_text, parse_mode="HTML")
                return
            
            if game.creator_chat_id != user_id:
                error_text = "🚫 Тільки організатор може перепровести жеребкування."
                await message.answer(error_text, parse_mode="HTML")
                return
            
            if not game.is_locked:
                error_text = "🔓 Спочатку заблокуйте гру: <code>/lock {game_code}</code>"
                await message.answer(error_text, parse_mode="HTML")
                return
            
            # Get participants
            participants = await repository.get_participants(game.id)
            participant_names = [p.name for p in participants]
            
            # Delete old results
            from sqlalchemy import delete
            from ..database.models import DrawResult
            
            stmt = delete(DrawResult).where(DrawResult.game_id == game.id)
            await session.execute(stmt)
            
            # Perform new draw
            draw_service = DrawService()
            draw_result = draw_service.perform_draw(participant_names)
            
            # Save new results
            await repository.save_draw_results(game.id, draw_result)
            
            response_text = (
                "🔄 <b>Жеребкування перепроведено!</b>\n\n"
                f"🎮 Гра: <code>{game_code}</code>\n"
                f"🎁 Нові результати збережено\n\n"
                "Отримати результати: <code>/export {game_code}</code>"
            )
            
            await message.answer(response_text, parse_mode="HTML")
    
    except Exception as e:
        logger.error(f"Error redrawing game {game_code}: {e}", exc_info=True)
        error_text = "❌ Помилка перепроведення жеребкування."
        await message.answer(error_text, parse_mode="HTML")