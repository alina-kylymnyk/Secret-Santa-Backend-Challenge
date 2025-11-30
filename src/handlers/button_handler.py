"""Button handler for keyboard interactions"""

import logging
from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from utils.keyboards import get_main_menu_keyboard

logger = logging.getLogger(__name__)

router = Router(name="button_handler")


class GameCodeInput(StatesGroup):
    """States for game code input"""
    waiting_for_code = State()
    waiting_for_join_data = State()


# Import command handlers
from . import game_creation, game_join, game_lock, draw, game_export, game_purge


async def get_last_game_code_keyboard(state: FSMContext, command_type: str):
    """
    Get inline keyboard with last used game code if available
    """
    data = await state.get_data()
    last_code = data.get("last_game_code")

    if last_code:
        keyboard = InlineKeyboardBuilder()
        keyboard.row(
            InlineKeyboardButton(
                text=f"✅ Використати {last_code}",
                callback_data=f"use_last_code:{command_type}:{last_code}"
            )
        )
        keyboard.row(
            InlineKeyboardButton(
                text="📝 Ввести інший код",
                callback_data=f"enter_new_code:{command_type}"
            )
        )
        return keyboard.as_markup()
    return None


@router.message(F.text == "🆕 Створити гру")
async def button_new_game(message: types.Message):
    """Handle new game button"""
    await game_creation.cmd_new(message)


@router.message(F.text == "❓ Допомога")
async def button_help(message: types.Message):
    """Handle help button"""
    await game_creation.cmd_help(message)


@router.message(F.text == "🏠 Головне меню")
async def button_main_menu(message: types.Message):
    """Handle main menu button"""
    await game_creation.cmd_start(message)


@router.message(F.text == "➕ Приєднатись")
async def button_join(message: types.Message, state: FSMContext):
    """Handle join button"""
    await state.set_state(GameCodeInput.waiting_for_join_data)
    await message.answer(
        "📝 <b>Приєднання до гри</b>\n\n"
        "Введіть код гри та ваше ім'я через пробіл:\n\n"
        "<b>Приклад:</b>\n"
        "<code>SANTA42 Ваше_Ім'я</code>",
        parse_mode="HTML"
    )


@router.message(F.text == "📋 Список учасників")
async def button_list(message: types.Message, state: FSMContext):
    """Handle list button"""
    await state.update_data(command_type="list")

    # Check if there's a last used game code
    keyboard = await get_last_game_code_keyboard(state, "list")

    if keyboard:
        await message.answer(
            "📝 <b>Список учасників</b>\n\n"
            "Використати останній код гри або ввести новий?",
            parse_mode="HTML",
            reply_markup=keyboard
        )
    else:
        await state.set_state(GameCodeInput.waiting_for_code)
        await message.answer(
            "📝 <b>Список учасників</b>\n\n"
            "Введіть код гри:\n\n"
            "<b>Приклад:</b> <code>SANTA42</code>",
            parse_mode="HTML"
        )


@router.message(F.text == "ℹ️ Інфо про гру")
async def button_info(message: types.Message, state: FSMContext):
    """Handle info button"""
    await state.update_data(command_type="info")
    keyboard = await get_last_game_code_keyboard(state, "info")

    if keyboard:
        await message.answer(
            "📝 <b>Інформація про гру</b>\n\n"
            "Використати останній код гри або ввести новий?",
            parse_mode="HTML",
            reply_markup=keyboard
        )
    else:
        await state.set_state(GameCodeInput.waiting_for_code)
        await message.answer(
            "📝 <b>Інформація про гру</b>\n\n"
            "Введіть код гри:\n\n"
            "<b>Приклад:</b> <code>SANTA42</code>",
            parse_mode="HTML"
        )


