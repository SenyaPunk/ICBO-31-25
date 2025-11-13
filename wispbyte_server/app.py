from flask import Flask, request, jsonify
import os
import logging
from typing import Literal

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

from flask_cors import CORS
CORS(app)

API_KEY = os.environ.get("API_KEY", "your-secret-api-key-here")
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")

try:
    import google.generativeai as genai
    genai.configure(api_key=GOOGLE_API_KEY)
    logger.info("Google Gemini API успешно настроен")
except Exception as e:
    logger.error(f"Ошибка настройки Gemini: {e}")
    genai = None


def extract_text_from_response(resp) -> str:
    try:
        if resp is None:
            return ""
        
        if isinstance(resp, str):
            return resp.strip()
        
        if hasattr(resp, "text") and isinstance(getattr(resp, "text"), str):
            return getattr(resp, "text").strip()
        
        if hasattr(resp, "content") and isinstance(getattr(resp, "content"), str):
            return getattr(resp, "content").strip()
        
        if hasattr(resp, "candidates"):
            candidates = getattr(resp, "candidates")
            if isinstance(candidates, (list, tuple)) and len(candidates) > 0:
                first = candidates[0]
                if isinstance(first, dict):
                    for k in ("content", "output", "text"):
                        if k in first and first[k]:
                            return str(first[k]).strip()
                else:
                    for k in ("content", "output", "text"):
                        if hasattr(first, k):
                            val = getattr(first, k)
                            if isinstance(val, str):
                                return val.strip()
        
        return str(resp).strip()
    except Exception as e:
        logger.debug(f"Не удалось извлечь текст из ответа: {e}")
        return ""


def verify_api_key():
    auth_header = request.headers.get('X-API-Key')
    if not auth_header or auth_header != API_KEY:
        return False
    return True


@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({
        "status": "ok",
        "service": "Gemini Text Generator API",
        "gemini_configured": genai is not None
    })


@app.route('/generate', methods=['POST'])
def generate_text():
    if not verify_api_key():
        return jsonify({"error": "Unauthorized"}), 401
    
    if not genai:
        return jsonify({"error": "Gemini API not configured"}), 500
    
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400
        
        greeting_type = data.get("type", "morning")
        model_name = data.get("model", "gemini-2.0-flash-exp")
        
        if greeting_type not in ["morning", "evening"]:
            return jsonify({"error": "Invalid type. Must be 'morning' or 'evening'"}), 400
        
        if greeting_type == "morning":
            user_prompt = (
                "Сгенерируй очень короткое и смешное пожелание доброго утра "
                "на русском языке для чата Волки МИРЭА (1–2 предложения). "
                "Используй маты, черный юмор и смешной зумерский стиль. "
                "Важно: оставь только одно сообщение с пожеланием, не добавляй комментариев и тд. Лишь один текст сообщения! "
                "Стиль — дружелюбный, смешной, вдохновляющий, энергичный."
            )
        else:
            user_prompt = (
                "Сгенерируй очень короткое и смешное пожелание спокойной ночи "
                "на русском языке для чата Волки вуза МИРЭА (1–2 предложения). "
                "Используй маты, черный юмор и смешной зумерский стиль. "
                "Важно: оставь только одно сообщение с пожеланием, не добавляй комментариев и тд. Лишь один текст сообщения! "
                "Стиль — уютный, нежный, смешной, расслабляющий."
            )
        
        logger.info(f"Генерация текста для типа: {greeting_type}")
        model_obj = genai.GenerativeModel(model_name)
        response = model_obj.generate_content(user_prompt)
        
        generated_text = extract_text_from_response(response)
        
        if not generated_text:
            raise ValueError("Пустой ответ от Gemini")
        
        generated_text = " ".join(generated_text.split())
        
        logger.info(f"Текст успешно сгенерирован ({len(generated_text)} символов)")
        
        return jsonify({
            "success": True,
            "text": generated_text,
            "type": greeting_type,
            "model": model_name
        })
        
    except Exception as e:
        logger.exception(f"Ошибка генерации текста: {e}")
        return jsonify({
            "error": "Failed to generate text",
            "details": str(e)
        }), 500


@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Endpoint not found"}), 404


@app.errorhandler(500)
def internal_error(error):
    return jsonify({"error": "Internal server error"}), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
