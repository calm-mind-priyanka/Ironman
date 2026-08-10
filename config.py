import os

def required(name):
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value

class Config:
    API_ID = int(required("API_ID"))
    API_HASH = required("API_HASH")
    BOT_TOKEN = required("BOT_TOKEN")
    DATABASE_URI = required("DATABASE_URI")
    DATABASE_URI_2 = os.getenv("DATABASE_URI_2", DATABASE_URI)
    DATABASE_NAME = os.getenv("DATABASE_NAME", "AutoFilterBot")
    ADMINS = {int(x) for x in os.getenv("ADMINS", "").replace(",", " ").split() if x.strip().lstrip("-").isdigit()}
    LOG_CHANNEL = int(os.getenv("LOG_CHANNEL", "0"))
    AUTO_INDEX_CHANNEL = int(os.getenv("AUTO_INDEX_CHANNEL", "0"))
    RESULTS_PER_PAGE = int(os.getenv("RESULTS_PER_PAGE", "10"))
    PORT = int(os.getenv("PORT", "8000"))
    DELETE_AFTER = int(os.getenv("DELETE_AFTER", "0"))
    SEARCH_COOLDOWN = float(os.getenv("SEARCH_COOLDOWN", "0"))
