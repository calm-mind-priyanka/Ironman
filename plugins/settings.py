from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from motor.motor_asyncio import AsyncIOMotorClient
from config import Config
import logging

logger = logging.getLogger(__name__)

try:
    db_client = AsyncIOMotorClient(Config.DATABASE_URI)
    db = db_client[getattr(Config, "DATABASE_NAME", "AutoFilterBot")]
    settings_col = db["settings"]
except Exception as e:
    logger.error(f"Failed to initialize settings collection in settings.py: {e}")

GROUP_INPUT_STATE = {}

DEFAULT_SETTINGS = {
    "auto_filter": True,
    "file_secure": True,
    "imdb": True,
    "spell_check": True,
    "auto_delete": False,
    "result_mode": True,
    "files_mode": True,
    "files_caption": "📂 **{file_name}**\n💾 Size: {file_size}",
    "tutorial_link": "https://t.me/your_tutorial_channel",
    "movie_req_chat": "Not Set ❌",
    "max_results": 10
}

async def get_settings(chat_id: int):
    try:
        current = await settings_col.find_one({"chat_id": chat_id})
        if not current:
            await settings_col.insert_one({"chat_id": chat_id, **DEFAULT_SETTINGS})
            return {"chat_id": chat_id, **DEFAULT_SETTINGS}
        return current
    except Exception as e:
        logger.error(f"Error fetching settings for chat {chat_id}: {e}")
        return {"chat_id": chat_id, **DEFAULT_SETTINGS}

async def build_settings_keyboard(chat_id: int):
    s = await get_settings(chat_id)
    
    af = "ON ✅" if s.get("auto_filter", True) else "OFF ❌"
    fs = "ON ✅" if s.get("file_secure", True) else "OFF ❌"
    im = "ON ✅" if s.get("imdb", True) else "OFF ❌"
    sc = "ON ✅" if s.get("spell_check", True) else "OFF ❌"
    ad = "ON ✅" if s.get("auto_delete", False) else "OFF ❌"
    rm = "BUTTON 📚" if s.get("result_mode", True) else "TEXT 📋"
    fm = "SHORTLINK 🔗" if s.get("files_mode", True) else "DIRECT 📁"

    buttons = [
        [InlineKeyboardButton(f"📝 AUTO FILTER: {af}", callback_data="set#auto_filter"),
         InlineKeyboardButton(f"🔒 FILE SECURE: {fs}", callback_data="set#file_secure")],
        [InlineKeyboardButton(f"🈴 IMDB: {im}", callback_data="set#imdb"),
         InlineKeyboardButton(f"🔍 SPELL CHECK: {sc}", callback_data="set#spell_check")],
        [InlineKeyboardButton(f"🗑️ AUTO DELETE: {ad}", callback_data="set#auto_delete"),
         InlineKeyboardButton(f"📚 RESULT MODE: {rm}", callback_data="set#result_mode")],
        [InlineKeyboardButton(f"📁 FILES MODE: {fm}", callback_data="set#files_mode"),
         InlineKeyboardButton("📋 FILES CAPTION", callback_data="set_caption_menu")],
        [InlineKeyboardButton("🥁 TUTORIAL LINK", callback_data="set_tutorial_menu"),
         InlineKeyboardButton("🔗 SET SHORTLINK", callback_data="set_shortlink_menu")],
        [InlineKeyboardButton("📢 SET MOVIE REQ", callback_data="set_movie_req"),
         InlineKeyboardButton("💡 DETAILS", callback_data="settings_details")],
        [InlineKeyboardButton("👥 FORCE CHANNEL", callback_data="set_force_channel"),
         InlineKeyboardButton(f"ℹ️ MAX RES: {s.get('max_results', 10)}", callback_data="set_max_results")],
        [InlineKeyboardButton("‼️ CLOSE SETTINGS MENU ‼️", callback_data="close_settings")]
    ]
    return InlineKeyboardMarkup(buttons)

@Client.on_message(filters.command("settings"))
async def open_settings(client: Client, message: Message):
    try:
        chat_id = message.chat.id
        keyboard = await build_settings_keyboard(chat_id)
        title = message.chat.title if message.chat.title else "Personal PM"
        await message.reply_text(f"⚙️ **Settings for {title}:**", reply_markup=keyboard)
    except Exception as err:
        logger.error(f"🚨 [CRITICAL COMMAND ERROR in settings.py]: /settings failed", exc_info=True)
        await message.reply_text("⚠️ An error occurred while opening settings.")

@Client.on_callback_query(filters.regex("^set#"))
async def toggle_setting_callback(client: Client, query: CallbackQuery):
    try:
        chat_id = query.message.chat.id
        key = query.data.split("#")[1]
        s = await get_settings(chat_id)
        new_val = not s.get(key, True)
        
        await settings_col.update_one({"chat_id": chat_id}, {"$set": {key: new_val}})
        new_keyboard = await build_settings_keyboard(chat_id)
        await query.message.edit_reply_markup(reply_markup=new_keyboard)
        await query.answer(f"Updated {key} successfully!")
    except Exception as err:
        logger.error(f"🚨 [CALLBACK ERROR in settings.py]: toggle {query.data} failed", exc_info=True)
        await query.answer("⚠️ Failed to update setting.", show_alert=True)

@Client.on_callback_query(filters.regex("^set_caption_menu$"))
async def caption_menu(client: Client, query: CallbackQuery):
    try:
        s = await get_settings(query.message.chat.id)
        text = f"📋 **Current Files Caption:**\n\n`{s.get('files_caption', '')}`\n\nSend new caption text or variables like `{{file_name}}`, `{{file_size}}`."
        buttons = [[InlineKeyboardButton("<< Back", callback_data="back_to_settings")]]
        await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(buttons))
        GROUP_INPUT_STATE[query.from_user.id] = {"chat_id": query.message.chat.id, "type": "caption"}
        await query.answer()
    except Exception as err:
        logger.error(f"🚨 [CALLBACK ERROR]: caption_menu failed", exc_info=True)

