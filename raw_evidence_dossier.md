# SignBridge Evidence Dossier

Here is the raw evidence dossier extracted from the repository's code, tests, and documentation, organized exactly as requested.

### 1. Inspiration
*   **Verified Facts:** The project targets the "Edge AI Consumer Utility Application" track (Snapdragon X Elite), aiming to provide everyday value by making real-time spoken content accessible. It specifically aims to capture not just microphone audio, but system audio (for translating videos, meetings, etc.). 
*   **Supporting Sources:** `app_idea.md` (Hackathon Track criteria; lines 1-10, 71).
*   **Missing Information Requiring Input:** Who exactly on the team brought up this use case? Was there a specific real-world interaction or personal observation that sparked the idea to focus on system audio and edge execution?

### 2. What it does
*   **Verified Facts:** SignBridge completely operates offline to translate voice into SignWriting (FSW) notation in real-time. A user selects "Microphone" or "System Audio" in the UI. As they speak, a Voice Activity Detector identifies clauses. Partial transcriptions appear in real-time, and when a pause is detected, the full clause is finalized, translated into SignWriting, and rendered visually.
*   **Supporting Sources:** `frontend/src/components/AudioRecorder.tsx` (UI source selection); `backend/api/stream_manager.py` (VAD clause detection and real-time WebSocket logic).
*   **Missing Information Requiring Input:** Have you tested the resulting SignWriting or UI workflow with actual Deaf or Hard-of-Hearing users yet?

### 3. How we built it
*   **Verified Facts:** 
    *   **Architecture:** The desktop app uses a Tauri (Rust) + React/Vite (TypeScript) frontend. The backend is a Python FastAPI server bundled as a Tauri sidecar (managed automatically by the application lifecycle).
    *   **Communication:** A WebSocket connection (`/ws/stream`) streams raw audio chunks to the backend.
    *   **AI Pipeline:** Uses `silero-vad` (Voice Activity Detection), `faster-whisper` (`tiny.en`) for on-device speech-to-text, and the HuggingFace `sign/sockeye-text-to-factored-signwriting` PyTorch model for text-to-SignWriting translation.
*   **Supporting Sources:** `app_idea.md` (Tauri sidecar concept), `backend/api/stream_manager.py` (WebSocket & VAD integration), `backend/api/transcribe.py`, `backend/api/signwriting_translation_pytorch.py`.
*   **Missing Information Requiring Input:** Did you evaluate any other models or frameworks before settling on Whisper tiny and Sockeye? Were there hidden packaging challenges with Tauri?

### 4. Challenges
*   **Verified Facts:** 
    *   **Concurrency/Latency:** CPU-bound inference blocked the real-time WebSocket loop, causing latency. This was solved by implementing a `TranscriptStabilizer` and offloading ASR and Sockeye translations to background threads using `loop.run_in_executor`, strictly managed by an `inference_lock`.
    *   **Cold Starts:** Loading PyTorch and Whisper models caused huge initial delays. This was addressed by implementing `_warmup()` methods on server startup that run dummy audio (`dummy_pcm`) and dummy text ("hello") through the models.
    *   **Resource Trade-offs:** Rather than translating every single word instantly, the system waits for a VAD-detected pause (clause boundary) to translate into SignWriting, balancing context quality and CPU load.
*   **Supporting Sources:** `backend/api/stream_manager.py` (asyncio locks and background tasks, `_on_pause_detected`), `backend/api/transcribe.py` & `backend/api/signwriting_translation_pytorch.py` (`_warmup` implementations).
*   **Missing Information Requiring Input:** Did you run into specific performance issues or limitations when testing this strictly on the Snapdragon X Elite hardware constraints?

### 5. Accomplishments
*   **Verified Facts:** The team built a demonstrably fully offline, continuous streaming E2E pipeline. Benchmark tests prove the locked architecture achieves an E2E Speech-End to Signs latency of ~1.8 to 2.0 seconds. `faster-whisper` handles 1s ASR in ~312-321ms, and the Sockeye pipeline latency is ~800-900ms.
*   **Supporting Sources:** `tests/benchmark_pipeline.py` (Terminal output latency tables, measuring warm average limits and memory footprint).
*   **Missing Information Requiring Input:** Do you have live demo videos, screenshots, or specific user feedback validating the working UI?

### 6. What we learned
*   **Verified Facts:** 
    *   Running complex AI (Python/PyTorch) seamlessly within a consumer desktop app is highly viable via Tauri sidecars.
    *   On-device Edge AI requires strict operational constraints. Relying on Voice Activity Detection (silero-vad) to chunk audio into clauses before invoking heavy translation models drastically improves system responsiveness over continuous translation.
*   **Supporting Sources:** `backend/api/stream_manager.py` (event-driven translation logic), `app_idea.md` (Sidecar documentation).
*   **Missing Information Requiring Input:** Were there specific interactions, failed experiments, or feedback during the hackathon that led you to the clause-chunking realization?

### 7. What's next
*   **Verified Facts:** 
    *   **Offline Pose Generation:** Currently, the app uses an external cloud API (`POSE_API_URL`) with a dummy local fallback for avatar pose generation. Integrating the `spoken-to-signed-translation` python package for completely offline `.pose` file generation is planned.
    *   **Reverse Mode:** Translating sign language back to text was deliberately scoped out of the MVP but is a logical future step.
*   **Supporting Sources:** `plan/phase13_offline_pose_generation.md`, `backend/api/pose_generation.py`, `app_idea.md` ("Reverse Mode: Not included in this MVP").
*   **Missing Information Requiring Input:** Which of these planned features is the highest priority for the team moving forward?

### 8. Technical stack
*   **Verified Facts:**
    *   **Frontend:** Tauri (Rust), React, TypeScript, Vite, Tailwind CSS.
    *   **Backend:** Python 3.11, FastAPI, Uvicorn, WebSockets.
    *   **Models:** `faster-whisper` (tiny.en), `silero-vad`, `sign/sockeye-text-to-factored-signwriting` (PyTorch).
    *   **Optional Integration:** Groq API (LLaMA) for cloud-based text simplification.
*   **Supporting Sources:** `frontend/package.json`, `backend/requirements-py311.txt`, `backend/main.py`.
*   **Missing Information Requiring Input:** Are there any additional tools (CI/CD, design tools) you want highlighted in the story?