@router.message(F.text == "🔒 Заблокувати")
async def button_lock(message: types.Message, state: FSMContext):
    """Handle lock button"""
    await state.update_data(command_type="lock")
    keyboard = await get_last_game_code_keyboard(state, "lock")

    if keyboard:
        await message.answer(
            "📝 <b>Блокування гри</b>\n\n"
            "Використати останній код гри або ввести новий?",
            parse_mode="HTML",
            reply_markup=keyboard
        )
    else:
        await state.set_state(GameCodeInput.waiting_for_code)
        await message.answer(
            "📝 <b>Блокування гри</b>\n\n"
            "Введіть код гри:\n\n"
            "<b>Приклад:</b> <code>SANTA42</code>",
            parse_mode="HTML"
        )


@router.message(F.text == "🔓 Розблокувати")
async def button_unlock(message: types.Message, state: FSMContext):
    """Handle unlock button"""
    await state.update_data(command_type="unlock")
    keyboard = await get_last_game_code_keyboard(state, "unlock")

    if keyboard:
        await message.answer(
            "📝 <b>Розблокування гри</b>\n\n"
            "Використати останній код гри або ввести новий?",
            parse_mode="HTML",
            reply_markup=keyboard
        )
    else:
        await state.set_state(GameCodeInput.waiting_for_code)
        await message.answer(
            "📝 <b>Розблокування гри</b>\n\n"
            "Введіть код гри:\n\n"
            "<b>Приклад:</b> <code>SANTA42</code>",
            parse_mode="HTML"
        )


@router.message(F.text == "🎲 Жеребкування")
async def button_draw(message: types.Message, state: FSMContext):
    """Handle draw button"""
    await state.update_data(command_type="draw")
    keyboard = await get_last_game_code_keyboard(state, "draw")

    if keyboard:
        await message.answer(
            "📝 <b>Жеребкування</b>\n\n"
            "Використати останній код гри або ввести новий?",
            parse_mode="HTML",
            reply_markup=keyboard
        )
    else:
        await state.set_state(GameCodeInput.waiting_for_code)
        await message.answer(
            "📝 <b>Жеребкування</b>\n\n"
            "Введіть код гри:\n\n"
            "<b>Приклад:</b> <code>SANTA42</code>",
            parse_mode="HTML"
        )


@router.message(F.text == "📤 Експорт")
async def button_export(message: types.Message, state: FSMContext):
    """Handle export button"""
    await state.update_data(command_type="export")
    keyboard = await get_last_game_code_keyboard(state, "export")

    if keyboard:
        await message.answer(
            "📝 <b>Експорт результатів</b>\n\n"
            "Використати останній код гри або ввести новий?",
            parse_mode="HTML",
            reply_markup=keyboard
        )
    else:
        await state.set_state(GameCodeInput.waiting_for_code)
        await message.answer(
            "📝 <b>Експорт результатів</b>\n\n"
            "Введіть код гри:\n\n"
            "<b>Приклад:</b> <code>SANTA42</code>",
            parse_mode="HTML"
        )


@router.message(F.text == "🗑 Видалити гру")
async def button_purge(message: types.Message, state: FSMContext):
    """Handle purge button"""
    await state.update_data(command_type="purge")
    keyboard = await get_last_game_code_keyboard(state, "purge")

    if keyboard:
        await message.answer(
            "📝 <b>Видалення гри</b>\n\n"
            "Використати останній код гри або ввести новий?",
            parse_mode="HTML",
            reply_markup=keyboard
        )
    else:
        await state.set_state(GameCodeInput.waiting_for_code)
        await message.answer(
            "📝 <b>Видалення гри</b>\n\n"
            "Введіть код гри:\n\n"
            "<b>Приклад:</b> <code>SANTA42</code>",
            parse_mode="HTML"
        )


@router.callback_query(F.data.startswith("use_last_code:"))
async def callback_use_last_code(callback: types.CallbackQuery, state: FSMContext):
    """Handle using last game code"""
    parts = callback.data.split(":")
    command_type = parts[1]
    game_code = parts[2]

    await callback.answer()
    await callback.message.delete()

    # Create a modified message with the command, using callback.from_user
    modified_message = callback.message.model_copy(update={
        "text": f"/{command_type} {game_code}",
        "from_user": callback.from_user
    })

    logger.info(f"Using last code from button: /{command_type} {game_code}")

    # Call appropriate handler
    await execute_command(command_type, game_code, modified_message, state)


