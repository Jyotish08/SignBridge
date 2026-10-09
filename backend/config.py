import os
from typing import List
from dotenv import load_dotenv
import json

# Load environment variables from .env file
load_dotenv()

# Enforce Offline Mode for HuggingFace Hub and Transformers
os.environ["HF_HUB_OFFLINE"] = os.getenv("HF_HUB_OFFLINE", "1")
os.environ["TRANSFORMERS_OFFLINE"] = os.getenv("TRANSFORMERS_OFFLINE", "1")

class Config:
    """Configuration class for the SignBridge backend"""
    
    # Server Configuration
    HOST: str = os.getenv("HOST", "127.0.0.1")
    PORT: int = int(os.getenv("PORT", "8000"))
    DEBUG: bool = os.getenv("DEBUG", "true").lower() == "true"
    
    # API Keys and External Services
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    GROQ_API_URL: str = os.getenv("GROQ_API_URL", "https://api.groq.com/openai/v1/chat/completions")
    
    # Pose Generation API
    POSE_API_URL: str = os.getenv("POSE_API_URL", "")
    
    # Whisper Model Configuration
    WHISPER_MODEL: str = os.getenv("WHISPER_MODEL", "tiny.en")
    WHISPER_DEVICE: str = os.getenv("WHISPER_DEVICE", "cpu")
    WHISPER_COMPUTE_TYPE: str = os.getenv("WHISPER_COMPUTE_TYPE", "int8")

    # Streaming & VAD Parameters
    VAD_THRESHOLD: float = float(os.getenv("VAD_THRESHOLD", "0.5"))
    PAUSE_THRESHOLD_SEC: float = float(os.getenv("PAUSE_THRESHOLD_SEC", "0.8"))
    MIN_CLAUSE_WORDS: int = int(os.getenv("MIN_CLAUSE_WORDS", "2"))
    MAX_CLAUSE_SEC: float = float(os.getenv("MAX_CLAUSE_SEC", "15.0"))
    N_STABLE_AGREEMENT: int = int(os.getenv("N_STABLE_AGREEMENT", "3"))

    
    # CORS Configuration
    @classmethod
    def get_cors_origins(cls) -> List[str]:
        """Parse CORS origins from environment variable"""
        cors_origins = os.getenv("CORS_ORIGINS", '["*"]')
        try:
            # Try to parse as JSON first
            return json.loads(cors_origins)
        except json.JSONDecodeError:
            # Fallback to comma-separated string
            return [origin.strip() for origin in cors_origins.strip('[]').split(',') if origin.strip()]
    
    CORS_ALLOW_CREDENTIALS: bool = os.getenv("CORS_ALLOW_CREDENTIALS", "true").lower() == "true"
    CORS_ALLOW_METHODS: List[str] = ["*"]
    CORS_ALLOW_HEADERS: List[str] = ["*"]
    
    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "DEBUG")
    
    @classmethod
    def validate(cls) -> None:
        """Validate required configuration values"""
        if not cls.GROQ_API_KEY:
            print("Warning: GROQ_API_KEY not set. Text simplification will not work.")
        
        if not cls.POSE_API_URL:
            print("Warning: POSE_API_URL not set. Pose generation will not work.")
    
    @classmethod
    def get_backend_url(cls) -> str:
        """Get the backend URL for frontend configuration"""
        return f"http://{cls.HOST}:{cls.PORT}"

# Create a global config instance
config = Config()

# Validate configuration on import
config.validate() 