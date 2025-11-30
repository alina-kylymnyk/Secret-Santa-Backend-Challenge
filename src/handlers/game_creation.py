import logging
from datetime import datetime, timedelta

from aiogram import Router, types
from aiogram.filters import Command

from src.database import get_session, GameRepository
from utils.code_generator import generate_game_code
from utils.keyboards import get_main_menu_keyboard

logger = logging.getLogger(__name__)

router = Router(name="game_creation")

# Configuration
AUTO_PURGE_DAYS = 30

@router.message(Command("new"))
async def cmd_new(message):
    """
    Handle /new command to create a new Secret Santa game.
    """

    user_id = message.from_user.id
    username = message.from_user.username or message.from_user.first_name

    logger.info(f"User {username} (ID: {user_id}) is creating a new game")

    try:
        async with get_session() as session:
            repository = GameRepository(session)

            # Generate unique game code
            game_code = await generate_game_code(session, prefix_list=None, suffix_length=None)

            # Calculate auto-purge date
            auto_purge_at = datetime.utcnow() + timedelta(days=AUTO_PURGE_DAYS)
            
            # Create game in database
            game = await repository.create_game(
                game_code=game_code,
                creator_chat_id=user_id,
                auto_purge_at=auto_purge_at
            )

            logger.info(
                f"Game created: {game_code} by user {username} "
                f"(will auto-purge at {auto_purge_at.date()})"
            )

            # Send success message
            response_text = (
                "✅ <b>Гра створена!</b>\n\n"
                f"🎮 <b>Код гри:</b> <code>{game_code}</code>\n\n"
                "📤 Поділіться цим кодом з друзями для приєднання!\n\n"
                "ℹ️ <b>Наступні кроки:</b>\n"
                f"1️⃣ Друзі використовують: <code>/join {game_code} Ім'я</code>\n"
                f"2️⃣ Коли всі приєдналися: <code>/lock {game_code}</code>\n"
                f"3️⃣ Проведіть жеребкування: <code>/draw {game_code}</code>\n"
                f"4️⃣ Отримайте результати: <code>/export {game_code}</code>\n\n"
                f"🗑 Гра автоматично видалиться через {AUTO_PURGE_DAYS} днів"
            )

            await message.answer(
                response_text,
                parse_mode="HTML",
                reply_markup=get_main_menu_keyboard()
            )

    except Exception as e:
        logger.error(f"Error creating game: {e}", exc_info=True)

        error_text = (
            "❌ <b>Помилка створення гри</b>\n\n"
            "Щось пішло не так. Спробуйте ще раз або зв'яжіться з підтримкою."
        )

        await message.answer(error_text, parse_mode="HTML")


@router.message(Command("start"))
async def cmd_start(message):
    """
    Handle /start command - welcome message
    """

    username = message.from_user.first_name or "друже"

    welcome_text = (
        f"🎅 <b>Привіт, {username}!</b>\n\n"
        "Вітаю в боті Secret Santa! 🎁\n\n"
        "Я допоможу організувати таємний обмін подарунками "
        "серед друзів, колег чи команди.\n\n"
        "<b>📋 Доступні команди:</b>\n\n"
        "🆕 <code>/new</code> - створити нову гру\n"
        "➕ <code>/join CODE ІМ'Я</code> - приєднатися до гри\n"
        "🔒 <code>/lock CODE</code> - закрити набір учасників\n"
        "🎲 <code>/draw CODE</code> - провести жеребкування\n"
        "📤 <code>/export CODE</code> - отримати результати\n"
        "🗑 <code>/purge CODE</code> - видалити гру\n\n"
        "<b>❓ Як це працює:</b>\n\n"
        "1. Організатор створює гру командою /new\n"
        "2. Учасники приєднуються за кодом гри\n"
        "3. Організатор блокує набір і проводить жеребкування\n"
        "4. Кожен учасник дізнається, кому дарувати подарунок\n\n"
        "🔒 <b>Конфіденційність:</b> бот не зберігає особисті дані - "
        "лише імена учасників!\n\n"
        "Почніть зі створення гри: /new"
    )

    await message.answer(
        welcome_text,
        parse_mode="HTML",
        reply_markup=get_main_menu_keyboard()
    )


@router.message(Command("help"))
async def cmd_help(message: types.Message) -> None:
    """
    Handle /help command - show help information.
    
    Args:
        message: Telegram message object
    """
    help_text = (
        "📚 <b>Довідка Secret Santa Bot</b>\n\n"
        
        "<b>🆕 Створення гри:</b>\n"
        "<code>/new</code>\n"
        "Створює нову гру та генерує унікальний код.\n\n"
        
        "<b>➕ Приєднання до гри:</b>\n"
        "<code>/join SANTA42 Іван</code>\n"
        "Приєднує учасника з ім'ям 'Іван' до гри SANTA42.\n"
        "⚠️ Ім'я має бути унікальним в рамках гри.\n\n"
        
        "<b>🔒 Закриття набору:</b>\n"
        "<code>/lock SANTA42</code>\n"
        "Блокує гру - нові учасники не зможуть приєднатися.\n"
        "Потрібно мінімум 3 учасники.\n"
        "📝 Цю команду може виконати тільки організатор.\n\n"
        
        "<b>🎲 Жеребкування:</b>\n"
        "<code>/draw SANTA42</code>\n"
        "Проводить жеребкування і визначає, хто кому дарує.\n"
        "📝 Тільки для організатора заблокованої гри.\n\n"
        
        "<b>📤 Експорт результатів:</b>\n"
        "<code>/export SANTA42</code>\n"
        "Отримати результати у текстовому форматі або CSV.\n"
        "📝 Тільки для організатора після жеребкування.\n\n"
        
        "<b>🗑 Видалення гри:</b>\n"
        "<code>/purge SANTA42</code>\n"
        "Остаточно видаляє гру та всі дані.\n"
        "📝 Тільки для організатора.\n\n"
        
        "<b>🔐 Конфіденційність:</b>\n"
        "• Бот не зберігає номери телефонів чи email\n"
        "• Зберігаються тільки імена учасників\n"
        "• Ігри автоматично видаляються через 30 днів\n"
        "• Результати жеребкування бачить тільки організатор\n\n"
        
        "<b>💡 Поради:</b>\n"
        "• Використовуйте прості та зрозумілі імена\n"
        "• Мінімум 3 учасники для жеребкування\n"
        "• Збережіть код гри в безпечному місці\n"
        "• Після завершення видаліть гру командою /purge\n\n"
        
        "❓ Питання? Пишіть @your_support_bot"
    )
    
    await message.answer(
        help_text,
        parse_mode="HTML",
        reply_markup=get_main_menu_keyboard()
    )






