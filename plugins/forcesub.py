from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from motor.motor_asyncio import AsyncIOMotorClient
from config import Config

db_client = AsyncIOMotorClient(Config.DATABASE_URI)
db = db_client[Config.DATABASE_NAME]
forcesub_col = db["forcesub_channels"]
USER_FS_STATE = {}

@Client.on_callback_query(filters.regex("^set_force_channel$"))
async def force_channel_menu(client: Client, query: CallbackQuery):
    chat_id = query.message.chat.id
    cursor = forcesub_col.find({"chat_id": chat_id})
    channels = await cursor.to_list(length=10)

    text = "👥 **Multi-Force Subscribe Settings**\n\nLinked channels:\n"
    if channels:
        for idx, c in enumerate(channels, 1):
            text += f"{idx}. {c.get('title', 'Channel')} (`{c['channel_id']}`)\n"
    else:
        text += "No channels added yet ❌\n"

    buttons = [
        [InlineKeyboardButton("➕ Add Channel", callback_data="fs_add"), InlineKeyboardButton("🗑️ Remove", callback_data="fs_remove")],
        [InlineKeyboardButton("<< Back", callback_data="back_to_settings")]
    ]
    await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(buttons))

@Client.on_callback_query(filters.regex("^fs_add$"))
async def prompt_fs_add(client: Client, query: CallbackQuery):
    USER_FS_STATE[query.from_user.id] = {"chat_id": query.message.chat.id}
    await query.message.reply_text("Send Channel ID and Invite Link separated by comma (`,`). Example:\n`-100123, https://t.me/link`")
