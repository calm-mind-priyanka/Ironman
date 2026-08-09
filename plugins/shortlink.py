import asyncio
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from motor.motor_asyncio import AsyncIOMotorClient
from config import Config
import logging

logger = logging.getLogger(__name__)

try:
    db_client = AsyncIOMotorClient(Config.DATABASE_URI)
    db = db_client[getattr(Config, "DATABASE_NAME", "AutoFilterBot")]
    shortlink_col = db["shortlinks"]
except Exception as e:
    logger.error(f"Failed to initialize shortlinks collection in shortlink.py: {e}")

USER_STATE = {}

@Client.on_callback_query(filters.regex("^set_shortlink_menu$"))
async def sl_menu(client: Client, query: CallbackQuery):
    try:
        chat_id = query.message.chat.id
        data = await shortlink_col.find_one({"chat_id": chat_id}) or {}
        text = f"🔗 **Shortlink Settings**\n\n• **1st Shortlink:** `{data.get('site1', 'Not Set ❌')}`\n• **2nd Shortlink:** `{data.get('site2', 'Not Set ❌')}`"
        buttons = [
            [InlineKeyboardButton("1st Shortlink", callback_data="edit_sl#1"), InlineKeyboardButton("2nd Shortlink", callback_data="edit_sl#2")],
            [InlineKeyboardButton("🗑️ Delete Shortlinks", callback_data="delete_sl")],
            [InlineKeyboardButton("<< Back", callback_data="back_to_settings")]
        ]
        await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(buttons))
        await query.answer()
    except Exception as err:
        logger.error(f"🚨 [CALLBACK ERROR in shortlink.py]: sl_menu failed", exc_info=True)
        await query.answer("⚠️ Failed to load shortlink menu.", show_alert=True)

@Client.on_callback_query(filters.regex("^edit_sl#"))
async def edit_sl(client: Client, query: CallbackQuery):
    try:
        USER_STATE[query.from_user.id] = {"chat_id": query.message.chat.id, "slot": query.data.split("#")[1]}
        await query.message.reply_text("Send shortlink URL **without** https (e.g., `tnshort.net`). Type /cancel to abort.")
        await query.answer()
    except Exception as err:
        logger.error(f"🚨 [CALLBACK ERROR in shortlink.py]: edit_sl failed", exc_info=True)
        await query.answer("⚠️ An error occurred.", show_alert=True)

@Client.on_callback_query(filters.regex("^delete_sl$"))
async def delete_sl(client: Client, query: CallbackQuery):
    try:
        await shortlink_col.update_one({"chat_id": query.message.chat.id}, {"$unset": {"site1": "", "site2": ""}})
        await query.answer("✅ Shortlinks deleted successfully!", show_alert=True)
        
        # Refresh menu view
        data = await shortlink_col.find_one({"chat_id": query.message.chat.id}) or {}
        text = f"🔗 **Shortlink Settings**\n\n• **1st Shortlink:** `{data.get('site1', 'Not Set ❌')}`\n• **2nd Shortlink:** `{data.get('site2', 'Not Set ❌')}`"
        buttons = [
            [InlineKeyboardButton("1st Shortlink", callback_data="edit_sl#1"), InlineKeyboardButton("2nd Shortlink", callback_data="edit_sl#2")],
            [InlineKeyboardButton("🗑️ Delete Shortlinks", callback_data="delete_sl")],
            [InlineKeyboardButton("<< Back", callback_data="back_to_settings")]
        ]
        await query.message.edit_reply_markup(reply_markup=InlineKeyboardMarkup(buttons))
    except Exception as err:
        logger.error(f"🚨 [CALLBACK ERROR in shortlink.py]: delete_sl failed", exc_info=True)
        await query.answer("⚠️ Failed to delete shortlinks.", show_alert=True)

@Client.on_message(filters.text & filters.private)
async def save_sl(client: Client, message: Message):
    try:
        if message.text and (message.text.startswith("/") or message.text.startswith("!")):
            return

        user_id = message.from_user.id
        if user_id not in USER_STATE:
            return
            
        state = USER_STATE.pop(message.from_user.id)
        val = message.text.strip()
        
        if val.lower() == "/cancel":
            await message.reply_text("❌ Configuration cancelled.")
            return
            
        if "http://" in val or "https://" in val:
            await message.reply_text("⚠️ Do not include `https://`. Try again.")
            USER_STATE[message.from_user.id] = state
            return
            
        await shortlink_col.update_one({"chat_id": state["chat_id"]}, {"$set": {f"site{state['slot']}": val}}, upsert=True)
        await message.reply_text("✅ Shortlink saved successfully!")
    except Exception as err:
        logger.error(f"🚨 [CRITICAL INPUT ERROR in shortlink.py]: save_sl failed", exc_info=True)
        await message.reply_text("⚠️ An internal error occurred while saving the shortlink.")
