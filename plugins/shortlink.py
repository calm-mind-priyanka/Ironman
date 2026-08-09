import logging
from pyrogram import Client, filters
from pyrogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from db import shortlink_col

logger = logging.getLogger(__name__)

USER_STATE = {}


@Client.on_callback_query(filters.regex("^set_shortlink_menu$"))
async def sl_menu(client: Client, query: CallbackQuery):
    try:
        chat_id = query.message.chat.id
        data = await shortlink_col.find_one({"chat_id": chat_id}) or {}

        text = (
            "🔗 **Shortlink Settings**\n\n"
            f"• **1st Shortlink:** `{data.get('site1', 'Not Set ❌')}`\n"
            f"• **2nd Shortlink:** `{data.get('site2', 'Not Set ❌')}`"
        )

        buttons = [
            [
                InlineKeyboardButton("1st Shortlink", callback_data="edit_sl#1"),
                InlineKeyboardButton("2nd Shortlink", callback_data="edit_sl#2"),
            ],
            [InlineKeyboardButton("🗑️ Delete Shortlinks", callback_data="delete_sl")],
            [InlineKeyboardButton("<< Back", callback_data="back_to_settings")],
        ]

        await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(buttons))
        await query.answer()

    except Exception:
        logger.error("🚨 [CALLBACK ERROR in shortlink.py]: sl_menu failed", exc_info=True)
        await query.answer("⚠️ Failed to load shortlink menu.", show_alert=True)


@Client.on_callback_query(filters.regex("^edit_sl#"))
async def edit_sl(client: Client, query: CallbackQuery):
    try:
        slot = query.data.split("#", 1)[1]
        USER_STATE[query.from_user.id] = {
            "chat_id": query.message.chat.id,
            "slot": slot,
        }

        await query.message.reply_text(
            "Send shortlink URL **without** `https://`\n\n"
            "Example:\n`tnshort.net`\n\n"
            "Type `/cancel` to abort."
        )
        await query.answer()

    except Exception:
        logger.error("🚨 [CALLBACK ERROR in shortlink.py]: edit_sl failed", exc_info=True)
        await query.answer("⚠️ An error occurred.", show_alert=True)


@Client.on_callback_query(filters.regex("^delete_sl$"))
async def delete_sl(client: Client, query: CallbackQuery):
    try:
        chat_id = query.message.chat.id

        await shortlink_col.update_one(
            {"chat_id": chat_id},
            {"$unset": {"site1": "", "site2": ""}},
        )

        await query.answer("✅ Shortlinks deleted successfully!", show_alert=True)

        data = await shortlink_col.find_one({"chat_id": chat_id}) or {}

        text = (
            "🔗 **Shortlink Settings**\n\n"
            f"• **1st Shortlink:** `{data.get('site1', 'Not Set ❌')}`\n"
            f"• **2nd Shortlink:** `{data.get('site2', 'Not Set ❌')}`"
        )

        buttons = [
            [
                InlineKeyboardButton("1st Shortlink", callback_data="edit_sl#1"),
                InlineKeyboardButton("2nd Shortlink", callback_data="edit_sl#2"),
            ],
            [InlineKeyboardButton("🗑️ Delete Shortlinks", callback_data="delete_sl")],
            [InlineKeyboardButton("<< Back", callback_data="back_to_settings")],
        ]

        await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(buttons))

    except Exception:
        logger.error("🚨 [CALLBACK ERROR in shortlink.py]: delete_sl failed", exc_info=True)
        await query.answer("⚠️ Failed to delete shortlinks.", show_alert=True)


@Client.on_message(filters.text & filters.private)
async def save_sl(client: Client, message: Message):
    try:
        if message.text and (message.text.startswith("/") or message.text.startswith("!")):
            return

        user_id = message.from_user.id
        if user_id not in USER_STATE:
            return

        state = USER_STATE.pop(user_id)
        val = message.text.strip()

        if val.lower() == "/cancel":
            await message.reply_text("❌ Configuration cancelled.")
            return

        if "http://" in val or "https://" in val:
            await message.reply_text("⚠️ Do not include `https://`.\n\nTry again.")
            USER_STATE[user_id] = state
            return

        slot = state["slot"]
        if slot not in ("1", "2"):
            await message.reply_text("⚠️ Invalid shortlink slot.")
            return

        await shortlink_col.update_one(
            {"chat_id": state["chat_id"]},
            {"$set": {f"site{slot}": val}},
            upsert=True,
        )

        await message.reply_text("✅ Shortlink saved successfully!")

    except Exception:
        logger.error("🚨 [CRITICAL INPUT ERROR in shortlink.py]: save_sl failed", exc_info=True)
        await message.reply_text("⚠️ An internal error occurred while saving the shortlink.")
