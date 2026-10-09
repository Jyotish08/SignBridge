import io
import json
import time
import asyncio
import logging
from typing import List, Dict, Tuple, Optional
import numpy as np
import torch
import av
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from config import config
from api.transcribe import WhisperEngine
from api.signwriting_translation_pytorch import SockeyeEngine

router = APIRouter()
logger = logging.getLogger(__name__)

class VADDetector:
    """Fast, local Silero VAD frame processor."""
    _model = None

    @classmethod
    def get_model(cls):
        if cls._model is None:
            logger.info("Loading Silero VAD model (offline)...")
            import os
            local_hub_path = os.path.expanduser("~/.cache/torch/hub/snakers4_silero-vad_master")
            if os.path.isdir(local_hub_path):
                cls._model, _ = torch.hub.load(
                    repo_or_dir=local_hub_path,
                    model="silero_vad",
                    source="local",
                    force_reload=False,
                    onnx=False
                )
            else:
                cls._model, _ = torch.hub.load(
                    repo_or_dir="snakers4/silero-vad",
                    model="silero_vad",
                    force_reload=False,
                    onnx=False
                )
            # Warm up with zero frame
            cls._model(torch.zeros(512), 16000)
            logger.info("Silero VAD ready.")
        return cls._model

    def __init__(self, threshold: float = 0.5):
        self.model = self.get_model()
        self.threshold = threshold

    def is_speech(self, frame_512: np.ndarray) -> Tuple[bool, float]:
        """Process a 512-sample (32ms at 16kHz) float32 frame."""
        tensor = torch.from_numpy(frame_512).float()
        with torch.no_grad():
            prob = self.model(tensor, 16000).item()
        return (prob >= self.threshold, prob)

class TranscriptStabilizer:
    """Stabilizes streaming ASR partial transcripts using prefix agreement."""
    def __init__(self, n_agreement: int = 3):
        self.n_agreement = n_agreement
        self.history: List[List[str]] = []
        self.committed_words: List[str] = []

    def update(self, new_text: str) -> Tuple[str, str]:
        """
        Takes raw ASR output and returns (stable_prefix, unstable_suffix).
        """
        words = [w for w in new_text.strip().split() if w]
        if not words:
            return (" ".join(self.committed_words), "")

        self.history.append(words)
        if len(self.history) > self.n_agreement:
            self.history.pop(0)

        # If we have enough history, find longest prefix shared across all recent history
        if len(self.history) >= self.n_agreement:
            min_len = min(len(h) for h in self.history)
            match_len = 0
            for i in range(min_len):
                candidate = self.history[0][i].lower()
                if all(h[i].lower() == candidate for h in self.history):
                    match_len = i + 1
                else:
                    break

            if match_len > len(self.committed_words):
                # Update committed words to the matched prefix
                self.committed_words = self.history[-1][:match_len]

        stable_text = " ".join(self.committed_words)
        unstable_words = words[len(self.committed_words):]
        unstable_text = " ".join(unstable_words)
        return (stable_text, unstable_text)

    def finalize(self, last_text: str) -> str:
        """Commit all remaining words upon clause boundary."""
        final_clause = last_text.strip()
        self.history.clear()
        self.committed_words.clear()
        return final_clause

