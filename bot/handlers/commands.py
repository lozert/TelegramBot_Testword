"""
Обработчики команд бота (/start, /help) и кнопки "Новый запрос".
"""

import logging

from telegram import KeyboardButton, ReplyKeyboardMarkup, Update
from telegram.ext import ContextTypes

from bot.services.history import DialogHistoryManager

logger = logging.getLogger(__name__)

# Текст кнопки «Новый запрос» — по нему обрабатываем нажатие в handle_text_message
NEW_REQUEST_BUTTON_TEXT = "Новый запрос"

# Менеджер истории передаётся извне (см. main.py), но на всякий случай
# определим тип-подсказку и ожидаемое имя в context.
HISTORY_MANAGER_KEY = "history_manager"


def _get_history_manager(context: ContextTypes.DEFAULT_TYPE) -> DialogHistoryManager:
    manager = context.application.bot_data.get(HISTORY_MANAGER_KEY)
    assert isinstance(manager, DialogHistoryManager)
    return manager


def get_new_request_keyboard() -> ReplyKeyboardMarkup:
    """Обычная (reply) клавиатура с кнопкой «Новый запрос» для сброса контекста."""
    return ReplyKeyboardMarkup(
        [[KeyboardButton(NEW_REQUEST_BUTTON_TEXT)]],
        resize_keyboard=True,
    )


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Команда /start — приветствие и сброс контекста диалога."""
    if not update.effective_user or not update.effective_chat:
        return

    user_id = update.effective_user.id
    username = update.effective_user.username or f"user_{user_id}"
    logger.info(f"Команда /start от пользователя {username} (ID: {user_id})")

    history_manager = _get_history_manager(context)
    history_manager.reset_context(user_id)
    logger.debug(f"История диалога пользователя {user_id} очищена")

    text = (
        "Привет! Я бот, который отвечает с помощью ChatGPT.\n\n"
        "Отправь мне любой текст, и я постараюсь помочь.\n"
        "Чтобы начать новый независимый диалог, нажми кнопку «Новый запрос» "
        "или снова введи /start."
    )

    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=text,
        reply_markup=get_new_request_keyboard(),
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Команда /help — краткая справка по возможностям бота."""
    if not update.effective_chat or not update.effective_user:
        return

    user_id = update.effective_user.id
    username = update.effective_user.username or f"user_{user_id}"
    logger.info(f"Команда /help от пользователя {username} (ID: {user_id})")

    help_text = (
        "Я бот, который использует ChatGPT для ответов.\n\n"
        "Доступные действия:\n"
        "• /start — начать новый диалог и сбросить контекст\n"
        "• /help — показать эту справку\n"
        "• Просто напиши сообщение — я отвечу с учётом истории диалога\n"
        "• Кнопка «Новый запрос» (внизу экрана) — сбросить контекст и начать заново"
    )

    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=help_text,
    )


async def handle_new_request_button(
    update: Update, context: ContextTypes.DEFAULT_TYPE, chat_id: int, user_id: int
) -> bool:
    """
    Обработка нажатия кнопки «Новый запрос» (reply-клавиатура).
    Очищает историю и отправляет подтверждение. Возвращает True, если обработано.
    """
    if not update.message or not update.message.text:
        return False
    if update.message.text.strip() != NEW_REQUEST_BUTTON_TEXT:
        return False

    username = update.effective_user.username or f"user_{user_id}" if update.effective_user else f"user_{user_id}"
    logger.info(f"Кнопка 'Новый запрос' нажата пользователем {username} (ID: {user_id})")

    history_manager = _get_history_manager(context)
    async with history_manager.lock(user_id):
        history_manager.clear_history(user_id)
    logger.info(f"История диалога удалена для пользователя {user_id}")

    text = (
        "История диалога удалена.\n\n"
        "Можешь отправить новый запрос — я буду отвечать без учёта предыдущих сообщений."
    )
    await context.bot.send_message(
        chat_id=chat_id,
        text=text,
        reply_markup=get_new_request_keyboard(),
    )
    return True

