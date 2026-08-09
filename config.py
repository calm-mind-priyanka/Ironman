import os

class Config:
    API_ID = int(os.environ.get("API_ID", "123456"))
    API_HASH = os.environ.get("API_HASH", "your_api_hash")
    BOT_TOKEN = os.environ.get("BOT_TOKEN", "your_bot_token")
    
    # Dual Database Active Mode URIs (DB1 & DB2)
    DATABASE_URI = os.environ.get("DATABASE_URI", "mongodb+srv://cluster0...")
    DATABASE_URI_2 = os.environ.get("DATABASE_URI_2", "mongodb+srv://cluster1...")
    DATABASE_NAME = os.environ.get("DATABASE_NAME", "Cluster0")
    
    ADMINS = [int(admin) for admin in os.environ.get("ADMINS", "12345678").split()]
    LOG_CHANNEL = int(os.environ.get("LOG_CHANNEL", "-100123456789"))
