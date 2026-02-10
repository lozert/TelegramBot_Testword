# Telegram ChatGPT Bot (Zabota)

Telegram-бот с интеграцией LLM API (ChatGPT/OpenRouter и др.): история диалогов в памяти, контекстные ответы, сброс контекста по команде или кнопке.

---

**При сдаче задания обязательно указать в чат:**
- **Никнейм бота** (например, `@YourBotName`)
- **Ссылку на GitHub** (например, `https://github.com/username/zabota`)

Если указано что-то одно (только ссылка или только никнейм), задание считается выполненным неправильно.

---

## Функциональность

- Команды `/start` и `/help`
- Ответы через LLM API (OpenAI-совместимый, в т.ч. OpenRouter)
- История диалогов в памяти с ограничением по длине (последние N сообщений)
- Контекст предыдущих сообщений при каждом запросе
- Сброс контекста: `/start` или кнопка **«Новый запрос»** на reply-клавиатуре (внизу экрана)

## Структура проекта

```
.
├── main.py                 # Точка входа, сборка Application и polling
├── bot/
│   ├── handlers/
│   │   ├── commands.py     # /start, /help, reply-клавиатура «Новый запрос»
│   │   └── messages.py     # Текст (в т.ч. нажатие кнопки) → LLM и история
│   ├── services/
│   │   ├── chatgpt.py      # Клиент LLM API (httpx)
│   │   └── history.py      # Менеджер истории диалогов (in-memory, блокировки по user_id)
│   └── models/
│       └── dialog.py       # Модель диалога (типы сообщений)
├── config/
│   └── settings.py        # Настройки из .env (Pydantic Settings)
├── alembic.ini            # Конфиг Alembic (миграции БД — зарезервировано)
├── alembic/
│   └── env.py             # Окружение Alembic
├── pyproject.toml         # Зависимости (Poetry)
├── .env.example            # Пример переменных окружения
├── run.bat                 # Запуск через Poetry (Windows)
└── README.md
```

## Установка

1. Установить зависимости (Poetry):
   ```bash
   poetry install
   ```

2. Создать `.env` по образцу `.env.example` и задать:
   - `TELEGRAM_BOT_TOKEN` — токен от @BotFather
   - `LLM_API_URL` — URL API (OpenRouter, OpenAI и т.п.)
   - `LLM_API_KEY` — API-ключ
   - `LLM_MODEL` — модель (например, `gpt-3.5-turbo` или модель OpenRouter)
   - при необходимости: `DATABASE_URL`, `LOG_LEVEL`

3. Запуск:
   ```bash
   poetry run python main.py
   ```
   Или через `run.bat` (Windows): активирует окружение и запускает бота.

## Конфигурация (.env)

| Переменная           | Описание |
|----------------------|----------|
| `TELEGRAM_BOT_TOKEN` | Токен бота (обязательно) |
| `LLM_API_URL`        | URL chat-completions API |
| `LLM_API_KEY`        | API-ключ |
| `LLM_MODEL`          | Имя модели |
| `DATABASE_URL`       | Подключение к БД (по умолчанию `sqlite:///./db.sqlite3`) |
| `LOG_LEVEL`          | Уровень логов (по умолчанию `INFO`) |

## Архитектура (кратко)

- **Обработчики:** команды в `commands.py`, все текстовые сообщения (включая нажатие «Новый запрос») в `messages.py`.
- **Кнопка «Новый запрос»:** обычная reply-клавиатура (`ReplyKeyboardMarkup`). Нажатие отправляет текст «Новый запрос» и обрабатывается в `handle_text_message` через `handle_new_request_button` — сброс истории без вызова LLM.
- **История:** один `DialogHistoryManager` в `application.bot_data`, блокировка по `user_id` (asyncio.Lock) для устранения гонок при `concurrent_updates=True`.

Подробнее — в [ARCHITECTURE.md](ARCHITECTURE.md).
