"""
Менеджер истории диалогов пользователей.

Пока реализован как in-memory хранилище:
user_id -> список сообщений формата {"role": "...", "content": "..."}.

При желании это можно перенести в БД (SQLAlchemy + Alembic).
"""

import asyncio
from collections import defaultdict
from typing import DefaultDict, Dict, List, TypedDict


class DialogMessage(TypedDict):
    role: str
    content: str


class DialogHistoryManager:
    """
    Менеджер истории диалогов.

    Хранит историю в памяти процесса. При перезапуске бота история сбрасывается,
    что допустимо для тестового задания.

    Использует блокировку по user_id, чтобы при concurrent_updates=True
    не было гонки между нажатием «Новый запрос» и обработкой текстового сообщения.
    """

    def __init__(self, max_messages_per_user: int = 30) -> None:
        self._storage: DefaultDict[int, List[DialogMessage]] = defaultdict(list)
        self._max_messages_per_user = max_messages_per_user
        self._locks: Dict[int, asyncio.Lock] = {}

    def _get_lock(self, user_id: int) -> asyncio.Lock:
        if user_id not in self._locks:
            self._locks[user_id] = asyncio.Lock()
        return self._locks[user_id]

    def lock(self, user_id: int) -> asyncio.Lock:
        """
        Блокировка по user_id для атомарных операций с историей.
        Использование: async with history_manager.lock(user_id): ...
        """
        return self._get_lock(user_id)

    def get_history(self, user_id: int) -> List[DialogMessage]:
        """
        Вернуть копию истории диалога пользователя.
        
        Возвращает список сообщений в формате:
        [{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}, ...]
        """
        return list(self._storage[user_id])

    def add_message(self, user_id: int, role: str, content: str) -> None:
        """
        Добавить сообщение в историю с ограничением по длине.
        
        :param user_id: ID пользователя
        :param role: роль сообщения ("user" или "assistant")
        :param content: содержимое сообщения
        """
        messages = self._storage[user_id]
        messages.append(DialogMessage(role=role, content=content))

        # Обрезаем историю, чтобы не раздувать контекст
        if len(messages) > self._max_messages_per_user:
            overflow = len(messages) - self._max_messages_per_user
            del messages[0:overflow]

    def clear_history(self, user_id: int) -> None:
        """Полностью очистить историю пользователя."""
        self._storage[user_id].clear()

    def reset_context(self, user_id: int) -> None:
        """Синоним для clear_history — сброс контекста диалога."""
        self.clear_history(user_id)

