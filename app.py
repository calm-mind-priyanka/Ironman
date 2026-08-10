import asyncio
import logging
import threading
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from zoneinfo import ZoneInfo

from pyrogram import Client, idle

from config import Config
from db import ping, ensure_indexes


# --------------------------------------------------
# LOGGING
# --------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - [%(levelname)s] - AutoFilterBot - %(message)s"
)

log = logging.getLogger("AutoFilterBot")


# --------------------------------------------------
# HEALTH SERVER
# --------------------------------------------------

class Health(BaseHTTPRequestHandler):
    ready = False

    def do_GET(self):
        body = b"OK" if Health.ready else b"STARTING"

        self.send_response(200 if Health.ready else 503)
        self.send_header("Content-Type", "text/plain")
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *args):
        pass


def health_server():
    server = ThreadingHTTPServer(
        ("0.0.0.0", Config.PORT),
        Health
    )

    log.info(
        "🌐 Health server listening on port %s",
        Config.PORT
    )

    server.serve_forever()


# --------------------------------------------------
# PYROGRAM CLIENT
# --------------------------------------------------

app = Client(
    "fresh_autofilter",
    api_id=Config.API_ID,
    api_hash=Config.API_HASH,
    bot_token=Config.BOT_TOKEN,
    workers=16,
)


# --------------------------------------------------
# REGISTER HANDLERS
# --------------------------------------------------

def register_all():
    """
    Register every handler exactly once.
    """

    from handlers import (
        start,
        admin,
        settings,
        forcesub,
        index,
        search,
        shortlink,
        payment,
        autofilter,
    )

    modules = (
        start,
        admin,
        settings,
        forcesub,
        index,
        search,
        shortlink,
        payment,
        autofilter,
    )

    for module in modules:
        module.register(app)


# --------------------------------------------------
# BOT RESTART MESSAGE
# --------------------------------------------------

async def send_restart_message():
    """
    Send a startup/restart notification to LOG_CHANNEL
    after Telegram has successfully connected.
    """

    if not Config.LOG_CHANNEL:
        log.warning(
            "⚠️ LOG_CHANNEL is not configured. "
            "Restart message will not be sent."
        )
        return

    try:
        now = datetime.now(
            ZoneInfo("Asia/Kolkata")
        )

        text = (
            "**✅ ʙᴏᴛ ʀᴇꜱᴛᴀʀᴛᴇᴅ!**\n"
            "🤖 **ʙᴏᴛ :** **AuTo-FiLteR- BoT**\n"
            f"📅 **ᴅᴀᴛᴇ:** `{now.strftime('%Y-%m-%d')}`\n"
            f"⏰ **ᴛɪᴍᴇ:** `{now.strftime('%H:%M:%S')}`\n"
            "🌐 **ᴢᴏɴᴇ:** `ᴀꜱɪᴀ/ᴋᴏʟᴋᴀᴛᴀ`\n"
            "🛠️ **ᴠᴇʀꜱɪᴏɴ:** `v4.3 [ ꜱᴛᴀʙʟᴇ ]`"
        )

        await app.send_message(
            Config.LOG_CHANNEL,
            text
        )

        log.info(
            "✅ Restart message sent to LOG_CHANNEL"
        )

    except Exception:
        log.exception(
            "❌ Failed to send restart message to LOG_CHANNEL"
        )


# --------------------------------------------------
# STARTUP
# --------------------------------------------------

async def startup():

    log.info(
        "🤖 Fresh AutoFilter Bot starting..."
    )

    # MongoDB
    log.info(
        "🔍 Checking MongoDB..."
    )

    await ping()
    await ensure_indexes()

    log.info(
        "✅ MongoDB OK"
    )

    # Koyeb health server
    threading.Thread(
        target=health_server,
        daemon=True
    ).start()

    # Telegram handlers
    register_all()

    log.info(
        "🧩 All handlers registered once"
    )

    # Telegram
    log.info(
        "🔌 Starting Telegram client..."
    )

    await app.start()

    # Confirm Telegram connection
    me = await app.get_me()

    Health.ready = True

    log.info(
        "✅ Telegram connected as @%s (id=%s)",
        me.username or me.first_name,
        me.id
    )

    # Send restart notification ONLY after Telegram is connected
    await send_restart_message()

    log.info(
        "✅ Bot is ready to receive updates"
    )


# --------------------------------------------------
# SHUTDOWN
# --------------------------------------------------

async def shutdown():

    Health.ready = False

    try:
        await app.stop()
    except Exception:
        pass


# --------------------------------------------------
# MAIN
# --------------------------------------------------

if __name__ == "__main__":

    try:

        asyncio.run(startup())

        # Keep Pyrogram running
        idle()

    except KeyboardInterrupt:

        log.info(
            "Stopping..."
        )

    except Exception:

        log.exception(
            "FATAL STARTUP ERROR"
        )

        raise

    finally:

        try:
            asyncio.run(
                shutdown()
            )
        except Exception:
            pass
