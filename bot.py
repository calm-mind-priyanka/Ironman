import asyncio
import importlib
import logging
import os
import sys
import threading
import traceback
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from motor.motor_asyncio import AsyncIOMotorClient
from pyrogram import Client

from config import Config

# ============================================================
# LOGGING
# ============================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - [%(levelname)s] - %(name)s - %(message)s",
)

logger = logging.getLogger("AutoFilterBot")

# ============================================================
# PLUGINS
# ============================================================

PLUGIN_MODULES = [
    "plugins.start",
    "plugins.settings",
    "plugins.autofilter",
    "plugins.index",
    "plugins.search",
    "plugins.forcesub",
    "plugins.shortlink",
    "plugins.p_s_qr",
    "plugins.admin",
]

# ============================================================
# BOT STATUS
# ============================================================

_bot_started = False

# ============================================================
# CONFIGURATION CHECK
# ============================================================

def validate_config():
    required = {
        "API_ID": Config.API_ID,
        "API_HASH": Config.API_HASH,
        "BOT_TOKEN": Config.BOT_TOKEN,
        "DATABASE_URI": Config.DATABASE_URI,
        "DATABASE_NAME": Config.DATABASE_NAME,
    }

    missing = [name for name, value in required.items() if not value]

    if missing:
        raise RuntimeError("Missing required configuration: " + ", ".join(missing))

    if not Config.DATABASE_URI_2:
        raise RuntimeError("DATABASE_URI_2 is missing")

# ============================================================
# MONGODB CHECK
# ============================================================

async def check_databases():
    logger.info("🔌 Checking MongoDB connection 1...")
    
    client1 = AsyncIOMotorClient(
        Config.DATABASE_URI,
        serverSelectionTimeoutMS=8000,
        connectTimeoutMS=8000,
    )
    
    try:
        await client1.admin.command("ping")
        logger.info("✅ MongoDB connection 1 OK")
    finally:
        client1.close()

    if Config.DATABASE_URI_2 != Config.DATABASE_URI:
        logger.info("🔌 Checking MongoDB connection 2...")
        
        client2 = AsyncIOMotorClient(
            Config.DATABASE_URI_2,
            serverSelectionTimeoutMS=8000,
            connectTimeoutMS=8000,
        )
        
        try:
            await client2.admin.command("ping")
            logger.info("✅ MongoDB connection 2 OK")
        finally:
            client2.close()
    else:
        logger.info("ℹ️ DATABASE_URI_2 is the same as DATABASE_URI")

# ============================================================
# PLUGIN CHECK
# ============================================================

def check_plugins():
    logger.info("🔎 Checking plugin imports...")
    failed = []

    for module_name in PLUGIN_MODULES:
        try:
            importlib.import_module(module_name)
            logger.info("✅ Plugin import OK: %s", module_name)
        except Exception:
            failed.append(module_name)
            logger.exception("❌ Plugin import FAILED: %s", module_name)

    if failed:
        raise RuntimeError("Plugin import failed: " + ", ".join(failed))

    logger.info("✅ All plugins imported successfully")

# ============================================================
# KOYEB HEALTH SERVER
# ============================================================

class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        status = 200 if _bot_started else 503
        self.send_response(status)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.end_headers()

        if _bot_started:
            self.wfile.write(b"Telegram bot is running")
        else:
            self.wfile.write(b"Telegram bot is starting")

    def log_message(self, format, *args):
        return

# ============================================================
# START HEALTH SERVER
# ============================================================

def start_web_server():
    port = int(os.environ.get("PORT", "8000"))
    server = ThreadingHTTPServer(("0.0.0.0", port), HealthHandler)
    logger.info("🌐 Health server listening on port %s", port)
    server.serve_forever()

# ============================================================
# PYROGRAM CLIENT
# ============================================================

app = Client(
    "AutoFilterBot",
    api_id=Config.API_ID,
    api_hash=Config.API_HASH,
    bot_token=Config.BOT_TOKEN,
    plugins={"root": "plugins"},
)

# ============================================================
# STARTUP CHECKS
# ============================================================

async def startup_checks():
    logger.info("🔍 Checking configuration...")
    validate_config()
    logger.info("✅ Configuration OK")
    check_plugins()
    await check_databases()

# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":
    logger.info("🤖 AutoFilterBot starting...")

    # Start Koyeb health server
    threading.Thread(target=start_web_server, daemon=True).start()

    # Create ONE event loop
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    try:
        # Startup checks
        loop.run_until_complete(startup_checks())

        # Start Pyrogram
        logger.info("🚀 Starting Pyrogram...")
        loop.run_until_complete(app.start())

        # Bot is running now
        _bot_started = True
        logger.info("✅ Pyrogram started successfully")
        logger.info("🤖 AutoFilterBot is now ONLINE")

        # Keep event loop alive
        loop.run_forever()

    except KeyboardInterrupt:
        logger.info("🛑 Shutdown requested")
    except Exception:
        logger.critical("❌ Pyrogram stopped/crashed")
        logger.critical(traceback.format_exc())
        sys.exit(1)
    finally:
        # Stop Pyrogram cleanly
        try:
            if app.is_connected:
                loop.run_until_complete(app.stop())
        except Exception:
            logger.exception("⚠️ Error while stopping Pyrogram")

        # Close event loop
        try:
            loop.close()
        except Exception:
            pass