@router.callback_query(F.data.startswith("enter_new_code:"))
async def callback_enter_new_code(callback: types.CallbackQuery, state: FSMContext):
    """Handle entering new game code"""
    command_type = callback.data.split(":")[1]

    await callback.answer()
    await callback.message.delete()

    await state.set_state(GameCodeInput.waiting_for_code)

    command_names = {
        "list": "Список учасників",
        "info": "Інформація про гру",
        "lock": "Блокування гри",
        "unlock": "Розблокування гри",
        "draw": "Жеребкування",
        "export": "Експорт результатів",
        "purge": "Видалення гри"
    }

    await callback.message.answer(
        f"📝 <b>{command_names.get(command_type, 'Введіть код гри')}</b>\n\n"
        f"Введіть код гри:\n\n"
        f"<b>Приклад:</b> <code>SANTA42</code>",
        parse_mode="HTML"
    )


async def execute_command(command_type: str, game_code: str, message: types.Message, state: FSMContext):
    """Execute command and save last game code"""
    # Save last game code for future use
    await state.update_data(last_game_code=game_code)

    # Call appropriate handler based on command type
    if command_type == "list":
        await game_join.cmd_list(message)
    elif command_type == "info":
        await game_purge.cmd_info(message)
    elif command_type == "lock":
        await game_lock.cmd_lock(message)
    elif command_type == "unlock":
        await game_lock.cmd_unlock(message)
    elif command_type == "draw":
        await draw.cmd_draw(message)
    elif command_type == "export":
        await game_export.cmd_export(message)
    elif command_type == "purge":
        await game_purge.cmd_purge(message)


@router.message(GameCodeInput.waiting_for_code)
async def process_game_code(message: types.Message, state: FSMContext):
    """Process game code input"""
    data = await state.get_data()
    command_type = data.get("command_type", "")
    game_code = message.text.strip().upper()

    # Clear state
    await state.clear()

    # Create a modified message with the command
    modified_message = message.model_copy(update={"text": f"/{command_type} {game_code}"})

    logger.info(f"Processing command from button: /{command_type} {game_code}")

    # Execute command and save last game code
    await execute_command(command_type, game_code, modified_message, state)


@router.message(GameCodeInput.waiting_for_join_data)
async def process_join_data(message: types.Message, state: FSMContext):
    """Process join command data (code + name)"""
    # The message should contain "CODE NAME"
    parts = message.text.strip().split(maxsplit=1)
    if len(parts) < 2:
        await state.clear()
        await message.answer(
            "❌ <b>Неправильний формат</b>\n\n"
            "Потрібно ввести код гри та ваше ім'я через пробіл.\n\n"
            "<b>Приклад:</b> <code>SANTA42 Іван</code>",
            parse_mode="HTML",
            reply_markup=get_main_menu_keyboard()
        )
        return

    game_code = parts[0].upper()
    name = parts[1]

    # Save last game code
    await state.update_data(last_game_code=game_code)
    await state.clear()

    # Create a modified message with the join command
    modified_message = message.model_copy(update={"text": f"/join {game_code} {name}"})

    logger.info(f"Processing join command from button: /join {game_code} {name}")

    # Call join handler
    await game_join.cmd_join(modified_message)


@router.message()
async def handle_unknown_message(message: types.Message):
    """
    Handle any unknown text messages (fallback handler)
    """
    logger.info(f"Unknown message from user {message.from_user.id}: {message.text}")

    await message.answer(
        "🤔 <b>Не зрозумів вашу команду</b>\n\n"
        "Скористайтесь кнопками нижче або подивіться список доступних команд:\n"
        "❓ /help\n\n"
        "Або натисніть кнопку <b>❓ Допомога</b>",
        parse_mode="HTML",
        reply_markup=get_main_menu_keyboard()
    )
