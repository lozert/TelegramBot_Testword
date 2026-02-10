# Telegram ChatGPT Bot

Telegram бот с интеграцией ChatGPT/LLM API, поддерживающий историю диалогов и контекстные ответы.

---

**При сдаче задания обязательно указать в чат:**
- **Никнейм бота** (например, `@YourBotName`)
- **Ссылку на GitHub** (например, `https://github.com/username/zabota`)

Если указано что-то одно (только ссылка или только никнейм), задание считается выполненным неправильно.

---

## Функциональность

- Обработка команд `/start` и `/help`
- Генерация ответов через ChatGPT API
- Сохранение истории диалогов
- Использование контекста предыдущих сообщений
- Сброс контекста по команде `/start` или кнопке "Новый запрос"

## Структура проекта

```
.
├── main.py                 # Точка входа
├── bot/
│   ├── __init__.py
│   ├── handlers/          # Обработчики команд и сообщений
│   │   ├── __init__.py
│   │   ├── commands.py    # Обработчики команд (/start, /help)
│   │   └── messages.py    # Обработчик текстовых сообщений
│   ├── services/          # Сервисы
│   │   ├── __init__.py
│   │   ├── chatgpt.py     # Клиент ChatGPT API
│   │   └── history.py     # Менеджер истории диалогов
│   └── models/            # Модели данных
│       ├── __init__.py
│       └── dialog.py      # Модель диалога
├── config/
│   ├── __init__.py
│   └── settings.py        # Настройки и конфигурация
├── requirements.txt        # Зависимости Python
├── .env.example           # Пример переменных окружения
└── README.md              # Документация
```

## Установка

1. Установите зависимости (Poetry):
```bash
poetry install
```

2. Создайте файл `.env` на основе `.env.example` и заполните переменные:
- `TELEGRAM_BOT_TOKEN` — токен бота от @BotFather
- `LLM_API_URL` — URL API (например, OpenRouter или OpenAI)
- `LLM_API_KEY` — API ключ
- `LLM_MODEL` — модель (например, `gpt-3.5-turbo` или модель OpenRouter)

3. Запустите бота:
```bash
poetry run python main.py
```

## Конфигурация

Настройки в `.env`:
- `TELEGRAM_BOT_TOKEN` — токен бота от @BotFather
- `LLM_API_URL`, `LLM_API_KEY`, `LLM_MODEL` — параметры LLM API (ChatGPT/OpenRouter и т.п.)
- `LOG_LEVEL` — уровень логов (по умолчанию: INFO)
