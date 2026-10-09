import os
from huggingface_hub import snapshot_download
from faster_whisper import WhisperModel

def download_models():
    print("Downloading faster-whisper tiny.en model...")
    # This downloads to the local cache, allowing offline usage later.
    model = WhisperModel("tiny.en", device="cpu", compute_type="int8", download_root="./models/faster-whisper")
    print("faster-whisper downloaded successfully.")

    print("Downloading Sockeye model...")
    sockeye_path = snapshot_download(
        repo_id="sign/sockeye-text-to-factored-signwriting",
        local_dir="./models/sockeye-text-to-factored-signwriting"
    )
    print(f"Sockeye model downloaded to {sockeye_path}")

if __name__ == "__main__":
    download_models()
