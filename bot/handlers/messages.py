"""
Обработчик текстовых сообщений от пользователей.
"""

import logging

from telegram import Update
from telegram.ext import ContextTypes

from bot.services.chatgpt import chatgpt_service
from bot.services.history import DialogHistoryManager
from bot.handlers.commands import (
    HISTORY_MANAGER_KEY,
    get_new_request_keyboard,
    handle_new_request_button,
)

logger = logging.getLogger(__name__)


def _get_history_manager(context: ContextTypes.DEFAULT_TYPE) -> DialogHistoryManager:
    manager = context.application.bot_data.get(HISTORY_MANAGER_KEY)
    assert isinstance(manager, DialogHistoryManager)
    return manager


async def handle_text_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Обработчик любых текстовых сообщений (кроме команд).

    1. Берём историю диалога пользователя.
    2. Добавляем текущее сообщение.
    3. Отправляем всё в LLM.
    4. Сохраняем ответ в историю.
    """
    if not update.effective_user or not update.effective_chat or not update.message:
        return

    user_id = update.effective_user.id
    username = update.effective_user.username or f"user_{user_id}"
    chat_id = update.effective_chat.id
    user_text = update.message.text or ""

    # Кнопка «Новый запрос» (reply) — сброс контекста без запроса к LLM
    if await handle_new_request_button(update, context, chat_id, user_id):
        return

    logger.info(f"Получено сообщение от {username} (ID: {user_id}): {user_text[:50]}...")

    history_manager = _get_history_manager(context)

    # Вся работа с историей — под одной блокировкой по user_id, чтобы нажатие
    # «Новый запрос» не пересекалось с чтением/записью (гонка при concurrent_updates).
    async with history_manager.lock(user_id):
        history = history_manager.get_history(user_id)
        logger.info(f"📚 История диалога пользователя {user_id}: {len(history)} сообщений")

        if history:
            history_preview = [
                f"{msg['role']}: {msg['content'][:50]}..."
                for msg in history[-3:]
            ]
            logger.info(f"📝 Последние сообщения в истории: {history_preview}")
        else:
            logger.info(f"📝 История пуста, начинаем новый диалог")

        messages = history + [{"role": "user", "content": user_text}]
        logger.info(
            f"🚀 Отправка в LLM: {len(messages)} сообщений "
            f"(история: {len(history)}, новое сообщение пользователя: 1)"
        )

        try:
            logger.debug(f"Отправка запроса к LLM API для пользователя {user_id}")
            reply_text = await chatgpt_service.generate_response(messages)
            logger.info(f"Получен ответ от LLM для пользователя {user_id}: {reply_text[:50]}...")
        except Exception as exc:  # noqa: BLE001
            logger.error(
                f"Ошибка при обращении к LLM API для пользователя {user_id}: {exc}",
                exc_info=True,
            )
            await context.bot.send_message(
                chat_id=chat_id,
                text="Произошла ошибка при обращении к сервису ChatGPT. Попробуйте позже.",
                reply_markup=get_new_request_keyboard(),
            )
            return

        history_manager.add_message(user_id, role="user", content=user_text)
        history_manager.add_message(user_id, role="assistant", content=reply_text)

        saved_history = history_manager.get_history(user_id)
        logger.info(
            f"✅ Сообщения сохранены в историю для пользователя {user_id}. "
            f"Теперь в истории: {len(saved_history)} сообщений "
            f"(было: {len(history)}, добавили: 2)"
        )

    await context.bot.send_message(
        chat_id=chat_id,
        text=reply_text,
        reply_markup=get_new_request_keyboard(),
    )

