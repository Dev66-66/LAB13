import asyncio
import logging

import google.generativeai as genai

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = (
    "Ты юридический помощник. Отвечай на русском языке. "
    "Используй предоставленные правовые нормы. "
    "В конце ВСЕГДА добавляй дословно: "
    "Disclaimer: данный ответ носит информационный характер "
    "и не является юридической консультацией."
)


class GeminiClient:
    """Клиент для взаимодействия с Gemini API."""

    def __init__(self, api_key: str) -> None:
        """Конфигурирует google-generativeai и создаёт модель gemini-1.5-flash."""
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(
            "gemini-1.5-flash",
            system_instruction=_SYSTEM_PROMPT,
        )

    async def generate_legal_answer(self, query: str, documents: list[str]) -> str:
        """
        Генерирует юридический ответ на основе запроса и списка документов.
        При ошибке выполняет 3 попытки повтора с задержками 1s, 2s, 4s.
        При полном отказе возвращает шаблонный ответ с перечнем документов.
        """
        docs_text = "\n".join(f"- {doc}" for doc in documents)
        prompt = f"Запрос: {query}\n\nДокументы:\n{docs_text}"

        last_error: Exception | None = None
        for attempt, delay in enumerate([0, 1, 2, 4]):
            if delay:
                await asyncio.sleep(delay)
            try:
                response = await asyncio.to_thread(self.model.generate_content, prompt)
                return response.text
            except Exception as exc:
                last_error = exc
                logger.warning("Gemini API attempt %d/4 failed: %s", attempt + 1, exc)

        logger.error("Gemini API failed after all retries: %s", last_error)
        return (
            f"На основе предоставленных документов:\n{docs_text}\n\n"
            "Disclaimer: данный ответ носит информационный характер "
            "и не является юридической консультацией."
        )