@Client.on_callback_query(filters.regex("^set_tutorial_menu$"))
async def tutorial_menu(client: Client, query: CallbackQuery):
    try:
        s = await get_settings(query.message.chat.id)
        text = f"🥁 **Current Tutorial Link:**\n\n`{s.get('tutorial_link', '')}`\n\nSend the new tutorial video/guide link."
        buttons = [[InlineKeyboardButton("<< Back", callback_data="back_to_settings")]]
        await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(buttons))
        GROUP_INPUT_STATE[query.from_user.id] = {"chat_id": query.message.chat.id, "type": "tutorial"}
        await query.answer()
    except Exception as err:
        logger.error(f"🚨 [CALLBACK ERROR]: tutorial_menu failed", exc_info=True)

@Client.on_callback_query(filters.regex("^set_movie_req$"))
async def movie_req_menu(client: Client, query: CallbackQuery):
    try:
        s = await get_settings(query.message.chat.id)
        text = f"📢 **Movie Request Channel/Chat:**\n\n`{s.get('movie_req_chat', '')}`\n\nSend the channel username or ID."
        buttons = [[InlineKeyboardButton("<< Back", callback_data="back_to_settings")]]
        await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(buttons))
        GROUP_INPUT_STATE[query.from_user.id] = {"chat_id": query.message.chat.id, "type": "movie_req"}
        await query.answer()
    except Exception as err:
        logger.error(f"🚨 [CALLBACK ERROR]: movie_req_menu failed", exc_info=True)

@Client.on_callback_query(filters.regex("^settings_details$"))
async def settings_details_callback(client: Client, query: CallbackQuery):
    try:
        s = await get_settings(query.message.chat.id)
        text = (
            f"💡 **Current Settings Details:**\n\n"
            f"• Chat ID: `{s.get('chat_id')}`\n"
            f"• Auto Filter: {s.get('auto_filter')}\n"
            f"• File Secure: {s.get('file_secure')}\n"
            f"• IMDb Info: {s.get('imdb')}\n"
            f"• Spell Check: {s.get('spell_check')}\n"
            f"• Auto Delete: {s.get('auto_delete')}\n"
            f"• Max Results: {s.get('max_results')}"
        )
        await query.answer(text, show_alert=True)
    except Exception as err:
        logger.error(f"🚨 [CALLBACK ERROR]: settings_details failed", exc_info=True)

@Client.on_callback_query(filters.regex("^set_max_results$"))
async def max_results_menu(client: Client, query: CallbackQuery):
    try:
        s = await get_settings(query.message.chat.id)
        text = f"ℹ️ **Max Results Per Page:**\n\nCurrent limit: `{s.get('max_results', 10)}`\n\nSend a number between 1 and 20."
        buttons = [[InlineKeyboardButton("<< Back", callback_data="back_to_settings")]]
        await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(buttons))
        GROUP_INPUT_STATE[query.from_user.id] = {"chat_id": query.message.chat.id, "type": "max_results"}
        await query.answer()
    except Exception as err:
        logger.error(f"🚨 [CALLBACK ERROR]: max_results_menu failed", exc_info=True)

@Client.on_callback_query(filters.regex("^back_to_settings$"))
async def back_to_main_settings(client: Client, query: CallbackQuery):
    try:
        chat_id = query.message.chat.id
        keyboard = await build_settings_keyboard(chat_id)
        await query.message.edit_text("⚙️ **Settings Menu:**", reply_markup=keyboard)
    except Exception as err:
        logger.error(f"🚨 [CALLBACK ERROR]: back_to_settings failed", exc_info=True)

@Client.on_callback_query(filters.regex("^close_settings$"))
async def close_settings_callback(client: Client, query: CallbackQuery):
    try:
        await query.message.delete()
    except Exception as err:
        logger.error(f"🚨 [CALLBACK ERROR]: close_settings failed", exc_info=True)

@Client.on_message(filters.text & filters.private)
async def capture_group_settings_inputs(client: Client, message: Message):
    try:
        if message.text and (message.text.startswith("/") or message.text.startswith("!")):
            return

        user_id = message.from_user.id
        if user_id not in GROUP_INPUT_STATE:
            return

        state = GROUP_INPUT_STATE.pop(user_id)
        chat_id = state["chat_id"]
        input_type = state["type"]
        val = message.text.strip()

        if val.lower() == "/cancel":
            await message.reply_text("❌ Configuration cancelled.")
            return

        update_field = None
        if input_type == "caption":
            update_field = "files_caption"
        elif input_type == "tutorial":
            update_field = "tutorial_link"
        elif input_type == "movie_req":
            update_field = "movie_req_chat"
        elif input_type == "max_results":
            try:
                val = int(val)
                if not (1 <= val <= 20):
                    raise ValueError()
                update_field = "max_results"
            except ValueError:
                await message.reply_text("⚠️ Please send a valid number between 1 and 20.")
                GROUP_INPUT_STATE[user_id] = state
                return

        if update_field:
            await settings_col.update_one({"chat_id": chat_id}, {"$set": {update_field: val}})
            await message.reply_text(f"✅ Successfully updated **{update_field}**!")
    except Exception as err:
        logger.error(f"🚨 [CRITICAL INPUT ERROR in settings.py]: capture_group_settings_inputs failed", exc_info=True)
        await message.reply_text("⚠️ An error occurred while updating the setting.")
