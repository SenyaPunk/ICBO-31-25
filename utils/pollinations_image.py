import logging
import urllib.parse
import requests
import random  

logger = logging.getLogger(__name__)


class PollinationsImageAPI:
  
    
    def __init__(
        self, 
        base_url: str = "https://pollinations.ai/p/",
        width: int = 1024,
        height: int = 1024,
        model: str = "flux",
        enhance: bool = True,
        nologo: bool = True
    ):
        self.base_url = base_url
        self.width = width
        self.height = height
        self.model = model
        self.enhance = enhance
        self.nologo = nologo
        logger.info(f"PollinationsImageAPI инициализирован (размер: {width}x{height}, модель: {model})")

    def generate_image_bytes(self, prompt: str, timeout: int = 120) -> bytes | None:
     
        try:
            encoded_prompt = urllib.parse.quote(prompt)
            
            url = f"{self.base_url}{encoded_prompt}"
            params = {
                "width": self.width,
                "height": self.height,
                "model": self.model,
                "enhance": str(self.enhance).lower(),
                "nologo": str(self.nologo).lower(),
                "seed": random.randint(1, 1000000)  
            }
            
            logger.info(f"Запрос изображения от Pollinations.ai: {prompt[:50]}...")
            logger.debug(f"URL: {url}, параметры: {params}")
            
            response = requests.get(url, params=params, timeout=timeout)
            
            if response.status_code != 200:
                logger.error(f"Ошибка от Pollinations.ai: {response.status_code}")
                return None
            
            image_bytes = response.content
            
            if not image_bytes or len(image_bytes) < 100:
                logger.error("Получено пустое или слишком маленькое изображение")
                return None
            
            logger.info(f"Изображение успешно получено ({len(image_bytes)} байт)")
            return image_bytes
            
        except requests.exceptions.Timeout:
            logger.error(f"Превышено время ожидания ({timeout} сек) при запросе к Pollinations.ai")
            return None
        except requests.exceptions.RequestException as e:
            logger.error(f"Ошибка сети при запросе к Pollinations.ai: {e}")
            return None
        except Exception as e:
            logger.error(f"Неожиданная ошибка при генерации изображения: {e}", exc_info=True)
            return None
