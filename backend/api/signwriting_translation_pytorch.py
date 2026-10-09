import logging
from typing import Optional, List
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from signwriting_translation.bin import load_sockeye_translator, tokenize_spoken_text, translate

router = APIRouter()
logger = logging.getLogger(__name__)

class TextRequest(BaseModel):
    text: str

class SockeyeEngine:
    _instance: Optional["SockeyeEngine"] = None

    def __init__(self, model_path: str = "sign/sockeye-text-to-factored-signwriting"):
        logger.info(f"Initializing Sockeye translator from '{model_path}'...")
        self.model_path = model_path
        self.translator, self.tokenizer_path = load_sockeye_translator(model_path)
        self._warmup()

    @classmethod
    def get_instance(cls) -> "SockeyeEngine":
        if cls._instance is None:
            cls._instance = SockeyeEngine()
        return cls._instance

    def _warmup(self):
        try:
            logger.info("Warming up Sockeye translator...")
            self.translate_text("hello")
            logger.info("Sockeye translator warm-up complete.")
        except Exception as e:
            logger.warning(f"Sockeye warmup warning: {e}")

    def translate_text(self, text: str, spoken_language: str = "en", signed_language: str = "ase") -> str:
        text = text.strip()
        if not text:
            return ""
        tokenized_text = tokenize_spoken_text(text)
        model_input = f"${spoken_language} ${signed_language} {tokenized_text}"
        outputs = translate(self.translator, [model_input])
        return outputs[0] if outputs else ""

@router.post("/translate_signwriting")
async def translate_signwriting(request: TextRequest):
    try:
        engine = SockeyeEngine.get_instance()
        output = engine.translate_text(request.text)
        return {"signwriting": output}
    except Exception as e:
        logger.error(f"Translation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Translation failed: {str(e)}")
