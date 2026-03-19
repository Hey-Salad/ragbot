import os
from dotenv import load_dotenv

load_dotenv()


def _get_bool(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


class Config:
    # Hugging Face Configuration
    HUGGINGFACE_API_TOKEN = os.getenv("HUGGINGFACE_API_TOKEN")
    HUGGINGFACE_MODEL = os.getenv("HUGGINGFACE_MODEL", "openai/gpt-oss-20b:fireworks-ai")
    EMBEDDING_BACKEND = os.getenv("EMBEDDING_BACKEND", "auto")

    # Slack Configuration
    SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN")
    SLACK_SIGNING_SECRET = os.getenv("SLACK_SIGNING_SECRET")
    SLACK_APP_TOKEN = os.getenv("SLACK_APP_TOKEN")

    # Twilio Configuration
    TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
    TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
    TWILIO_PHONE_NUMBER = os.getenv("TWILIO_PHONE_NUMBER")
    VALIDATE_TWILIO_SIGNATURES = _get_bool("VALIDATE_TWILIO_SIGNATURES", True)
    PUBLIC_BASE_URL = os.getenv("PUBLIC_BASE_URL")
    ALLOWED_TWILIO_MEDIA_HOSTS = tuple(
        host.strip()
        for host in os.getenv(
            "ALLOWED_TWILIO_MEDIA_HOSTS", "api.twilio.com,mms.twiliocdn.com"
        ).split(",")
        if host.strip()
    )

    # Application Configuration
    PORT = int(os.getenv("PORT", 8000))
    HOST = os.getenv("HOST", "127.0.0.1")
    DEBUG = _get_bool("DEBUG", False)
    ENABLE_DOCS = _get_bool("ENABLE_DOCS", DEBUG)
    API_KEY = os.getenv("API_KEY")
    CHROMA_PERSIST_DIRECTORY = os.getenv("CHROMA_PERSIST_DIRECTORY", "./chroma_db")
    UPLOAD_DIRECTORY = os.getenv("UPLOAD_DIRECTORY", "./uploads")
    USER_DATA_DIRECTORY = os.getenv("USER_DATA_DIRECTORY", "./user_data")
    REQUEST_TIMEOUT_SECONDS = float(os.getenv("REQUEST_TIMEOUT_SECONDS", "15"))
    MAX_UPLOAD_SIZE_BYTES = int(os.getenv("MAX_UPLOAD_SIZE_BYTES", "5242880"))
    MAX_SCRAPE_BYTES = int(os.getenv("MAX_SCRAPE_BYTES", "250000"))
    MAX_TEXT_CHARS = int(os.getenv("MAX_TEXT_CHARS", "100000"))

    # RAG Configuration
    CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "1000"))
    CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "200"))
    TOP_K_RESULTS = int(os.getenv("TOP_K_RESULTS", "5"))

    @classmethod
    def validate(cls):
        """Validate required configuration"""
        if cls.CHUNK_SIZE <= cls.CHUNK_OVERLAP:
            raise ValueError("CHUNK_SIZE must be greater than CHUNK_OVERLAP")
        if cls.MAX_UPLOAD_SIZE_BYTES <= 0:
            raise ValueError("MAX_UPLOAD_SIZE_BYTES must be positive")
        if cls.MAX_SCRAPE_BYTES <= 0:
            raise ValueError("MAX_SCRAPE_BYTES must be positive")
        return True
