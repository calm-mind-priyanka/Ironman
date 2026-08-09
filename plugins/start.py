from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from motor.motor_asyncio import AsyncIOMotorClient
from config import Config
import logging

logger = logging.getLogger(__name__)

# Safely establish database connection references
try:
    db_client = AsyncIOMotorClient(Config.DATABASE_URI)
    db = db_client[getattr(Config, "DATABASE_NAME", "AutoFilterBot")]
    users_col = db["users"]
except Exception as e:
    logger.error(f"Failed to initialize users collection in start.py: {e}")

@Client.on_message(filters.command("start") & filters.private)
async def start_cmd(client: Client, message: Message):
    try:
        user_id = message.from_user.id
        
        # Safe database check and user insertion
        if 'users_col' in globals() and users_col is not None:
            existing_user = await users_col.find_one({"user_id": user_id})
            if not existing_user:
                await users_col.insert_one({
                    "user_id": user_id, 
                    "name": message.from_user.first_name
                })

        text = f"👋 Hello **{message.from_user.first_name}**!\n\nI am your Advanced Auto-Filter Bot.\n🎯 Send me any movie name to search."
        buttons = [
            [InlineKeyboardButton("🔍 Search Here", switch_inline_query_current_chat=""), InlineKeyboardButton("💎 My Plan", callback_data="my_plan_menu")],
            [InlineKeyboardButton("⚙️ Help", callback_data="help_menu")]
        ]
        await message.reply_text(text, reply_markup=InlineKeyboardMarkup(buttons))
        
    except Exception as err:
        logger.error(f"🚨 [CRITICAL COMMAND ERROR in start.py]: /start failed for user {message.from_user.id}")
        logger.error(f"• Reason: {err}", exc_info=True)
        await message.reply_text("⚠️ An internal error occurred while processing your command. The event has been logged.")
