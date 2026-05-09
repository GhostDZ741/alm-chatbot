import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
ENV_PATH = BASE_DIR / ".env"
load_dotenv(ENV_PATH)


def getenv(key: str, default: str = "") -> str:
    return os.getenv(key, default)


# ── n8n (opcional, ya no es obligatorio) ──────────────────
N8N_PORT = getenv("N8N_PORT", "5678")
N8N_API_KEY = getenv("N8N_API_KEY", "")

# ── Groq ──────────────────────────────────────────────────
GROQ_API_KEY = getenv("GROQ_API_KEY", "")
GROQ_MODEL = getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
# alternativas gratuitas: mixtral-8x7b-32768, llama-3.1-8b-instant

# ── Meta - WhatsApp ───────────────────────────────────────
WHATSAPP_PHONE_NUMBER_ID = getenv("WHATSAPP_PHONE_NUMBER_ID", "")
WHATSAPP_ACCESS_TOKEN = getenv("WHATSAPP_ACCESS_TOKEN", "")
META_VERIFY_TOKEN = getenv("META_VERIFY_TOKEN", "alm_webhook_2024_secure")

# ── Meta - Instagram / Facebook ───────────────────────────
INSTAGRAM_PAGE_ACCESS_TOKEN = getenv("INSTAGRAM_PAGE_ACCESS_TOKEN", "")
FACEBOOK_PAGE_ID = getenv("FACEBOOK_PAGE_ID", "")
FACEBOOK_PAGE_ACCESS_TOKEN = getenv("FACEBOOK_PAGE_ACCESS_TOKEN", "")

# ── Google Sheets (opcional) ──────────────────────────────
GOOGLE_SHEETS_ID = getenv("GOOGLE_SHEETS_ID", "")
GOOGLE_SERVICE_ACCOUNT_EMAIL = getenv("GOOGLE_SERVICE_ACCOUNT_EMAIL", "")
GOOGLE_PRIVATE_KEY = getenv("GOOGLE_PRIVATE_KEY", "").replace("\\n", "\n")

# ── CEO / Agencia ─────────────────────────────────────────
CEO_WHATSAPP_NUMBER = getenv("CEO_WHATSAPP_NUMBER", "")
CALCOM_LINK = getenv("CALCOM_LINK", "")
AGENCY_NAME = getenv("AGENCY_NAME", "Arab Lion Marketing")
BOT_NAME = getenv("BOT_NAME", "Leo")

# ── Web ───────────────────────────────────────────────────
WEBHOOK_PATH = getenv("WEBHOOK_PATH", "/webhook/meta-bot")
PORT = int(getenv("PORT", "8000"))

# ── SQLite (si no hay Google Sheets) ──────────────────────
DATABASE_PATH = BASE_DIR / "data" / "alm_bot.db"
