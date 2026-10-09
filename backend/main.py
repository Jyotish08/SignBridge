import os
import tempfile
import logging
import asyncio
import uuid
import shutil
import subprocess
import uvicorn
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from api.signwriting_translation_pytorch import router as signwriting_translation_pytorch_router
from api.simplify_text import router as simplify_text_router
from api.pose_generation import router as pose_generation_router
from api.transcribe import router as transcribe_router
from api.stream_manager import router as stream_router
from config import config

app = FastAPI()


app.add_middleware(
    CORSMiddleware,
    allow_origins=config.get_cors_origins(),
    allow_credentials=config.CORS_ALLOW_CREDENTIALS,
    allow_methods=config.CORS_ALLOW_METHODS,
    allow_headers=config.CORS_ALLOW_HEADERS,
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(BASE_DIR, "..")) 

logging.basicConfig(level=getattr(logging, config.LOG_LEVEL))

app.include_router(transcribe_router)
app.include_router(signwriting_translation_pytorch_router)
app.include_router(simplify_text_router)
app.include_router(pose_generation_router)
app.include_router(stream_router)

@app.on_event("startup")
async def startup_event():
    logging.info("SignBridge backend starting up - warming models...")
    from api.transcribe import WhisperEngine
    from api.signwriting_translation_pytorch import SockeyeEngine
    from api.stream_manager import VADDetector
    
    # Warm up in background thread to avoid blocking loop
    loop = asyncio.get_running_loop()
    await loop.run_in_executor(None, WhisperEngine.get_instance)
    await loop.run_in_executor(None, SockeyeEngine.get_instance)
    await loop.run_in_executor(None, VADDetector.get_model)
    logging.info("SignBridge all inference engines ready and warm!")

@app.get("/")
def read_root():
    return {
        "status": "ok",
        "service": "SignBridge Backend API",
        "docs": "http://127.0.0.1:8000/docs",
        "frontend": "http://localhost:5173"
    }

@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "whisper": config.WHISPER_MODEL,
        "mode": "OFFLINE"
    }

if __name__ == "__main__":
    uvicorn.run("main:app", host=config.HOST, port=config.PORT, reload=config.DEBUG)
