import logging
import requests
import random
import time
import os

logger = logging.getLogger(__name__)

HF_TOKEN = os.getenv("HF_TOKEN")

class PollinationsImageAPI:

    def __init__(
        self,
        base_url: str = "https://router.huggingface.co/hf-inference/models/black-forest-labs/FLUX.1-schnell",
        width: int = 1024,
        height: int = 1024,
        model: str = "flux-schnell", 
        enhance: bool = True,
        nologo: bool = True
    ):
        self.base_url = base_url
        self.headers = {"Authorization": f"Bearer {HF_TOKEN}"}
        self.width = width
        self.height = height
        logger.info(f"HuggingFaceImageAPI initialized (Target: FLUX.1-schnell)")

    def _construct_hq_prompt(self, raw_prompt: str) -> str:

        
        scenarios = [
            {
                "context": "wearing a dark blue university hoodie",
                "text_pos": "printed on the hoodie chest",
                "color": "white"
            },
            {
                "context": "wearing a white oversized t-shirt",
                "text_pos": "printed on the t-shirt",
                "color": "deep blue"
            },
            {
                "context": "wearing a stylish blue scarf and glasses",
                "text_pos": "embroidered on the scarf",
                "color": "white"
            },
            {
                "context": "sitting next to a white ceramic coffee mug",
                "text_pos": "printed on the mug surface",
                "color": "blue"
            },
            {
                "context": "sitting on a pile of books with a blue notebook",
                "text_pos": "printed on the notebook cover",
                "color": "white"
            },
            {
                "context": "sitting next to a student backpack",
                "text_pos": "on the backpack patch",
                "color": "white"
            },
            {
                "context": "working at a desk with a modern laptop open",
                "text_pos": "displayed brightly on the laptop screen as a wallpaper",
                "color": "white"
            },
            {
                "context": "holding a modern tablet",
                "text_pos": "on the tablet screen",
                "color": "blue"
            }
        ]

        backgrounds = [
            "university library with books",
            "cozy dorm room with fairy lights",
            "futuristic cyber-lab with neon",
            "sunny campus park",
            "minimalist study desk"
        ]

        scene = random.choice(scenarios)
        bg = random.choice(backgrounds)

        
        clean_prompt = (
            f"A high-quality photo of a cute fluffy cat {scene['context']}, {raw_prompt}. "
            f"Background: {bg}. "
            f"The image features a clear 'RTU MIREA' logo {scene['text_pos']}. "
            f"The text is '{scene['color']}', bold, sans-serif font. "
            "The text spells: 'R' 'T' 'U' ' ' 'M' 'I' 'R' 'E' 'A'. "
            "Focus on the cat and the text. Sharp focus, cinematic lighting, 8k, photorealistic."
        )
        return clean_prompt

    def generate_image_bytes(self, prompt: str, timeout: int = 60, max_retries: int = 5) -> bytes | None:
        final_prompt = self._construct_hq_prompt(prompt)
        
        attempt = 0
        while attempt < max_retries:
            attempt += 1
            
            payload = {
                "inputs": final_prompt,
                "parameters": {
                    "num_inference_steps": 4, 
                    "guidance_scale": 3.5,
                    "width": self.width,
                    "height": self.height
                }
            }
            
            try:
                logger.info(f"Image attempt={attempt}. Prompt: {final_prompt[:80]}...")
                
                resp = requests.post(
                    self.base_url, 
                    headers=self.headers, 
                    json=payload, 
                    timeout=timeout
                )
                
                if resp.status_code == 503:
                    wait_time = 20
                    logger.warning(f"Model is loading (503). Sleeping {wait_time}s...")
                    time.sleep(wait_time)
                    continue 
                
                if resp.status_code != 200:
                    logger.warning(f"HF Error {resp.status_code}")
                    if resp.status_code in [400, 401, 403, 410]:
                        return None
                else:
                    if len(resp.content) > 1000:
                        return resp.content

                backoff = (2 ** attempt) + random.uniform(0, 1)
                time.sleep(backoff)

            except Exception as e:
                logger.exception(f"Error: {e}")
                time.sleep(2)

        return None