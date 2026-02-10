"""
Точка входа для Telegram ChatGPT бота.

Запускает python-telegram-bot, настраивает хендлеры и менеджер истории диалогов.
"""

import logging
import sys

from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from bot.handlers.commands import (
    HISTORY_MANAGER_KEY,
    help_command,
    start,
)
from bot.handlers.messages import handle_text_message
from bot.services.history import DialogHistoryManager
from config.settings import get_settings


def setup_logging(log_level: str = "INFO") -> None:
    """
    Настройка логирования для всего приложения.

    :param log_level: уровень логирования (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    level = getattr(logging, log_level.upper(), logging.INFO)

    # Формат логов: время, имя модуля, уровень, сообщение
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    date_format = "%Y-%m-%d %H:%M:%S"

    logging.basicConfig(
        format=log_format,
        datefmt=date_format,
        level=level,
        stream=sys.stdout,
    )

    # Настройка логирования для библиотеки python-telegram-bot
    logging.getLogger("telegram").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)

    logger = logging.getLogger(__name__)
    logger.info(f"Логирование настроено. Уровень: {log_level}")


async def _on_startup(application: Application) -> None:
    """
    Хук, который вызывается при старте приложения.

    Здесь мы инициализируем общий менеджер истории диалогов.
    """
    logger = logging.getLogger(__name__)
    logger.info("Инициализация менеджера истории диалогов")
    application.bot_data[HISTORY_MANAGER_KEY] = DialogHistoryManager()
    logger.info("Бот успешно запущен и готов к работе")


def build_application() -> Application:
    """
    Создать и сконфигурировать экземпляр Telegram Application.
    """
    settings = get_settings()

    application = (
        Application.builder()
        .token(settings.telegram_bot_token)
        .concurrent_updates(True)
        .post_init(_on_startup)
        .build()
    )

    # Команды
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))

    # Текстовые сообщения (в т.ч. нажатие кнопки «Новый запрос» на reply-клавиатуре)
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_message)
    )

    return application


def main() -> None:
    """Синхронная точка входа, делегирует управление PTB."""
    settings = get_settings()
    setup_logging(settings.log_level)

    logger = logging.getLogger(__name__)
    logger.info("Запуск Telegram ChatGPT бота...")

    application = build_application()
    logger.info("Бот запущен, ожидание сообщений...")
    application.run_polling()


if __name__ == "__main__":
    main()

