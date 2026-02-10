# Архитектура Telegram ChatGPT Bot (Zabota)

## Обзор

Модульная структура: точка входа, обработчики команд и сообщений, сервисы (LLM, история), конфигурация из `.env`. История диалогов — in-memory с блокировками по пользователю.

## Компоненты

### 1. Точка входа (`main.py`)

- Настройка логирования, загрузка настроек через `get_settings()`.
- Сборка `Application`: токен, `concurrent_updates=True`, `post_init` для инициализации менеджера истории.
- Регистрация обработчиков:
  - `CommandHandler("start", start)` и `CommandHandler("help", help_command)`.
  - `MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_message)` — все текстовые сообщения (в т.ч. нажатие кнопки «Новый запрос»).
- Запуск через `application.run_polling()`.

### 2. Обработчики (`bot/handlers/`)

#### `commands.py`

- **`start`** — команда `/start`:
  - Сброс истории пользователя (`reset_context(user_id)`).
  - Приветствие и отправка reply-клавиатуры с кнопкой «Новый запрос».

- **`help_command`** — команда `/help`: справка по командам и кнопке.

- **`get_new_request_keyboard()`** — возвращает `ReplyKeyboardMarkup` с одной кнопкой «Новый запрос» (`resize_keyboard=True`). Кнопка не inline: при нажатии пользователь отправляет обычное текстовое сообщение с этим текстом.

- **`handle_new_request_button(update, context, chat_id, user_id)`** — если текст сообщения совпадает с текстом кнопки:
  - Очищает историю пользователя под блокировкой.
  - Отправляет подтверждение и снова показывает reply-клавиатуру.
  - Возвращает `True` (обработка «кнопки» выполнена), иначе `False`.

#### `messages.py`

- **`handle_text_message`** — обработка любого текстового сообщения (кроме команд):
  1. Вызов `handle_new_request_button(...)`; при возврате `True` — выход (сброс контекста уже выполнен).
  2. Получение истории пользователя под блокировкой `history_manager.lock(user_id)`.
  3. Формирование списка сообщений для LLM (история + текущее сообщение пользователя).
  4. Запрос к LLM, сохранение пары (user, assistant) в историю (всё в той же блокировке).
  5. Отправка ответа пользователю с reply-клавиатурой «Новый запрос».

### 3. Сервисы (`bot/services/`)

#### `chatgpt.py`

- **`ChatGPTService`** — HTTP-клиент к LLM API (httpx).
- **`generate_response(messages)`** — POST на `llm_api_url` с телом `{ "model": ..., "messages": ... }`, возвращает текст ответа ассистента. Настройки (`llm_api_url`, `llm_api_key`, `llm_model`) из `config.settings`.

#### `history.py`

- **`DialogHistoryManager`**:
  - Хранилище: `defaultdict(int -> list[DialogMessage])`, лимит длины истории на пользователя (`max_messages_per_user`, по умолчанию 30).
  - **`lock(user_id)`** — возвращает `asyncio.Lock` для данного пользователя; используется для атомарности операций при параллельной обработке апдейтов.
  - **`get_history(user_id)`**, **`add_message(user_id, role, content)`**, **`clear_history(user_id)`**, **`reset_context(user_id)`** — синхронные методы, вызываемые только внутри `async with manager.lock(user_id)` в обработчиках.

### 4. Модели (`bot/models/`)

- Типы/структуры сообщений диалога (в т.ч. `DialogMessage` в `history.py`: `role`, `content`). Модели БД (SQLAlchemy) и миграции Alembic зарезервированы под персистентное хранение.

### 5. Конфигурация (`config/`)

- **`settings.py`** — Pydantic Settings, чтение из `.env`:
  - `telegram_bot_token`, `llm_api_url`, `llm_api_key`, `llm_model`, `database_url`, `debug`, `environment`, `log_level`.
- Доступ к настройкам: `get_settings()` (кеширование через `lru_cache`).

## Потоки данных

### Команда /start

```
Пользователь → /start
    → commands.start()
    → history_manager.reset_context(user_id)
    → Отправка приветствия + ReplyKeyboardMarkup «Новый запрос»
```

### Текстовое сообщение (обычный запрос к LLM)

```
Пользователь → текст (не «Новый запрос»)
    → messages.handle_text_message()
    → handle_new_request_button() → False
    → async with history_manager.lock(user_id):
          history = get_history(user_id)
          messages = history + [user_message]
          reply_text = chatgpt_service.generate_response(messages)
          add_message(user), add_message(assistant)
    → Отправка reply_text + reply-клавиатура
```

### Сброс контекста (кнопка «Новый запрос»)

```
Пользователь → нажатие кнопки «Новый запрос» (отправляется текст «Новый запрос»)
    → messages.handle_text_message()
    → handle_new_request_button() → True
          async with history_manager.lock(user_id): clear_history(user_id)
          Отправка «История удалена…» + reply-клавиатура
    → return (запрос к LLM не выполняется)
```

## Структура истории

Сообщения в формате `{"role": "user" | "assistant", "content": "текст"}`. История хранится в памяти; при перезапуске бота теряется. Ограничение длины на пользователя — последние N сообщений (по умолчанию 30).

## Зависимости

- **python-telegram-bot** — Telegram Bot API, обработчики, фильтры.
- **httpx** — асинхронные запросы к LLM API (в коде используется в `chatgpt.py`).
- **pydantic-settings** — загрузка конфигурации из `.env`.
- **python-dotenv** — поддержка `.env`.
- **SQLAlchemy**, **alembic** — зарезервированы под БД.

## Особенности реализации

1. **Reply-клавиатура вместо inline** — кнопка «Новый запрос» не использует callback; нажатие отправляет текст, обрабатывается в общем обработчике сообщений.
2. **Блокировки по user_id** — при `concurrent_updates=True` операции с историей выполняются под `asyncio.Lock` по пользователю, чтобы сброс контекста и обработка следующего сообщения не пересекались.
3. **Один менеджер истории** — экземпляр `DialogHistoryManager` создаётся в `post_init` и хранится в `application.bot_data[HISTORY_MANAGER_KEY]`.

## Возможные улучшения

- Персистентное хранение истории (SQLite/PostgreSQL) и миграции Alembic.
- Rate limiting, ограничение длины контекста в токенах.
- Логирование запросов/ответов, поддержка нескольких языков, медиа.
