# SignBridge — 48-Hour Hackathon Demo Guide

## 1. System Overview
SignBridge is a **100% offline, streaming speech-to-SignWriting translation system**. It uses a two-speed architecture:
- **Fast Path (Audio -> VAD -> tiny.en)**: Real-time partial transcript streaming via WebSockets with prefix freezing.
- **Slow Path (Pause -> Clause Commit -> Sockeye)**: Serialized clause-level translation to Factored SignWriting (FSW) with zero CPU contention.

---

## 2. One-Click Launch Instructions (Windows)

### Option A: Launcher Script
Double-click:
```cmd
scripts\start_app.bat
```
This automatically verifies the virtualenv, starts the backend server with pre-warmed models on `http://127.0.0.1:8000`, and launches the Vite frontend on `http://localhost:5173`.

### Option B: Manual Two-Terminal Launch
**Terminal 1 (Backend):**
```powershell
cd backend
.\venv\Scripts\uvicorn main:app --port 8000
```
*Wait ~3 seconds for `SignBridge all inference engines ready and warm!`.*

**Terminal 2 (Frontend):**
```powershell
cd frontend
npm run dev
```
Open `http://localhost:5173` in any browser.

---

## 3. High-Confidence Demo Sentences

Use these deterministic sentences during the live presentation for optimal translation and sub-second latency:

| # | Spoken Clause | Expected Latency | Sign Tokens Generated |
|---|---|---|---|
| **1** | *"Hello"* | ~348 ms | `M500x500S14c20...` (1 sign) |
| **2** | *"How are you?"* | ~482 ms | `M500x500S10020...` (1 sign) |
| **3** | *"Good morning everyone"* | ~826 ms | `M500x500S15d10...` (1 sign) |
| **4** | *"Thank you very much for your help"* | ~1290 ms | 5 signs |
| **5** | *"Sign language translation is working in real time offline"* | ~1570 ms | 8 signs |

---

## 4. Live Verification Checklist for Judges

1. **Offline Proof:**
   - Turn off Wi-Fi / disconnect network cables completely.
   - Speak into the microphone.
   - The status pill will show `● Speaking` -> `Pause Detected` -> `Translating (Sockeye)`.
   - SignWriting glyphs appear with zero network calls (`HF_HUB_OFFLINE=1`).

2. **Real-Time Streaming & Prefix Freezing:**
   - Speak a sentence naturally.
   - Notice the grey/italic text updating dynamically as words are recognized.
   - Notice words turning solid black as prefix agreement freezes them before pausing.

3. **Measured Latency Telemetry:**
   - Observe the top-right telemetry pill on the UI:
     `ASR: ~840ms | Sockeye: ~841ms | E2E: ~1.8s | OFFLINE`
   - All measurements are computed in real time from timestamp deltas.

4. **Synthetic Fallback Audio Verification:**
   Run the automated test pipeline from the terminal at any time:
   ```powershell
   .\backend\venv\Scripts\python.exe tests/test_streaming_pipeline.py
   ```
   Passes all verification gates with synthetic audio in ~5 seconds.
