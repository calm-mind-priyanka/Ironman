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

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - [%(levelname)s] - %(name)s - %(message)s",
)

logger = logging.getLogger("AutoFilterBot")

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

_bot_started = False


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


async def check_databases():
    logger.info("🔌 Checking MongoDB connection 1...")
    client1 = AsyncIOMotorClient(
        Config.DATABASE_URI,
        serverSelectionTimeoutMS=8000,
        connectTimeoutMS=8000,
    )
    await client1.admin.command("ping")
    logger.info("✅ MongoDB connection 1 OK")

    if Config.DATABASE_URI_2 != Config.DATABASE_URI:
        logger.info("🔌 Checking MongoDB connection 2...")
        client2 = AsyncIOMotorClient(
            Config.DATABASE_URI_2,
            serverSelectionTimeoutMS=8000,
            connectTimeoutMS=8000,
        )
        await client2.admin.command("ping")
        logger.info("✅ MongoDB connection 2 OK")
    else:
        logger.info("ℹ️ DATABASE_URI_2 is the same as DATABASE_URI")


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


def start_web_server():
    port = int(os.environ.get("PORT", "8000"))
    server = ThreadingHTTPServer(("0.0.0.0", port), HealthHandler)
    logger.info("🌐 Health server listening on port %s", port)
    server.serve_forever()


app = Client(
    "AutoFilterBot",
    api_id=Config.API_ID,
    api_hash=Config.API_HASH,
    bot_token=Config.BOT_TOKEN,
    plugins={"root": "plugins"},
)


async def startup_checks():
    logger.info("🔍 Checking configuration...")
    validate_config()
    logger.info("✅ Configuration OK")
    check_plugins()
    await check_databases()


if __name__ == "__main__":
    logger.info("🤖 AutoFilterBot starting...")

    threading.Thread(target=start_web_server, daemon=True).start()

    try:
        asyncio.run(startup_checks())
    except Exception as exc:
        logger.critical("❌ Startup checks failed: %s", exc)
        logger.critical(traceback.format_exc())
        sys.exit(1)

    try:
        logger.info("🚀 Starting Pyrogram...")
        app.run()
        _bot_started = True
    except Exception:
        logger.critical("❌ Pyrogram stopped/crashed")
        logger.critical(traceback.format_exc())
        sys.exit(1)
