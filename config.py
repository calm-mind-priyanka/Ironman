import os

class Config:
    API_ID = int(os.environ.get("API_ID", "24222039"))
    API_HASH = os.environ.get("API_HASH", "6dd2dc70434b2f577f76a2e993135662")
    BOT_TOKEN = os.environ.get("BOT_TOKEN", "7905740502:AAEbesPWE30nXZwcAibymVfvi4gZVvJTyuI")
    
    # Dual Database Active Mode URIs (DB1 & DB2)
    DATABASE_URI = os.environ.get("DATABASE_URI", "mongodb+srv://rajibchaun_db_user:Fa1SV672h6xrxFxR@cluster0.pfgtal2.mongodb.net/?appName=Cluster0")
    DATABASE_URI_2 = os.environ.get("DATABASE_URI_2", "mongodb+srv://rajibchaun_db_user:Fa1SV672h6xrxFxR@cluster0.pfgtal2.mongodb.net/?appName=Cluster0")
    DATABASE_NAME = os.environ.get("DATABASE_NAME", "Cluster0")
    
    ADMINS = [int(admin) for admin in os.environ.get("ADMINS", "6046055058").split()]
    LOG_CHANNEL = int(os.environ.get("LOG_CHANNEL", "-100123456789"))
    
    # 📌 Hardcoded Auto-Index Channel ID (Replace with your actual channel ID)
    AUTO_INDEX_CHANNEL = int(os.environ.get("AUTO_INDEX_CHANNEL", "-1002694840394"))
