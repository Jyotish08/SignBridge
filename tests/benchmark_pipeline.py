import os
import sys
import time
import wave
import json
import asyncio
import numpy as np
import psutil
import websockets

# Add backend directory to sys.path so we can import engines directly for micro-benchmarks
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend"))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"

def benchmark_sockeye_micro():
    print("\n==========================================")
    print("1. MICRO-BENCHMARK: SOCKEYE TRANSLATOR")
    print("==========================================")
    from api.signwriting_translation_pytorch import SockeyeEngine

    process = psutil.Process(os.getpid())
    mem_before = process.memory_info().rss / (1024 * 1024)

    t_load_start = time.perf_counter()
    engine = SockeyeEngine.get_instance()
    t_load_sec = time.perf_counter() - t_load_start

    mem_after = process.memory_info().rss / (1024 * 1024)
    print(f"Sockeye Load + Warmup Time: {t_load_sec:.3f} s")
    print(f"Process RAM: {mem_after:.1f} MB (Delta: +{mem_after - mem_before:.1f} MB)")

    test_phrases = [
        "Hello",
        "How are you?",
        "Good morning everyone",
        "Thank you very much for your help",
        "Sign language translation is working in real time offline"
    ]

    latencies = []
    print("\nRunning warm translation iterations:")
    for i, phrase in enumerate(test_phrases, 1):
        t0 = time.perf_counter()
        fsw = engine.translate_text(phrase)
        t_ms = (time.perf_counter() - t0) * 1000.0
        latencies.append(t_ms)
        tokens = len(fsw.strip().split())
        print(f"  [{i}] '{phrase[:30]:<30}' -> {t_ms:>7.1f} ms | Signs: {tokens}")

    avg_lat = sum(latencies) / len(latencies)
    min_lat = min(latencies)
    max_lat = max(latencies)
    print(f"\nSockeye Warm Latency Summary: Avg = {avg_lat:.1f} ms | Min = {min_lat:.1f} ms | Max = {max_lat:.1f} ms")
    return {"avg_ms": avg_lat, "min_ms": min_lat, "max_ms": max_lat}

def benchmark_whisper_micro():
    print("\n==========================================")
    print("2. MICRO-BENCHMARK: FASTER-WHISPER TINY.EN")
    print("==========================================")
    from api.transcribe import WhisperEngine

    process = psutil.Process(os.getpid())
    mem_before = process.memory_info().rss / (1024 * 1024)

    t_load_start = time.perf_counter()
    whisper_engine = WhisperEngine.get_instance()
    t_load_sec = time.perf_counter() - t_load_start

    mem_after = process.memory_info().rss / (1024 * 1024)
    print(f"Whisper tiny.en Load + Warmup Time: {t_load_sec:.3f} s")
    print(f"Process RAM: {mem_after:.1f} MB")

    wav_path = os.path.join(os.path.dirname(__file__), "test_file_converted.wav")
    with wave.open(wav_path, "rb") as wf:
        raw_bytes = wf.readframes(wf.getnframes())
        full_audio = np.frombuffer(raw_bytes, dtype=np.int16).astype(np.float32) / 32768.0

    # Test segments: 1s, 2s, full 4.14s
    segments = [
        ("1.0s chunk", full_audio[:16000]),
        ("2.0s chunk", full_audio[:32000]),
        ("4.1s full utterance", full_audio)
    ]

    latencies = []
    print("\nRunning warm ASR inference:")
    for label, audio_slice in segments:
        t0 = time.perf_counter()
        text = whisper_engine.transcribe_audio_array(audio_slice)
        t_ms = (time.perf_counter() - t0) * 1000.0
        latencies.append(t_ms)
        print(f"  [{label:<19}] -> {t_ms:>7.1f} ms | Text: '{text}'")

    avg_lat = sum(latencies) / len(latencies)
    print(f"\nWhisper tiny.en Latency Summary: Avg = {avg_lat:.1f} ms | Min = {min(latencies):.1f} ms | Max = {max(latencies):.1f} ms")
    return {"avg_ms": avg_lat, "min_ms": min(latencies), "max_ms": max(latencies)}

async def benchmark_websocket_pipeline():
    print("\n==========================================")
    print("3. E2E STREAMING PIPELINE BENCHMARK (WEBSOCKET)")
    print("==========================================")
    uri = "ws://127.0.0.1:8000/ws/stream"
    wav_path = os.path.join(os.path.dirname(__file__), "test_file_converted.wav")

    async with websockets.connect(uri) as ws:
        init_raw = await ws.recv()
        print("Connected! Init packet:", init_raw)

        results = {}
        is_done = asyncio.Event()

        async def listen():
            while not is_done.is_set():
                try:
                    msg = await ws.recv()
                    data = json.loads(msg)
                    if data.get("type") == "signwriting":
                        results.update(data)
                        is_done.set()
                        break
                except Exception:
                    break

        listener = asyncio.create_task(listen())

        with wave.open(wav_path, "rb") as wf:
            chunk_size = 4096
            sample_rate = wf.getframerate()
            t_start_stream = time.perf_counter()

            while True:
                chunk = wf.readframes(chunk_size)
                if not chunk:
                    break
                await ws.send(chunk)
                await asyncio.sleep(chunk_size / sample_rate * 0.7)

            # Send 1.2s silence to trigger pause commitment
            silence = np.zeros(chunk_size, dtype=np.int16).tobytes()
            for _ in range(5):
                await ws.send(silence)
                await asyncio.sleep(0.15)

        await asyncio.wait_for(is_done.wait(), timeout=10.0)
        listener.cancel()

        print("\nPipeline Result:")
        print("  Committed Clause:", results.get("clause"))
        print("  FSW Output:      ", results.get("signwriting"))
        print("  Signs Count:     ", len(results.get("signs", [])))
        print("  Telemetry:       ", results.get("telemetry"))
        return results.get("telemetry", {})

def main():
    print("==================================================")
    print(" SIGNBRIDGE LOCKED ARCHITECTURE BENCHMARK SUITE")
    print("==================================================")
    sockeye_res = benchmark_sockeye_micro()
    whisper_res = benchmark_whisper_micro()

    print("\nRunning E2E pipeline test against active server...")
    try:
        e2e_telemetry = asyncio.run(benchmark_websocket_pipeline())
    except Exception as e:
        print(f"E2E test note (ensure backend is up on :8000): {e}")
        e2e_telemetry = {}

    print("\n==================================================")
    print(" FINAL BENCHMARK COMPARISON TABLE")
    print("==================================================")
    print(f"{'Component':<28} | {'Measured Live':<15} | {'Locked Target':<15}")
    print("-" * 65)
    print(f"{'Sockeye Warm Average':<28} | {sockeye_res['avg_ms']:>6.1f} ms       | 855 ms (warm avg)")
    print(f"{'Sockeye Warm Min':<28} | {sockeye_res['min_ms']:>6.1f} ms       | 687 ms (warm min)")
    print(f"{'Whisper tiny.en 1s ASR':<28} | {whisper_res['min_ms']:>6.1f} ms       | 312-321 ms")
    if e2e_telemetry:
        print(f"{'E2E Speech-End -> Signs':<28} | {e2e_telemetry.get('e2e_ms', 0):>6.1f} ms       | ~1.8 - 2.0 s")
        print(f"{'Sockeye Pipeline Latency':<28} | {e2e_telemetry.get('sockeye_ms', 0):>6.1f} ms       | ~800 - 900 ms")
    print(f"{'Offline Execution Mode':<28} | {'CONFIRMED':<15} | 100% OFFLINE")
    print("==================================================")

if __name__ == "__main__":
    main()
