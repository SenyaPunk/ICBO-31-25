import logging
import os
from typing import Literal
import httpx

logger = logging.getLogger(__name__)


class TextGenerator:
    def __init__(self, api_url: str = None, api_key: str = None):
        self.api_url = api_url or os.environ.get("WISPBYTE_API_URL")
        self.api_key = api_key or os.environ.get("WISPBYTE_API_KEY")
        
        if not self.api_url:
            logger.error("WISPBYTE_API_URL не настроен в переменных окружения")
        if not self.api_key:
            logger.error("WISPBYTE_API_KEY не настроен в переменных окружения")
        
        if self.api_url and self.api_key:
            logger.info("TextGenerator настроен для работы с wispbyte API: %s", self.api_url)
        else:
            logger.warning("TextGenerator не полностью настроен - некоторые функции не будут работать")

    def generate_greeting(self, kind: Literal["morning", "evening"]) -> str:
        if not self.api_url or not self.api_key:
            logger.error("API URL или API Key не настроены")
            return self._get_fallback_text(kind)
        
        try:
            logger.info("Отправка запроса на генерацию текста (%s) к wispbyte API", kind)
            
            headers = {
                "X-API-Key": self.api_key,
                "Content-Type": "application/json"
            }
            
            payload = {
                "type": kind,
                "model": "gemini-2.0-flash-exp"
            }
            
            with httpx.Client(timeout=30.0) as client:
                response = client.post(
                    f"{self.api_url}/generate",
                    json=payload,
                    headers=headers
                )
                
                if response.status_code != 200:
                    logger.error(
                        "Ошибка от wispbyte API: %d - %s",
                        response.status_code,
                        response.text
                    )
                    return self._get_fallback_text(kind)
                
                data = response.json()
                
                if not data.get("success"):
                    logger.error("API вернул ошибку: %s", data.get("error"))
                    return self._get_fallback_text(kind)
                
                generated_text = data.get("text", "").strip()
                
                if not generated_text:
                    logger.warning("Получен пустой текст от API")
                    return self._get_fallback_text(kind)
                
                logger.info("Текст успешно получен от wispbyte API (%d символов)", len(generated_text))
                return generated_text
                
        except httpx.TimeoutException:
            logger.error("Таймаут при запросе к wispbyte API")
            return self._get_fallback_text(kind)
        except httpx.RequestError as e:
            logger.error("Ошибка сети при запросе к wispbyte API: %s", e)
            return self._get_fallback_text(kind)
        except Exception as e:
            logger.exception("Непредвиденная ошибка при генерации текста: %s", e)
            return self._get_fallback_text(kind)

    def _get_fallback_text(self, kind: Literal["morning", "evening"]) -> str:
        if kind == "morning":
            return "Доброе утро, ИКБО-31-25! Пусть день будет продуктивным! 🌅"
        else:
            return "Спокойной ночи, ИКБО-31-25! Сладких снов! 🌙"
