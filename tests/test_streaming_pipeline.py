import asyncio
import wave
import json
import time
import numpy as np
import websockets

async def run_streaming_test():
    uri = "ws://127.0.0.1:8000/ws/stream"
    wav_path = "tests/test_file_converted.wav"

    print(f"Connecting to {uri}...")
    async with websockets.connect(uri) as ws:
        print("Connected to WebSocket successfully!")

        # Wait for init message
        init_msg = await ws.recv()
        print("Init message received:", init_msg)

        # Background task to listen for server responses
        received_events = []
        is_done = asyncio.Event()

        async def listen_server():
            try:
                while not is_done.is_set():
                    raw_msg = await ws.recv()
                    data = json.loads(raw_msg)
                    msg_type = data.get("type")
                    received_events.append(data)
                    print(f"  [SERVER -> CLIENT] {msg_type.upper()}: {data}")
                    if msg_type == "signwriting":
                        print("\n>>> SignWriting generation received! Test successful! <<<\n")
                        is_done.set()
                        break
            except Exception as e:
                if not is_done.is_set():
                    print("Listener terminated:", e)

        listener_task = asyncio.create_task(listen_server())

        # Stream audio chunks from wav file
        with wave.open(wav_path, "rb") as wf:
            chunk_size = 4096  # 256ms at 16kHz
            sample_rate = wf.getframerate()
            print(f"Streaming audio: {wf.getnframes()} frames, {sample_rate}Hz in chunks of {chunk_size} samples...")

            while True:
                data = wf.readframes(chunk_size)
                if not data:
                    break
                # Send raw 16-bit PCM chunk
                await ws.send(data)
                # Simulate real-time audio playback
                await asyncio.sleep(chunk_size / sample_rate * 0.7)

        print("\nFinished sending speech audio. Now sending 1.5s of silence to trigger pause commitment...")
        silence_chunk = np.zeros(chunk_size, dtype=np.int16).tobytes()
        for _ in range(6):  # ~1.5 seconds of silence
            await ws.send(silence_chunk)
            await asyncio.sleep(0.15)

        # Wait up to 10 seconds for translation
        try:
            await asyncio.wait_for(is_done.wait(), timeout=10.0)
        except asyncio.TimeoutError:
            print("Timed out waiting for SignWriting translation.")
        finally:
            is_done.set()
            listener_task.cancel()

        print("\n=== SUMMARY OF RECEIVED EVENTS ===")
        types = [e.get("type") for e in received_events]
        print(f"Event types received: {types}")
        
        has_transcript = any(t == "transcript" for t in types)
        has_clause = any(t == "clause_committed" for t in types)
        has_signwriting = any(t == "signwriting" for t in types)

        print(f"Partial transcripts received: {has_transcript}")
        print(f"Committed clause received: {has_clause}")
        print(f"SignWriting tokens received: {has_signwriting}")

        for e in received_events:
            if e.get("type") == "signwriting":
                print("\nFINAL SIGNWRITING RESULT:")
                print("  Clause:", e.get("clause"))
                print("  Signs (tokens):", e.get("signs"))
                print("  Telemetry:", e.get("telemetry"))

        assert has_transcript or has_clause, "Should have received transcripts or clause"
        assert has_signwriting, "Should have received SignWriting output from Sockeye"
        print("\n>>> ALL VERIFICATION GATES PASSED! <<<")

if __name__ == "__main__":
    asyncio.run(run_streaming_test())
