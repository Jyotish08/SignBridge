import logging
import re
import requests
from fastapi import APIRouter
from pydantic import BaseModel
from config import config

router = APIRouter()
logger = logging.getLogger(__name__)

class TextRequest(BaseModel):
    text: str

def local_simplify(text: str) -> str:
    """Basic local rule-based text simplification for offline use."""
    cleaned = text.strip()
    # Remove excessive whitespace
    cleaned = re.sub(r'\s+', ' ', cleaned)
    # Remove common conversational filler words if present
    filler_patterns = [
        r'\b(?:um|uh|erm|like,?\s*you\s*know|you\s*know|basically|actually|literally)\b',
    ]
    for pattern in filler_patterns:
        cleaned = re.sub(pattern, '', cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    return cleaned or text.strip()

@router.post("/simplify_text")
async def simplify_text(request: TextRequest):
    input_text = request.text.strip()
    if not input_text:
        return {"simplified_text": ""}

    has_groq_key = bool(config.GROQ_API_KEY and config.GROQ_API_KEY.strip() != "your_groq_api_key_here")

    if has_groq_key:
        headers = {
            "Authorization": f"Bearer {config.GROQ_API_KEY.strip()}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": "llama3-70b-8192",
            "messages": [
                {
                    "role": "user",
                    "content": f"Simplify this text in one short sentence, and only return me the Simplify text nothing it should not contain any bulit points, it should be just a sentence here is the text: {input_text}"
                }
            ]
        }
        try:
            response = requests.post(config.GROQ_API_URL, json=payload, headers=headers, timeout=5)
            response.raise_for_status()
            simplified_text = response.json().get("choices", [{}])[0].get("message", {}).get("content", "").strip()
            if simplified_text:
                return {"simplified_text": simplified_text}
        except Exception as e:
            logger.warning(f"Groq API simplification failed, falling back to local simplification: {e}")

    # Fallback to local rule-based simplification
    fallback_text = local_simplify(input_text)
    return {
        "simplified_text": fallback_text,
        "fallback": True
    }
