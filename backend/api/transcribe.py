import os
import tempfile
import logging
import numpy as np
from typing import Optional
from fastapi import APIRouter, UploadFile, File, HTTPException
from faster_whisper import WhisperModel
from config import config

router = APIRouter()
logger = logging.getLogger(__name__)

class WhisperEngine:
    _instance: Optional["WhisperEngine"] = None

    def __init__(self):
        logger.info(f"Initializing faster-whisper model '{config.WHISPER_MODEL}' on {config.WHISPER_DEVICE} ({config.WHISPER_COMPUTE_TYPE})...")
        try:
            self.model = WhisperModel(
                config.WHISPER_MODEL,
                device=config.WHISPER_DEVICE,
                compute_type=config.WHISPER_COMPUTE_TYPE,
                local_files_only=True,
                cpu_threads=4
            )
        except Exception:
            self.model = WhisperModel(
                config.WHISPER_MODEL,
                device=config.WHISPER_DEVICE,
                compute_type=config.WHISPER_COMPUTE_TYPE,
                local_files_only=False,
                cpu_threads=4
            )
        self._warmup()

    @classmethod
    def get_instance(cls) -> "WhisperEngine":
        if cls._instance is None:
            cls._instance = WhisperEngine()
        return cls._instance

    def _warmup(self):
        try:
            logger.info("Warming up faster-whisper model...")
            dummy_pcm = np.zeros(16000, dtype=np.float32)
            segments, _ = self.model.transcribe(dummy_pcm, language="en")
            list(segments)
            logger.info("faster-whisper warm-up complete.")
        except Exception as e:
            logger.warning(f"Whisper warmup warning: {e}")

    def transcribe_audio_array(self, audio_data: np.ndarray) -> str:
        """
        Transcribe a 16kHz float32 mono numpy array directly from memory.
        """
        if len(audio_data) == 0:
            return ""
        segments, _ = self.model.transcribe(
            audio_data,
            language="en",
            beam_size=1,
            best_of=1,
            temperature=0.0,
            condition_on_previous_text=False
        )
        text = " ".join([seg.text.strip() for seg in segments]).strip()
        return text

    def transcribe_file(self, file_path: str) -> str:
        segments, _ = self.model.transcribe(
            file_path,
            language="en",
            beam_size=1,
            temperature=0.0
        )
        text = " ".join([seg.text.strip() for seg in segments]).strip()
        return text

@router.post("/transcribe")
async def transcribe(audio: UploadFile = File(...)):
    input_filepath = None
    try:
        suffix = os.path.splitext(audio.filename or "temp.wav")[-1]
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as input_file:
            contents = await audio.read()
            if not contents:
                raise HTTPException(status_code=400, detail="Empty audio file uploaded.")
            input_file.write(contents)
            input_filepath = input_file.name

        engine = WhisperEngine.get_instance()
        transcription = engine.transcribe_file(input_filepath)
        return {"text": transcription}
    except Exception as e:
        logger.error(f"Transcription error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if input_filepath and os.path.exists(input_filepath):
            try:
                os.remove(input_filepath)
            except Exception:
                pass
