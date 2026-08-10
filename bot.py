import asyncio
import importlib
import logging
import os
import sys
import traceback
import threading
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
# Pyrogram Smart Plugins is the ONLY plugin loader used by this bot.
# Do not manually import plugin modules here; doing both can register
# overlapping handlers twice. admin_actions.py is excluded because it
# duplicates the handlers already implemented in admin.py.

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

    missing = [
        name
        for name, value in required.items()
        if not value
    ]

    if missing:
        raise RuntimeError(
            "Missing required configuration: "
            + ", ".join(missing)
        )

    if not Config.DATABASE_URI_2:
        raise RuntimeError(
            "DATABASE_URI_2 is missing"
        )


# ============================================================
# MONGODB CHECK
# ============================================================

async def check_databases():

    logger.info(
        "🔌 Checking MongoDB connection 1..."
    )

    client1 = AsyncIOMotorClient(
        Config.DATABASE_URI,
        serverSelectionTimeoutMS=8000,
        connectTimeoutMS=8000,
    )

    try:

        await client1.admin.command("ping")

        logger.info(
            "✅ MongoDB connection 1 OK"
        )

    finally:

        client1.close()


    if Config.DATABASE_URI_2 != Config.DATABASE_URI:

        logger.info(
            "🔌 Checking MongoDB connection 2..."
        )

        client2 = AsyncIOMotorClient(
            Config.DATABASE_URI_2,
            serverSelectionTimeoutMS=8000,
            connectTimeoutMS=8000,
        )

        try:

            await client2.admin.command("ping")

            logger.info(
                "✅ MongoDB connection 2 OK"
            )

        finally:

            client2.close()

    else:

        logger.info(
            "ℹ️ DATABASE_URI_2 is the same as DATABASE_URI"
        )


# ============================================================
# PLUGIN CHECK
# ============================================================
# Handler registration is performed by Pyrogram's Smart Plugin loader
# when the Client starts. Manual imports are intentionally avoided.

# ============================================================
# KOYEB HEALTH SERVER
# ============================================================

class HealthHandler(
    BaseHTTPRequestHandler
):

    def do_GET(self):

        status = (
            200
            if _bot_started
            else 503
        )

        self.send_response(
            status
        )

        self.send_header(
            "Content-Type",
            "text/plain; charset=utf-8"
        )

        self.end_headers()

        if _bot_started:

            self.wfile.write(
                b"Telegram bot is running"
            )

        else:

            self.wfile.write(
                b"Telegram bot is starting"
            )

    def log_message(
        self,
        format,
        *args
    ):

        return


# ============================================================
# START HEALTH SERVER
# ============================================================

def start_web_server():

    port = int(
        os.environ.get(
            "PORT",
            "8000"
        )
    )

    server = ThreadingHTTPServer(
        (
            "0.0.0.0",
            port
        ),
        HealthHandler
    )

    logger.info(
        "🌐 Health server listening on port %s",
        port
    )

    server.serve_forever()


# ============================================================
# PYROGRAM CLIENT
# ============================================================

app = Client(
    "AutoFilterBot",
    api_id=Config.API_ID,
    api_hash=Config.API_HASH,
    bot_token=Config.BOT_TOKEN,
    plugins={
        "root": "plugins",
        "exclude": ["admin_actions"],
    },
)


# ============================================================
# STARTUP CHECKS
# ============================================================

async def startup_checks():

    logger.info(
        "🔍 Checking configuration..."
    )

    validate_config()

    logger.info(
        "✅ Configuration OK"
    )

    await check_databases()


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    logger.info("🤖 AutoFilterBot starting...")

    threading.Thread(
        target=start_web_server,
        daemon=True,
    ).start()

    try:
        validate_config()
        logger.info("✅ Configuration OK")

        # Run database checks on the same loop Pyrogram will use.
        # app.run() starts Pyrogram and keeps the process alive.
        app.run(startup_checks())

    except KeyboardInterrupt:
        logger.info("🛑 Shutdown requested")
    except Exception:
        logger.critical("❌ Bot startup failed", exc_info=True)
        sys.exit(1)
    finally:
        _bot_started = False
