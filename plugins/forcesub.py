from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from motor.motor_asyncio import AsyncIOMotorClient
from config import Config
import logging

logger = logging.getLogger(__name__)

try:
    db_client = AsyncIOMotorClient(Config.DATABASE_URI)
    db = db_client[getattr(Config, "DATABASE_NAME", "AutoFilterBot")]
    forcesub_col = db["forcesub_channels"]
except Exception as e:
    logger.error(f"Failed to initialize forcesub collection in forcesub.py: {e}")

USER_FS_STATE = {}

@Client.on_callback_query(filters.regex("^set_force_channel$"))
async def force_channel_menu(client: Client, query: CallbackQuery):
    try:
        chat_id = query.message.chat.id
        cursor = forcesub_col.find({"chat_id": chat_id})
        channels = await cursor.to_list(length=10)

        text = "👥 **Multi-Force Subscribe Settings**\n\nLinked channels:\n"
        if channels:
            for idx, c in enumerate(channels, 1):
                text += f"{idx}. {c.get('title', 'Channel')} (`{c.get('channel_id', 'N/A')}`)\n"
        else:
            text += "No channels added yet ❌\n"

        buttons = [
            [InlineKeyboardButton("➕ Add Channel", callback_data="fs_add"), InlineKeyboardButton("🗑️ Remove", callback_data="fs_remove")],
            [InlineKeyboardButton("<< Back", callback_data="back_to_settings")]
        ]
        await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(buttons))
    except Exception as err:
        logger.error(f"🚨 [CALLBACK ERROR in forcesub.py]: force_channel_menu failed", exc_info=True)
        await query.answer("⚠️ Failed to load force subscription menu.", show_alert=True)

@Client.on_callback_query(filters.regex("^fs_add$"))
async def prompt_fs_add(client: Client, query: CallbackQuery):
    try:
        USER_FS_STATE[query.from_user.id] = {"chat_id": query.message.chat.id}
        await query.message.reply_text("Send Channel ID and Invite Link separated by comma (`,`). Example:\n`-100123, https://t.me/link`")
        await query.answer()
    except Exception as err:
        logger.error(f"🚨 [CALLBACK ERROR in forcesub.py]: prompt_fs_add failed", exc_info=True)
        await query.answer("⚠️ An error occurred.", show_alert=True)
