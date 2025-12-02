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
                KeyboardButton(text="➕ Приєднатись"),
            ],
            [
                KeyboardButton(text="📋 Список учасників"),
                KeyboardButton(text="ℹ️ Інфо про гру"),
            ],
            [
                KeyboardButton(text="🔒 Заблокувати"),
                KeyboardButton(text="🔓 Розблокувати"),
            ],
            [KeyboardButton(text="🎲 Жеребкування"), KeyboardButton(text="📤 Експорт")],
            [KeyboardButton(text="🗑 Видалити гру"), KeyboardButton(text="❓ Допомога")],
        ],
        resize_keyboard=True,
        input_field_placeholder="Оберіть дію або введіть команду",
    )
    return keyboard
