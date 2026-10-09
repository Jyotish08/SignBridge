# SignBridge — User & Evaluation Guide

## 1. Quick Start Guide

### Prerequisites
- Windows 10/11 (or macOS / Linux)
- Python 3.10+
- Node.js 18+

### Launching SignBridge
Double-click:
```cmd
scripts\start_app.bat
```
Or start manually:
1. **Backend Server:**
   ```powershell
   cd backend
   .\venv\Scripts\uvicorn main:app --port 8000
   ```
2. **Frontend UI:**
   ```powershell
   cd frontend
   npm run dev
   ```
3. Open `http://localhost:5173` in your browser.

---

## 2. Audio Input Sources

### A. Microphone Input (Default)
1. Click **Record Voice** (or the microphone icon).
2. Allow browser microphone access when prompted.
3. Speak clearly. Your speech is recognized and translated at each natural pause.

### B. System Audio Capture (Meetings & Video)
1. Open **Settings & Metrics** (the gear icon in the top header).
2. Under *Audio Input Source*, select **System Audio**.
3. Click **Record Voice**.
4. In the browser screen-sharing dialog:
   - Select the entire screen or browser tab playing audio.
   - **Important:** Ensure the **"Share audio"** checkbox is checked!
5. Play audio from YouTube, Zoom, or any video. SignBridge will translate the system audio in real time.

---

## 3. Pause & Sensitivity Tuning
- Use the **Pause: 0.8s** slider on the live transcript container or in Settings to adjust speech segmentation:
  - **Fast Speakers:** Set to `0.5s – 0.6s` for rapid, punchy translation.
  - **Deliberate Speakers:** Set to `0.8s – 1.2s` to allow natural thinking pauses without prematurely triggering translation.

---

## 4. Live Offline Demonstration (Judges Checklist)

1. **Disconnect Wi-Fi:** Unplug your Ethernet cable or turn off Wi-Fi.
2. **Test Speech Recognition:** Speak `"How are you?"`.
3. **Verify Behavior:**
   - Real-time partial transcript displays with grey italic unstable text.
   - Upon pause, clause commits and Sockeye produces SignWriting in **~480 ms**.
   - Notice the green **OFFLINE** badge in the telemetry pill.
4. **Export Benchmarks:** Open Settings -> Click **Export JSON Log** to save all timestamped latencies for your project evaluation!
