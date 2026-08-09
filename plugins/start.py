from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from motor.motor_asyncio import AsyncIOMotorClient
from config import Config

db_client = AsyncIOMotorClient(Config.DATABASE_URI)
db = db_client[Config.DATABASE_NAME]
users_col = db["users"]

@Client.on_message(filters.command("start") & filters.private)
async def start_cmd(client: Client, message: Message):
    user_id = message.from_user.id
    if not await users_col.find_one({"user_id": user_id}):
        await users_col.insert_one({"user_id": user_id, "name": message.from_user.first_name})

    text = f"👋 Hello **{message.from_user.first_name}**!\n\nI am your Advanced Auto-Filter Bot.\n🎯 Send me any movie name to search."
    buttons = [
        [InlineKeyboardButton("🔍 Search Here", switch_inline_query_current_chat=""), InlineKeyboardButton("💎 My Plan", callback_data="my_plan_menu")],
        [InlineKeyboardButton("⚙️ Help", callback_data="help_menu")]
    ]
    await message.reply_text(text, reply_markup=InlineKeyboardMarkup(buttons))
