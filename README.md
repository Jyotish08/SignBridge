# SignBridge: Real-Time Voice-to-Sign Translator

## Project Overview

**SignBridge** is a cross-platform Edge AI application that translates spoken English into animated SignWriting in real time. Designed for accessibility and inclusivity, SignBridge empowers Deaf and hard-of-hearing users to access spoken content—live or recorded—on any device, fully offline or with optional online enhancements.

- **Track:** Edge AI Consumer Utility Application (Snapdragon® X Elite)
- **Core Value:** Everyday utility for a broad audience, enabling real-time voice-to-sign translation on-device.
- **Edge AI:** All core AI runs locally (Whisper, PyTorch SignWriting Model, etc.), with optional cloud-based text simplification (Groq + LLaMA).
- **Cross-Platform:** Runs on Windows, macOS, Linux, and Snapdragon X Elite devices as a web or native desktop app (Tauri).

---

## Key Features

- **Speech-to-Text (Offline):**
  - Uses Whisper for fast, accurate, on-device transcription.
- **Optional Text Simplification (Online):**
  - Toggle to simplify complex sentences using Groq API + LLaMA models (for easier sign translation).
- **Text-to-SignWriting Translation(Offline):**
  - Converts English text to SignWriting notation using a Sign Writing model (runs locally).
- **SignWriting Rendering & Animation(Hybrid):**
  - Displays animated SignWriting using open web standards and custom components.
- **System & Mic Audio Input(Offline + Enhanced Foe Each Device):**
  - Capture from microphone and system audio for real-time translation of meetings, videos, etc.
- **Save & Export:**
  - Download SignWriting as SVG image.
- **Modern UI:**
  - Responsive, accessible, and themeable (light/dark mode).

---

## Quick Start Guide

### 1. **Clone the Repository**
```sh
git clone https://github.com/your-org/SignBridge.git
cd SignBridge
```

### 2. **Quick Start (One-Click Launch)**
The easiest way to run SignBridge is using the integrated startup script:

**On Windows:**
```bat
.\scripts\start_app.bat
```
*(or run `powershell -ExecutionPolicy Bypass -File .\scripts\start_app.ps1`)*

**On macOS / Linux:**
```sh
chmod +x ./scripts/start_app.sh
./scripts/start_app.sh
```

This automatically launches the FastAPI Edge AI backend (loading local offline models) and opens the Vite web interface on [http://localhost:5173](http://localhost:5173).

---

### 3. **Manual Setup (Development)**
If you prefer running backend and frontend independently:

**Backend Setup:**
```sh
cd backend
# Create and activate virtual environment (Python 3.10 or 3.11)
python -m venv venv

# Windows:
.\venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

pip install -r requirements.txt
python run_backend.py
```
Backend will be live and serving inference on `http://127.0.0.1:8000` (API docs at `/docs`, health check at `/health`).

**Frontend Setup:**
```sh
cd frontend
npm install
npm run dev
```
Open [http://localhost:5173](http://localhost:5173) in your browser.

---

## Documentation
- [Frontend README](./frontend/README.md): UI, Tauri, and web app details
- [Backend README](./backend/README.md): API endpoints, Python setup, and model info

---

## Hackathon & Category Fit
- **Consumer-Oriented:** Designed for real-world accessibility and communication needs.
- **Utility-Focused:** Bridges the gap between spoken language and sign language in any setting.
- **Edge AI:** All core translation and rendering runs locally; no cloud required for main pipeline.
- **Fully On-Device:** Works offline; optional online features (text simplification) enhance experience.
- **Cross-Platform:** Runs on Snapdragon X Elite, Windows, macOS, and Linux.
- **LLaMA & Groq Integration:** Uses Groq API to accelerate LLaMA-based text simplification.

---

## Development Phases & Roadmap

See the [plan/](./plan/) directory for detailed phase documents.

| Phase | Description | Status |
|-------|-------------|--------|
| 1 | Speech-to-Text (Whisper) | ✅ Done |
| 2 | Text Simplification (Groq + LLaMA) | ✅ Done |
| 3 | Text-to-SignWriting Translation | ✅ Done |
| 4 | SignWriting Rendering | ✅ Done |
| 5 | 2D Skeleton Animation | ✅ Done |
| 6 | UI Packaging & Polish | ✅ Done |
| 7 | UI Enhancements | ✅ Done |
| 8 | Tauri Integration | ✅ Done |
| 9 | Cross-Platform Build Scripts | ✅ Done |
| 10 | Snapdragon Optimization | ⏳ In Progress |
| 11 | System Audio & Realtime Streaming | ✅ Done |
| 12 | Settings & Telemetry Metrics | ✅ Done |
| 13 | Offline Pose Generation | ⏳ Reference Baseline (Phase 13 In Progress) |

- **See [plan/](./plan/) for all phase docs and details.**
- **Completed phases:** 1–9, 11, 12
- **Current/Next:** 10, 13 (Snapdragon hardware acceleration & full text-to-pose model)

---

## License
MIT License 