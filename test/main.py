import requests
import io
import os
import time
from PIL import Image

# Вставь свой токен от Hugging Face
HF_TOKEN = ...

# НОВЫЙ АДРЕС (Router API)
# Мы указываем модель прямо в пути после /models/
# Используем SCHNELL, но через правильный эндпоинт
API_URL = "https://router.huggingface.co/hf-inference/models/black-forest-labs/FLUX.1-schnell"
headers = {"Authorization": f"Bearer {HF_TOKEN}"}

def generate_hq_cat(prompt_subject, folder="mirea_cats"):
    if not os.path.exists(folder):
        os.makedirs(folder)
        
    # Секрет успеха: четкая инструкция для текста в начале
    # Мы буквально говорим модели: 'Начни с текста'
    clean_prompt = (
        f"A high-quality photo of {prompt_subject}. "
        "The hoodie has a large white text 'RTU MIREA' printed on it. "
        "The text is 'R' 'T' 'U' ' ' 'M' 'I' 'R' 'E' 'A'. " # Подсказка по буквам
        "Typography: bold sans-serif font, straight lines, no extra characters, correct spelling. "
        "Focus on the word 'MIREA' on the chest."
    )
    
    payload = {
        "inputs": clean_prompt,
        "parameters": {
            "num_inference_steps": 4, # Для schnell это максимум
            "guidance_scale": 3.5
        }
    }
    
    print(f"📡 Запрос отправлен... Ждем фото...")
    
    try:
        response = requests.post(API_URL, headers=headers, json=payload)
        
        if response.status_code == 503:
            print("⏳ Модель спит, просыпается... (20 сек)")
            time.sleep(20)
            return generate_hq_cat(prompt_subject, folder)

        if response.status_code == 200:
            image = Image.open(io.BytesIO(response.content))
            path = os.path.join(folder, f"cat_{int(time.time())}.png")
            image.save(path)
            print(f"✅ Готово! Текст должен быть четким: {path}")
        else:
            print(f"❌ Ошибка {response.status_code}: {response.text}")
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")

# Запуск с коротким и ясным описанием объекта
generate_hq_cat("a ginger cat student wearing a blue hoodie")