class StreamingSession:
    """
    Manages audio streaming, VAD pause detection, serialized ASR/Sockeye inference,
    and WebSocket communication for a single client session.
    """
    def __init__(self, websocket: WebSocket):
        self.ws = websocket
        self.vad = VADDetector(threshold=config.VAD_THRESHOLD)
        self.stabilizer = TranscriptStabilizer(n_agreement=config.N_STABLE_AGREEMENT)
        self.whisper = WhisperEngine.get_instance()
        self.sockeye = SockeyeEngine.get_instance()

        # Audio buffers (16kHz float32)
        self.audio_buffer = np.array([], dtype=np.float32)
        self.speech_buffer = np.array([], dtype=np.float32)
        self.pause_threshold_sec = config.PAUSE_THRESHOLD_SEC

        # State tracking
        self.is_speaking = False
        self.silence_samples = 0
        self.speech_samples = 0
        self.last_asr_text = ""
        self.last_asr_time = 0.0
        self.t_speech_start = 0.0
        self.t_last_speech = 0.0

        # Inference serialization lock
        self.inference_lock = asyncio.Lock()
        self.is_running = True

    async def handle_audio_chunk(self, raw_bytes: bytes):
        """Decode incoming chunk and push into audio buffer."""
        pcm = self._decode_chunk(raw_bytes)
        if len(pcm) == 0:
            return

        self.audio_buffer = np.concatenate([self.audio_buffer, pcm])

        # Process available 512-sample frames for VAD
        frame_size = 512
        pause_threshold_samples = int(self.pause_threshold_sec * 16000)

        while len(self.audio_buffer) >= frame_size:
            frame = self.audio_buffer[:frame_size]
            self.audio_buffer = self.audio_buffer[frame_size:]

            is_voice, prob = self.vad.is_speech(frame)

            if is_voice:
                if not self.is_speaking:
                    self.is_speaking = True
                    self.t_speech_start = time.perf_counter()
                    await self._send_status("SPEECH_DETECTED")

                self.speech_buffer = np.concatenate([self.speech_buffer, frame])
                self.speech_samples += frame_size
                self.silence_samples = 0
                self.t_last_speech = time.perf_counter()

            else:
                if self.is_speaking:
                    # Still in speech session, accumulating silence
                    self.speech_buffer = np.concatenate([self.speech_buffer, frame])
                    self.silence_samples += frame_size

                    # Check for pause / clause boundary
                    if self.silence_samples >= pause_threshold_samples:
                        await self._on_pause_detected()

        # If speaking and not currently translating, run partial ASR every ~350ms
        now = time.perf_counter()
        if self.is_speaking and (now - self.last_asr_time > 0.35) and not self.inference_lock.locked():
            asyncio.create_task(self._run_partial_asr())

    def _decode_chunk(self, data: bytes) -> np.ndarray:
        """Decodes raw 16kHz PCM (int16/float32) or WebM/Opus."""
        # 1. Check if raw WebM/Matroska container
        if data.startswith(b'\x1a\x45\xdf\xa3'):
            try:
                container = av.open(io.BytesIO(data))
                resampler = av.AudioResampler(format='s16', layout='mono', rate=16000)
                pcm_bytes = bytearray()
                for frame in container.decode(audio=0):
                    resampled = resampler.resample(frame)
                    for r in resampled:
                        pcm_bytes.extend(r.to_ndarray().tobytes())
                if len(pcm_bytes) > 0:
                    return np.frombuffer(pcm_bytes, dtype=np.int16).astype(np.float32) / 32768.0
            except Exception as e:
                logger.debug(f"PyAV container decode note: {e}")

        # 2. Raw 16-bit PCM (16kHz mono) - standard streaming format
        try:
            return np.frombuffer(data, dtype=np.int16).astype(np.float32) / 32768.0
        except Exception:
            return np.array([], dtype=np.float32)

    async def _run_partial_asr(self):
        """Runs faster-whisper tiny.en on current speech buffer if lock is free."""
        if len(self.speech_buffer) < 4000:  # Need at least 250ms of audio
            return

        if self.inference_lock.locked():
            return

        async with self.inference_lock:
            self.last_asr_time = time.perf_counter()
            t0 = time.perf_counter()

            # Take a snapshot of current speech buffer
            audio_snapshot = self.speech_buffer.copy()

            # Run in worker thread to not block asyncio loop
            loop = asyncio.get_running_loop()
            text = await loop.run_in_executor(
                None,
                self.whisper.transcribe_audio_array,
                audio_snapshot
            )

            t_asr = (time.perf_counter() - t0) * 1000.0

            if text and text != self.last_asr_text:
                self.last_asr_text = text
                stable, unstable = self.stabilizer.update(text)
                await self._send_json({
                    "type": "transcript",
                    "stable": stable,
                    "unstable": unstable,
                    "is_final": False,
                    "asr_ms": round(t_asr, 1)
                })

    async def _on_pause_detected(self):
        """Called when silence threshold is exceeded. Commits clause and invokes Sockeye."""
        t_pause = time.perf_counter()
        self.is_speaking = False
        await self._send_status("PAUSE_DETECTED")

        # Must acquire lock for Sockeye inference
        async with self.inference_lock:
            # 1. Final ASR pass on entire clause
            t_asr_start = time.perf_counter()
            loop = asyncio.get_running_loop()

            clause_audio = self.speech_buffer.copy()
            final_text = await loop.run_in_executor(
                None,
                self.whisper.transcribe_audio_array,
                clause_audio
            )
            t_asr_ms = (time.perf_counter() - t_asr_start) * 1000.0

            clause = self.stabilizer.finalize(final_text or self.last_asr_text)
            words = clause.split()

            # Reset speech buffers for next clause
            self.speech_buffer = np.array([], dtype=np.float32)
            self.silence_samples = 0
            self.speech_samples = 0
            self.last_asr_text = ""

            if not clause or len(words) < config.MIN_CLAUSE_WORDS:
                await self._send_status("LISTENING")
                return

            # Emit committed clause
            await self._send_json({
                "type": "clause_committed",
                "clause": clause,
                "asr_ms": round(t_asr_ms, 1)
            })

            # 2. Sockeye SignWriting translation
            await self._send_status("TRANSLATING")
            t_sockeye_start = time.perf_counter()

            fsw_output = await loop.run_in_executor(
                None,
                self.sockeye.translate_text,
                clause
            )
            t_sockeye_ms = (time.perf_counter() - t_sockeye_start) * 1000.0
            t_e2e_ms = (time.perf_counter() - t_pause) * 1000.0

            signs = [token for token in fsw_output.strip().split() if token]

            # 3. Emit SignWriting and latency telemetry
            await self._send_json({
                "type": "signwriting",
                "clause": clause,
                "signwriting": fsw_output,
                "signs": signs,
                "telemetry": {
                    "asr_ms": round(t_asr_ms, 1),
                    "sockeye_ms": round(t_sockeye_ms, 1),
                    "e2e_ms": round(t_e2e_ms, 1),
                    "mode": "OFFLINE"
                }
            })

            await self._send_status("LISTENING")

    async def _send_status(self, status: str):
        await self._send_json({"type": "status", "status": status})

    async def _send_json(self, data: dict):
        try:
            await self.ws.send_json(data)
        except Exception:
            pass

