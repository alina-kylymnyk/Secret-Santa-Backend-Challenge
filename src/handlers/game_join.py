import logging
from typing import Optional

from aiogram import Router, types
from aiogram.filters import Command

from src.database import get_session, GameRepository
from utils.validators import ParticipantNameValidator, ValidationError, sanitize_name
from utils.keyboards import get_main_menu_keyboard

logger = logging.getLogger(__name__)

router = Router(name="game_join")

def parse_join_command(text):
    """
    Parse /join command to extract game code and participant name
    """

    parts = text.split(maxsplit=2)
    
    if len(parts) < 3:
        return None, None
    
    game_code = parts[1].upper()
    name = parts[2]
    
    return game_code, name

@router.message(Command("join"))
async def cmd_join(message):
    """
    Handle /join command to add a participant to a game
    """
    user_id = message.from_user.id
    username = message.from_user.username or message.from_user.first_name

    # Parse command
    game_code, participant_name = parse_join_command(message.text)
    
    if not game_code or not participant_name:
        error_text = (
            "❌ <b>Неправильний формат команди</b>\n\n"
            "Використовуйте: <code>/join КОД_ГРИ Ім'я</code>\n\n"
            "<b>Приклад:</b>\n"
            "<code>/join SANTA42 Іван</code>"
        )
        await message.answer(error_text, parse_mode="HTML")
        return
    
    # Sanitize name
    participant_name = sanitize_name(participant_name)
    
    logger.info(
        f"User {username} (ID: {user_id}) attempting to join game {game_code} "
        f"as '{participant_name}'"
    )

    try:
        # Validate name
        try:
            ParticipantNameValidator.validate_or_raise(participant_name)
        except ValidationError as e:
            error_text = (
                f"❌ <b>Некоректне ім'я</b>\n\n"
                f"{str(e)}\n\n"
                "Ім'я має бути від 2 до 50 символів і містити тільки літери, "
                "пробіли, дефіси та апострофи."
            )
            await message.answer(error_text, parse_mode="HTML")
            return
        
        async with get_session() as session:
            repository = GameRepository(session)

            # Check if game exists
            logger.info(f"Looking up game with code: {game_code}")
            game = await repository.get_game_by_code(game_code)

            if not game:
                logger.warning(f"Game not found: {game_code}")
                error_text = (
                    f"❌ <b>Гра не знайдена</b>\n\n"
                    f"Гра з кодом <code>{game_code}</code> не існує.\n\n"
                    "Перевірте код або попросіть організатора створити нову гру."
                )
                await message.answer(error_text, parse_mode="HTML")
                return

            logger.info(f"Game found: {game_code} (ID: {game.id})")
            
            # Check if game is locked
            if game.is_locked:
                error_text = (
                    f"🔒 <b>Гра заблокована</b>\n\n"
                    f"Гра <code>{game_code}</code> вже закрила набір учасників.\n"
                    "Нові учасники не можуть приєднатися."
                )
                await message.answer(error_text, parse_mode="HTML")
                return
            
            # Check if name already exists in this game
            if await repository.participant_exists(game.id, participant_name):
                error_text = (
                    f"❌ <b>Ім'я вже зайняте</b>\n\n"
                    f"Учасник з ім'ям '<b>{participant_name}</b>' вже є в цій грі.\n\n"
                    "Виберіть інше ім'я або додайте унікальний ідентифікатор "
                    "(наприклад, 'Іван К.' або 'Іван_2')."
                )
                await message.answer(error_text, parse_mode="HTML")
                return
            
            # Add participant
            await repository.add_participant(game.id, participant_name)
            
            # Get updated participant count
            participants = await repository.get_participants(game.id)
            participant_count = len(participants)
            
            logger.info(
                f"Participant '{participant_name}' added to game {game_code}. "
                f"Total participants: {participant_count}"
            )
            
            # Send success message
            response_text = (
                f"🎉 <b>{participant_name}</b> приєднався до гри!\n\n"
                f"🎮 Гра: <code>{game_code}</code>\n"
                f"👥 Загальна кількість учасників: <b>{participant_count}</b>\n\n"
            )
            
            # Add hints based on participant count
            if participant_count < 3:
                response_text += (
                    f"⚠️ Для жеребкування потрібно мінімум 3 учасники.\n"
                    f"Ще потрібно: {3 - participant_count}"
                )
            else:
                response_text += (
                    "✅ Достатньо учасників для жеребкування!\n\n"
                    "📋 <b>Список учасників:</b>\n"
                )
                for i, p in enumerate(participants, 1):
                    response_text += f"{i}. {p.name}\n"
                
                response_text += (
                    f"\n💡 Коли всі приєдналися, організатор може:\n"
                    f"1. Закрити набір: <code>/lock {game_code}</code>\n"
                    f"2. Провести жеребкування: <code>/draw {game_code}</code>"
                )

            await message.answer(
                response_text,
                parse_mode="HTML",
                reply_markup=get_main_menu_keyboard()
            )
    
    except Exception as e:
        logger.error(
            f"Error joining game {game_code} as {participant_name}: {e}",
            exc_info=True
        )
        
        error_text = (
            "❌ <b>Помилка приєднання до гри</b>\n\n"
            "Щось пішло не так. Спробуйте ще раз."
        )
        
        await message.answer(error_text, parse_mode="HTML")


@router.message(Command("list"))
async def cmd_list(message):
    """
    Handle /list command to show participants in a game
    """
    parts = message.text.split(maxsplit=1)

    if len(parts) < 2:
        error_text = (
            "❌ <b>Неправильний формат команди</b>\n\n"
            "Використовуйте: <code>/list КОД_ГРИ</code>\n\n"
            "<b>Приклад:</b>\n"
            "<code>/list SANTA42</code>"
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
            
            participants = await repository.get_participants(game.id)
            
            if not participants:
                response_text = (
                    f"📋 <b>Учасники гри {game_code}</b>\n\n"
                    "Поки що немає учасників.\n\n"
                    f"Приєднайтесь: <code>/join {game_code} Ваше_Ім'я</code>"
                )
            else:
                status = "🔒 Заблокована" if game.is_locked else "🔓 Відкрита"
                drawn_status = "✅ Проведено" if game.is_drawn else "⏳ Очікує"
                
                response_text = (
                    f"📋 <b>Учасники гри {game_code}</b>\n\n"
                    f"Статус: {status}\n"
                    f"Жеребкування: {drawn_status}\n"
                    f"Всього учасників: <b>{len(participants)}</b>\n\n"
                )
                
                for i, p in enumerate(participants, 1):
                    response_text += f"{i}. {p.name}\n"
                
                if not game.is_locked and len(participants) >= 3:
                    response_text += (
                        f"\n💡 Готово до жеребкування!\n"
                        f"Організатор може заблокувати гру: "
                        f"<code>/lock {game_code}</code>"
                    )

            await message.answer(
                response_text,
                parse_mode="HTML",
                reply_markup=get_main_menu_keyboard()
            )
    
    except Exception as e:
        logger.error(f"Error listing participants for game {game_code}: {e}")
        error_text = "❌ Помилка отримання списку учасників."
        await message.answer(error_text, parse_mode="HTML")


    