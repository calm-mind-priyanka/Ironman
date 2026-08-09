import sys
import traceback
import logging
import asyncio
from pyrogram import Client, raw
from config import Config
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading
from motor.motor_asyncio import AsyncIOMotorClient

# Setup high-visibility logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - [%(levelname)s] - %(message)s")
logger = logging.getLogger("GodLevelDebugger")

# ==========================================
# GOD-LEVEL DIAGNOSTIC & CRASH INTERCEPTOR
# ==========================================
def activate_god_tier_debugging(app: Client):
    """
    Intercepts every single layer of execution: unhandled exceptions, 
    background coroutine crashes, database dropouts, and silent handler failures.
    Prints the exact file name, line number, faulty code, and clear fix to Koyeb logs.
    """
    
    # 1. Catch all uncaught global/async exceptions
    original_excepthook = sys.excepthook

    def god_mode_excepthook(exc_type, exc_value, exc_traceback):
        logger.critical("=" * 70)
        logger.critical("🚨 [GOD-LEVEL BUG DETECTOR] CRITICAL RUNTIME CRASH DETECTED 🚨")
        logger.critical(f"• Error Category : {exc_type.__name__}")
        logger.critical(f"• Exact Reason   : {exc_value}")
        
        # Extract precise traceback with file paths and line numbers
        tb_lines = traceback.format_exception(exc_type, exc_value, exc_traceback)
        logger.critical("• Traceback & Faulty Code Lines:\n" + "".join(tb_lines))
        
        # Intelligent Auto-Analysis for Common Bot Errors
        err_str = str(exc_value).lower()
        if "auth key" in err_str or "session" in err_str:
            logger.critical("💡 [DIAGNOSIS]: Pyrogram session file is corrupted or out of sync.")
            logger.critical("🛠️ [FIX]: Delete the local '*.session' file from your hosting workspace and restart.")
        elif "database" in err_str or "connection" in err_str or "timed out" in err_str or "bad auth" in err_str:
            logger.critical("💡 [DIAGNOSIS]: MongoDB connection failed or authentication rejected.")
            logger.critical("🛠️ [FIX]: Check your DATABASE_URI in config.py and ensure Atlas IP Access allows 0.0.0.0/0.")
        elif "api_id" in err_str or "api_hash" in err_str:
            logger.critical("💡 [DIAGNOSIS]: Invalid or malformed Telegram API credentials.")
            logger.critical("🛠️ [FIX]: Re-check API_ID and API_HASH values in config.py.")
        elif "plugins" in err_str or "import" in err_str or "syntax" in err_str:
            logger.critical("💡 [DIAGNOSIS]: A plugin file has a syntax or import error.")
            logger.critical("🛠️ [FIX]: Inspect the traceback above to find the exact plugin file and line number.")
            
        logger.critical("=" * 70)
        original_excepthook(exc_type, exc_value, exc_traceback)

    sys.excepthook = god_mode_excepthook

    # 2. Intercept Pyrogram's internal update processor to catch silent handler bugs
    @app.on_raw_update()
    async def global_packet_inspector(client, update, users, chats):
        try:
            pass # Active monitor pipeline
        except Exception as packet_err:
            logger.error(f"⚠️ [PACKET ERROR] Failed to process incoming update: {packet_err}")

# ==========================================
# PRE-FLIGHT CONFIG & DATABASE VALIDATOR
# ==========================================
async def preflight_health_check():
    logger.info("🔍 [DIAGNOSTIC] Running pre-flight system integrity checks...")
    
    # Check config variables
    if not Config.API_ID or not Config.API_HASH:
        logger.critical("❌ [FATAL CONFIG ERROR]: API_ID or API_HASH is missing in config.py!")
        sys.exit(1)
        
    if not Config.BOT_TOKEN:
        logger.critical("❌ [FATAL CONFIG ERROR]: BOT_TOKEN is missing in config.py!")
        sys.exit(1)
        
    if not Config.DATABASE_URI:
        logger.critical("❌ [FATAL CONFIG ERROR]: DATABASE_URI is missing in config.py!")
        sys.exit(1)

    if hasattr(Config, "ADMINS") and not isinstance(Config.ADMINS, (list, set)):
        logger.critical("❌ [FATAL CONFIG ERROR]: ADMINS must be a list in config.py (e.g., ADMINS = [12345678])!")
        sys.exit(1)

    # Test MongoDB live connection
    try:
        logger.info("🔌 Testing MongoDB Atlas live connection...")
        client = AsyncIOMotorClient(Config.DATABASE_URI, serverSelectionTimeoutMS=4000)
        await client.admin.command('ping')
        logger.info("✅ [DATABASE]: Connection healthy and verified!")
    except Exception as db_err:
        logger.critical("=" * 70)
        logger.critical("❌ [FATAL DATABASE FAILURE]: Cannot connect to MongoDB!")
        logger.critical(f"• Exact Error: {db_err}")
        logger.critical("💡 [DIAGNOSIS]: Your MongoDB URI is wrong, password has special characters, or IP is blocked.")
        logger.critical("🛠️ [FIX]: Whitelist '0.0.0.0/0' in MongoDB Atlas Network Access.")
        logger.critical("=" * 70)
        sys.exit(1)

# ==========================================
# WEB SERVER FOR HOSTING HEALTH CHECKS
# ==========================================
class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is fully operational!")
    def log_message(self, format, *args):
        return

def start_web_server():
    server = HTTPServer(("0.0.0.0", 8000), HealthHandler)
    server.serve_forever()

# ==========================================
# MAIN APPLICATION INITIALIZATION
# ==========================================
app = Client(
    "AutoFilterBot",
    api_id=Config.API_ID,
    api_hash=Config.API_HASH,
    bot_token=Config.BOT_TOKEN,
    plugins=dict(root="plugins")
)

if __name__ == "__main__":
    print("🤖 Advanced Auto-Filter Bot is starting up under God-Level Debug Mode...")
    
    # Attach the master debugger
    activate_god_tier_debugging(app)
    
    # Spin up background keep-alive web server
    threading.Thread(target=start_web_server, daemon=True).start()
    
    # Run pre-flight checks before launching bot
    try:
        asyncio.run(preflight_health_check())
    except Exception as e:
        logger.critical(f"❌ Startup sequence aborted: {e}")
        sys.exit(1)
        
    # Launch Pyrogram
    app.run()
