import logging
from pyrogram import Client
from config import Config

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

app = Client(
    "AutoFilterBot",
    api_id=Config.API_ID,
    api_hash=Config.API_HASH,
    bot_token=Config.BOT_TOKEN,
    plugins=dict(root="plugins")
)

if __name__ == "__main__":
    print("🤖 Advanced Auto-Filter Bot is starting up...")
    app.run()
