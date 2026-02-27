import logging
import requests
import random
import time
from typing import Optional

logger = logging.getLogger(__name__)

THECATAPI_KEY = None
UNSPLASH_ACCESS_KEY = None 
PEXELS_API_KEY = None        

class PollinationsImageAPI:
    def __init__(self,
                 source: str = "thecatapi", 
                 unsplash_key: Optional[str] = None,
                 pexels_key: Optional[str] = None,
                 thecatapi_key: Optional[str] = None,
                 timeout: int = 20):
        self.source = source
        self.timeout = timeout
        self.unsplash_key = unsplash_key
        self.pexels_key = pexels_key
        self.thecatapi_key = thecatapi_key

    def _download_bytes(self, url: str, max_retries: int = 3):
        for attempt in range(max_retries):
            try:
                logger.info(f"Downloading image from {url} (attempt {attempt+1})")

                with requests.get(
                    url,
                    timeout=(5, 10),  
                    stream=True
                ) as resp:

                    if resp.status_code != 200:
                        logger.warning(f"HTTP {resp.status_code}")
                        continue

                    chunks = []
                    for chunk in resp.iter_content(chunk_size=8192):
                        if chunk:
                            chunks.append(chunk)

                    return b"".join(chunks)

            except requests.exceptions.ReadTimeout:
                logger.warning("Read timeout, retrying...")
            except Exception as e:
                logger.exception("Download error: %s", e)

        return None

    def _fetch_from_thecatapi(self, limit: int = 5) -> Optional[bytes]:
        url = "https://api.thecatapi.com/v1/images/search"
        headers = {}
        if self.thecatapi_key:
            headers["x-api-key"] = self.thecatapi_key
        params = {"limit": limit}
        try:
            r = requests.get(url, params=params, headers=headers, timeout=self.timeout)
            if r.status_code != 200:
                logger.warning("TheCatAPI returned %s", r.status_code)
                return None
            data = r.json()
            if not data:
                return None
            img_url = random.choice(data).get("url")
            if img_url:
                return self._download_bytes(img_url)
        except Exception as e:
            logger.exception("TheCatAPI error: %s", e)
        return None

    def _fetch_from_unsplash(self, query: str = "cat morning", per_page: int = 10) -> Optional[bytes]:
        if not self.unsplash_key:
            logger.warning("Unsplash API key not provided")
            return None
        search_url = "https://api.unsplash.com/search/photos"
        headers = {"Accept-Version": "v1", "Authorization": f"Client-ID {self.unsplash_key}"}
        params = {"query": query, "per_page": per_page}
        try:
            r = requests.get(search_url, headers=headers, params=params, timeout=self.timeout)
            if r.status_code != 200:
                logger.warning("Unsplash API returned %s", r.status_code)
                return None
            resp = r.json()
            results = resp.get("results", [])
            if not results:
                return None
            img_url = random.choice(results).get("urls", {}).get("regular")
            if img_url:
                return self._download_bytes(img_url)
        except Exception as e:
            logger.exception("Unsplash error: %s", e)
        return None

    def _fetch_from_pexels(self, query: str = "cat morning", per_page: int = 15) -> Optional[bytes]:
        if not self.pexels_key:
            logger.warning("Pexels API key not provided")
            return None
        url = "https://api.pexels.com/v1/search"
        headers = {"Authorization": self.pexels_key}
        params = {"query": query, "per_page": per_page}
        try:
            r = requests.get(url, headers=headers, params=params, timeout=self.timeout)
            if r.status_code != 200:
                logger.warning("Pexels API returned %s", r.status_code)
                return None
            js = r.json()
            photos = js.get("photos", [])
            if not photos:
                return None
            img_url = random.choice(photos).get("src", {}).get("large")
            if img_url:
                return self._download_bytes(img_url)
        except Exception as e:
            logger.exception("Pexels error: %s", e)
        return None

    def generate_image_bytes(self, prompt: str, timeout: int = 20, max_retries: int = 3):

        if "morning" in prompt.lower():
            return self.get_cat_image_bytes("morning")
        elif "evening" in prompt.lower() or "night" in prompt.lower():
            return self.get_cat_image_bytes("evening")
        else:
            return self.get_cat_image_bytes("morning")
        
    def get_cat_image_bytes(self, time_of_day: str = "morning") -> Optional[bytes]:
        queries = {
            "morning": ["cat morning", "kitten sunrise", "cat sunrise", "cat morning light"],
            "evening": ["cat evening", "cat sunset", "cat twilight", "cat dusk", "cat night"],
            "night": ["cat night", "nocturnal cat", "cat moonlight"]
        }
        q_list = queries.get(time_of_day.lower(), [f"cat {time_of_day}", "cat"])

        if self.source == "thecatapi":
            return self._fetch_from_thecatapi(limit=5)

        for q in q_list:
            if self.source == "unsplash":
                img = self._fetch_from_unsplash(query=q, per_page=12)
            elif self.source == "pexels":
                img = self._fetch_from_pexels(query=q, per_page=12)
            else:
                img = None

            if img:
                return img
            time.sleep(0.5 + random.random() * 0.5)



        logger.info("Falling back to TheCatAPI")
        return self._fetch_from_thecatapi(limit=3)

