"""
Сервис для работы с LLM (ChatGPT / OpenRouter совместимый API).

Ожидается, что конфиг предоставляет:
- settings.llm_api_url
- settings.llm_api_key
- settings.llm_model
"""

import logging
from typing import List, Mapping

import httpx

from config.settings import get_settings

logger = logging.getLogger(__name__)


class ChatGPTService:
    """Клиент для вызова chat-completions API."""

    def __init__(self) -> None:
        self._settings = get_settings()

    async def generate_response(self, messages: List[Mapping[str, str]]) -> str:
        """
        Вызвать LLM, передав историю диалога.

        :param messages: список сообщений формата
            {"role": "user" | "assistant" | "system", "content": "..."}
        :return: контент ответа ассистента
        """
        logger.info(
            f"Запрос к LLM API: модель={self._settings.llm_model}, "
            f"количество сообщений в контексте={len(messages)}"
        )
        
        # Логируем структуру сообщений для отладки
        if messages:
            preview = [
                f"{msg.get('role', 'unknown')}: {str(msg.get('content', ''))[:30]}..."
                for msg in messages
            ]
            logger.debug(f"Структура сообщений для API: {preview}")

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    self._settings.llm_api_url,
                    headers={
                        "Authorization": f"Bearer {self._settings.llm_api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": self._settings.llm_model,
                        "messages": messages,
                    },
                )
                response.raise_for_status()

                data = response.json()
                content = data["choices"][0]["message"]["content"]

                logger.debug(f"Успешный ответ от LLM API, длина: {len(content)} символов")
                return content
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP ошибка при запросе к LLM API: {e.response.status_code} - {e.response.text}")
            raise
        except httpx.RequestError as e:
            logger.error(f"Ошибка сети при запросе к LLM API: {e}")
            raise
        except Exception as e:
            logger.error(f"Неожиданная ошибка при запросе к LLM API: {e}", exc_info=True)
            raise


# Singleton-инстанс сервиса, который можно переиспользовать в хендлерах
chatgpt_service = ChatGPTService()

