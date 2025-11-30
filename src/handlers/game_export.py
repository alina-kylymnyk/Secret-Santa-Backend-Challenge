import logging

from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.types import BufferedInputFile, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from src.database import get_session, GameRepository
from services.export_service import ExportService, ExportFormatter

logger = logging.getLogger(__name__)

router = Router(name="game_export")


@router.message(Command("export"))
async def cmd_export(message):
    """
    Handle /export command to export draw results
    """
    user_id = message.from_user.id
    username = message.from_user.username or message.from_user.first_name

    # Parse command
    parts = message.text.split(maxsplit=1)

    if len(parts) < 2:
        error_text = (
            "❌ <b>Неправильний формат команди</b>\n\n"
            "Використовуйте: <code>/export КОД_ГРИ</code>\n\n"
            "<b>Приклад:</b>\n"
            "<code>/export SANTA42</code>"
        )
        await message.answer(error_text, parse_mode="HTML")
        return

    game_code = parts[1].upper()

    logger.info(
        f"User {username} (ID: {user_id}) requesting export for game {game_code}"
    )

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
                    "Тільки організатор гри може експортувати результати.\n\n"
                    "Це необхідно для збереження конфіденційності результатів."
                )
                await message.answer(error_text, parse_mode="HTML")
                return

            # Check if draw has been performed
            if not game.is_drawn:
                error_text = (
                    "⏳ <b>Жеребкування ще не проведено</b>\n\n"
                    "Спочатку проведіть жеrebкування:\n"
                    f"<code>/draw {game_code}</code>"
                )
                await message.answer(error_text, parse_mode="HTML")
                return

            # Get draw results
            results = await repository.get_draw_results(game.id)

            if not results:
                error_text = (
                    "❌ <b>Результати не знайдено</b>\n\n"
                    "Щось пішло не так. Спробуйте провести жеребкування знову."
                )
                await message.answer(error_text, parse_mode="HTML")
                return

            logger.info(f"Exporting {len(results)} results for game {game_code}")

            # Validate results
            is_valid, validation_msg = ExportService.validate_results(results)
            if not is_valid:
                logger.error(f"Invalid results for game {game_code}: {validation_msg}")
                error_text = (
                    f"⚠️ <b>Помилка валідації</b>\n\n"
                    f"Результати не пройшли перевірку: {validation_msg}\n\n"
                    "Спробуйте перепровести жеребкування: <code>/redraw {game_code}</code>"
                )
                await message.answer(error_text, parse_mode="HTML")
                return

            # Create inline keyboard with export options
            keyboard = InlineKeyboardBuilder()
            keyboard.row(
                InlineKeyboardButton(
                    text="📄 Текст", callback_data=f"export_text:{game_code}"
                ),
                InlineKeyboardButton(
                    text="📊 CSV", callback_data=f"export_csv:{game_code}"
                ),
            )
            keyboard.row(
                InlineKeyboardButton(
                    text="📋 Таблиця", callback_data=f"export_table:{game_code}"
                )
            )

            response_text = (
                f"📤 <b>Експорт результатів</b>\n\n"
                f"🎮 Гра: <code>{game_code}</code>\n"
                f"🎁 Пар: <b>{len(results)}</b>\n\n"
                "Оберіть формат експорту:"
            )

            await message.answer(
                response_text, parse_mode="HTML", reply_markup=keyboard.as_markup()
            )

    except Exception as e:
        logger.error(f"Error exporting game {game_code}: {e}", exc_info=True)

        error_text = (
            "❌ <b>Помилка експорту</b>\n\n" "Щось пішло не так. Спробуйте ще раз."
        )

        await message.answer(error_text, parse_mode="HTML")


@router.callback_query(F.data.startswith("export_text:"))
async def callback_export_text(callback):
    """
    Handle text export callback
    """
    game_code = callback.data.split(":")[1]
    user_id = callback.from_user.id

    try:
        async with get_session() as session:
            repository = GameRepository(session)

            game = await repository.get_game_by_code(game_code)

            if not game or game.creator_chat_id != user_id:
                await callback.answer("❌ Доступ заборонено", show_alert=True)
                return

            results = await repository.get_draw_results(game.id)

            # Generate text export
            export_text = ExportService.generate_text_export(results, game_code)

            # Send as regular message
            await callback.message.answer(
                f"<pre>{export_text}</pre>", parse_mode="HTML"
            )

            await callback.answer("✅ Експортовано як текст")

            logger.info(f"Text export completed for game {game_code}")

    except Exception as e:
        logger.error(f"Error in text export callback: {e}", exc_info=True)
        await callback.answer("❌ Помилка експорту", show_alert=True)


@router.callback_query(F.data.startswith("export_csv:"))
async def callback_export_csv(callback):
    """
    Handle CSV export callback
    """
    game_code = callback.data.split(":")[1]
    user_id = callback.from_user.id

    try:
        async with get_session() as session:
            repository = GameRepository(session)

            game = await repository.get_game_by_code(game_code)

            if not game or game.creator_chat_id != user_id:
                await callback.answer("❌ Доступ заборонено", show_alert=True)
                return

            results = await repository.get_draw_results(game.id)

            # Generate CSV export
            csv_data = ExportService.generate_csv_export(results)

            # Create file
            file = BufferedInputFile(
                csv_data.read(), filename=f"secret_santa_{game_code}.csv"
            )

            # Send file
            await callback.message.answer_document(
                file,
                caption=(
                    f"📊 <b>CSV експорт</b>\n\n"
                    f"Гра: <code>{game_code}</code>\n"
                    f"Пар: {len(results)}\n\n"
                    "⚠️ Зберігайте цей файл в безпечному місці!"
                ),
                parse_mode="HTML",
            )

            await callback.answer("✅ CSV файл надіслано")

            logger.info(f"CSV export completed for game {game_code}")

    except Exception as e:
        logger.error(f"Error in CSV export callback: {e}", exc_info=True)
        await callback.answer("❌ Помилка експорту", show_alert=True)


@router.callback_query(F.data.startswith("export_table:"))
async def callback_export_table(callback):
    """
    Handle table export callback
    """
    game_code = callback.data.split(":")[1]
    user_id = callback.from_user.id

    try:
        async with get_session() as session:
            repository = GameRepository(session)

            game = await repository.get_game_by_code(game_code)

            if not game or game.creator_chat_id != user_id:
                await callback.answer("❌ Доступ заборонено", show_alert=True)
                return

            results = await repository.get_draw_results(game.id)

            # Generate table export
            table = ExportFormatter.format_table(results)

            # Send as code block for monospace formatting
            await callback.message.answer(
                f"📋 <b>Результати у вигляді таблиці</b>\n\n"
                f"<pre>{table}</pre>\n\n"
                f"Гра: <code>{game_code}</code>",
                parse_mode="HTML",
            )

            await callback.answer("✅ Таблиця створена")

            logger.info(f"Table export completed for game {game_code}")

    except Exception as e:
        logger.error(f"Error in table export callback: {e}", exc_info=True)
        await callback.answer("❌ Помилка експорту", show_alert=True)
