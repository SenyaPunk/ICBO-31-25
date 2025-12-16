import logging
import os
from typing import Literal
import requests

logger = logging.getLogger(__name__)


class OpenRouterTextGenerator:
    
    def __init__(self, api_key: str = None, model: str = None):
        self.api_key = api_key or os.environ.get("OPENROUTER_API_KEY")
        self.model = model or os.environ.get("OPENROUTER_MODEL", "x-ai/grok-4.1-fast")
        self.api_url = "https://openrouter.ai/api/v1/chat/completions"
        
        if not self.api_key:
            logger.error("OPENROUTER_API_KEY не настроен в переменных окружения")
        else:
            logger.info(f"OpenRouterTextGenerator настроен с моделью: {self.model}")

    def generate_greeting(self, kind: Literal["morning", "evening"]) -> str:
        
        if not self.api_key:
            logger.error("OPENROUTER_API_KEY не настроен")
            return self._get_fallback_text(kind)
        
        try:
            logger.info(f"Генерация {kind} приветствия через Grok...")
            
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            prompt = self._get_prompt(kind)
            
            data = {
                "model": self.model,
                "messages": [
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.7,
                "max_tokens": 500
            }
            
            response = requests.post(
                self.api_url,
                headers=headers,
                json=data,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                generated_text = result["choices"][0]["message"]["content"].strip()
                
                if not generated_text:
                    logger.warning("Получен пустой текст от Grok")
                    return self._get_fallback_text(kind)
                
                logger.info(f"✅ Текст успешно сгенерирован ({len(generated_text)} символов)")
                return generated_text
            else:
                logger.error(f"Ошибка от OpenRouter API: {response.status_code} - {response.text}")
                return self._get_fallback_text(kind)
                
        except requests.exceptions.Timeout:
            logger.error("Таймаут при запросе к OpenRouter API")
            return self._get_fallback_text(kind)
        except requests.exceptions.RequestException as e:
            logger.error(f"Ошибка сети при запросе к OpenRouter API: {e}")
            return self._get_fallback_text(kind)
        except Exception as e:
            logger.exception(f"Непредвиденная ошибка при генерации текста: {e}")
            return self._get_fallback_text(kind)

    def _get_prompt(self, kind: Literal["morning", "evening"]) -> str:
        if kind == "morning":
            return (
                "Сгенерируй очень короткое и смешное пожелание доброго утра на русском языке "
                "для чата группы ИКБО-31-25 (1–3 предложения). Используй маты, черный юмор и "
                "смешной зумерский стиль. Важно: оставь только одно сообщение с пожеланием, "
                "не добавляй комментариев и тд. Лишь один текст сообщения! "
                "Стиль — дружелюбный, смешной, вдохновляющий, энергичный. Разрешено до двух уместных эмодзи"
            )
        else:  # evening
            return (
                "Сгенерируй очень короткое и смешное пожелание спокойной ночи на русском языке "
                "для чата группы ИКБО-31-25 (1–3 предложения). Используй маты, черный юмор и "
                "смешной зумерский стиль. Важно: оставь только одно сообщение с пожеланием, "
                "не добавляй комментариев и тд. Лишь один текст сообщения! "
                "Стиль — дружелюбный, смешной, расслабляющий, уютный. Разрешено до двух уместных эмодзи"
            )

    def _get_fallback_text(self, kind: Literal["morning", "evening"]) -> str:
        if kind == "morning":
            return "Доброе утро, ИКБО-31-25! Пусть день будет продуктивным! 🌅"
        else:
            return "Спокойной ночи, ИКБО-31-25! Сладких снов! 🌙"
