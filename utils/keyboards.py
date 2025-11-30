"""Keyboards module for Secret Santa Bot"""

from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove


def get_main_menu_keyboard():
    """
    Get main menu keyboard with primary commands
    """
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="🆕 Створити гру"),
                KeyboardButton(text="➕ Приєднатись")
            ],
            [
                KeyboardButton(text="📋 Список учасників"),
                KeyboardButton(text="ℹ️ Інфо про гру")
            ],
            [
                KeyboardButton(text="🔒 Заблокувати"),
                KeyboardButton(text="🔓 Розблокувати")
            ],
            [
                KeyboardButton(text="🎲 Жеребкування"),
                KeyboardButton(text="📤 Експорт")
            ],
            [
                KeyboardButton(text="🗑 Видалити гру"),
                KeyboardButton(text="❓ Допомога")
            ]
        ],
        resize_keyboard=True,
        input_field_placeholder="Оберіть дію або введіть команду"
    )
    return keyboard


def get_organizer_keyboard():
    """
    Get keyboard with organizer commands only
    """
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="🔒 Заблокувати"),
                KeyboardButton(text="🎲 Жеребкування")
            ],
            [
                KeyboardButton(text="📤 Експорт"),
                KeyboardButton(text="📋 Список учасників")
            ],
            [
                KeyboardButton(text="🗑 Видалити гру"),
                KeyboardButton(text="🏠 Головне меню")
            ]
        ],
        resize_keyboard=True,
        input_field_placeholder="Виберіть дію організатора"
    )
    return keyboard


def get_participant_keyboard():
    """
    Get keyboard with participant commands only
    """
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="📋 Список учасників"),
                KeyboardButton(text="ℹ️ Інфо про гру")
            ],
            [
                KeyboardButton(text="🏠 Головне меню")
            ]
        ],
        resize_keyboard=True,
        input_field_placeholder="Виберіть дію"
    )
    return keyboard


def get_minimal_keyboard():
    """
    Get minimal keyboard with just main menu button
    """
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🏠 Головне меню")]
        ],
        resize_keyboard=True,
        one_time_keyboard=False
    )
    return keyboard


def remove_keyboard():
    """
    Remove keyboard
    """
    return ReplyKeyboardRemove()


# Button text to command mapping
BUTTON_COMMANDS = {
    "🆕 Створити гру": "/new",
    "➕ Приєднатись": "/join",
    "📋 Список учасників": "/list",
    "ℹ️ Інфо про гру": "/info",
    "🔒 Заблокувати": "/lock",
    "🔓 Розблокувати": "/unlock",
    "🎲 Жеребкування": "/draw",
    "🔄 Перепровести": "/redraw",
    "📤 Експорт": "/export",
    "🗑 Видалити гру": "/purge",
    "❓ Допомога": "/help",
    "🏠 Головне меню": "/start"
}
