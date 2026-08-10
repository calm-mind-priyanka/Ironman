import logging
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pyrogram import Client, idle

from config import Config
from db import ping, ensure_indexes

logging.basicConfig(level=logging.INFO, format="%(asctime)s - [%(levelname)s] - AutoFilterBot - %(message)s")
log=logging.getLogger("AutoFilterBot")

class Health(BaseHTTPRequestHandler):
    ready=False
    def do_GET(self):
        body=b"OK" if Health.ready else b"STARTING"
        self.send_response(200 if Health.ready else 503)
        self.send_header("Content-Type","text/plain")
        self.end_headers()
        self.wfile.write(body)
    def log_message(self,*args): pass

def health_server():
    server=ThreadingHTTPServer(("0.0.0.0",Config.PORT),Health)
    log.info("🌐 Health server listening on port %s",Config.PORT)
    server.serve_forever()

app=Client(
    "fresh_autofilter",
    api_id=Config.API_ID,
    api_hash=Config.API_HASH,
    bot_token=Config.BOT_TOKEN,
    workers=16,
)

def register_all():
    # Explicit, deterministic registration: every handler is registered exactly once.
    from handlers import start, admin, settings, forcesub, index, search, shortlink, payment, autofilter
    for module in (start, admin, settings, forcesub, index, search, shortlink, payment, autofilter):
        module.register(app)

async def startup():
    log.info("🤖 Fresh AutoFilter Bot starting...")
    log.info("🔍 Checking MongoDB...")
    await ping()
    await ensure_indexes()
    log.info("✅ MongoDB OK")
    threading.Thread(target=health_server, daemon=True).start()

    register_all()
    log.info("🧩 All handlers registered once")

    log.info("🔌 Starting Telegram client...")
    await app.start()
    me=await app.get_me()
    Health.ready=True
    log.info("✅ Telegram connected as @%s (id=%s)",me.username or me.first_name,me.id)
    log.info("✅ Bot is ready to receive updates")

async def shutdown():
    Health.ready=False
    await app.stop()

if __name__=="__main__":
    import asyncio
    try:
        asyncio.run(startup())
        idle()
    except KeyboardInterrupt:
        log.info("Stopping...")
    except Exception:
        log.exception("FATAL STARTUP ERROR")
        raise
    finally:
        try: asyncio.run(shutdown())
        except Exception: pass