@router.websocket("/ws/stream")
async def websocket_stream(websocket: WebSocket):
    await websocket.accept()
    logger.info("Client connected to /ws/stream")
    session = StreamingSession(websocket)

    try:
        # Initial greeting with system status
        await websocket.send_json({
            "type": "init",
            "status": "READY",
            "whisper_model": config.WHISPER_MODEL,
            "mode": "OFFLINE"
        })

        while True:
            msg = await websocket.receive()
            if msg.get("type") == "websocket.disconnect":
                logger.info("Client disconnected from /ws/stream (clean disconnect)")
                break

            if "bytes" in msg and msg["bytes"]:
                await session.handle_audio_chunk(msg["bytes"])
            elif "text" in msg and msg["text"]:
                try:
                    payload = json.loads(msg["text"])
                    if payload.get("type") == "config":
                        if "pause_threshold_sec" in payload:
                            session.pause_threshold_sec = float(payload["pause_threshold_sec"])
                            logger.info(f"Updated session pause threshold: {session.pause_threshold_sec}s")
                            await session._send_json({
                                "type": "config_ack",
                                "pause_threshold_sec": session.pause_threshold_sec
                            })
                except Exception as e:
                    logger.warning(f"Error handling WS config text: {e}")

    except WebSocketDisconnect:
        logger.info("Client disconnected from /ws/stream")
    except RuntimeError as e:
        if "disconnect message has been received" in str(e):
            logger.info("Client session ended.")
        else:
            logger.error(f"WebSocket runtime error: {e}")
    except Exception as e:
        logger.error(f"WebSocket session error: {e}")
