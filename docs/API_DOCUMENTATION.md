# SignBridge — API & Streaming Protocol Documentation

## 1. Overview
SignBridge provides a real-time, 100% offline speech-to-SignWriting translation engine. It uses a **two-speed serialized architecture** to eliminate CPU contention between speech recognition (`faster-whisper tiny.en`) and neural sign translation (`Sockeye`).

---

## 2. WebSocket Streaming Protocol (`/ws/stream`)

### Endpoint
```text
ws://127.0.0.1:8000/ws/stream
```

### Connection Flow
1. **Handshake & Init Packet:**
   Upon connection, the server sends an initialization status message:
   ```json
   {
     "type": "init",
     "status": "READY",
     "whisper_model": "tiny.en",
     "mode": "OFFLINE"
   }
   ```

2. **Client -> Server (Audio Streaming):**
   - **Format:** Raw 16kHz, 16-bit Mono Linear PCM (or WebM container chunks).
   - **Chunk Size:** 4096 samples (~256 ms per chunk).
   - **Transport:** Binary WebSocket frames (`send_bytes`).

3. **Client -> Server (Dynamic Configuration):**
   Clients can adjust session parameters at runtime via JSON text messages:
   ```json
   {
     "type": "config",
     "pause_threshold_sec": 0.8
   }
   ```
   Server acknowledges with:
   ```json
   {
     "type": "config_ack",
     "pause_threshold_sec": 0.8
   }
   ```

4. **Server -> Client Events:**

   - **System Status (`status`):**
     Sent when VAD or inference states change:
     ```json
     { "type": "status", "status": "SPEECH_DETECTED" | "PAUSE_DETECTED" | "TRANSLATING" | "LISTENING" }
     ```

   - **Streaming Partial Transcript (`transcript`):**
     Emitted periodically (~350ms) during speech. Uses prefix-freezing for visual stability:
     ```json
     {
       "type": "transcript",
       "stable": "Hello, how",
       "unstable": "are you doing?",
       "is_final": false,
       "asr_ms": 318.5
     }
     ```

   - **Clause Committed (`clause_committed`):**
     Emitted when silence exceeds the pause threshold and a clause is finalized:
     ```json
     {
       "type": "clause_committed",
       "clause": "Hello, how are you doing?",
       "asr_ms": 320.1
     }
     ```

   - **SignWriting Output & Telemetry (`signwriting`):**
     Emitted when Sockeye finishes translating the committed clause:
     ```json
     {
       "type": "signwriting",
       "clause": "Hello, how are you doing?",
       "signwriting": "M500x500S14c20... M500x500S10020...",
       "signs": [
         "M500x500S14c20...",
         "M500x500S10020..."
       ],
       "telemetry": {
         "asr_ms": 320.1,
         "sockeye_ms": 841.0,
         "e2e_ms": 1161.1,
         "mode": "OFFLINE"
       }
     }
     ```

---

## 3. REST Compatibility Endpoints

### `POST /transcribe`
Upload a full audio file for batch transcription.
- **Request:** `multipart/form-data` with `audio` file.
- **Response:**
  ```json
  { "text": "Hi how are you?" }
  ```

### `POST /translate_signwriting`
Direct clause translation to Factored SignWriting (FSW).
- **Request:**
  ```json
  { "text": "Hello" }
  ```
- **Response:**
  ```json
  { "signwriting": "M500x500S14c20489x524S27106515x543S30a00482x482S33e00482x482" }
  ```

### `POST /generate_pose`
Generates pose skeleton animation with local `default.pose` fallback when offline.
- **Request:**
  ```json
  {
    "text": "Hello",
    "spoken_language": "en",
    "signed_language": "ase"
  }
  ```
- **Response:**
  ```json
  {
    "pose_data": "<base64_encoded_binary>",
    "data_format": "binary_base64"
  }
  ```
