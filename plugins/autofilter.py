import re
import asyncio
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from spellchecker import SpellChecker
from motor.motor_asyncio import AsyncIOMotorClient
from config import Config
from plugins.settings import get_settings

db1_client = AsyncIOMotorClient(Config.DATABASE_URI)
db1 = db1_client[Config.DATABASE_NAME]
files_col_1 = db1["files"]

db2_client = AsyncIOMotorClient(Config.DATABASE_URI_2)
db2 = db2_client[Config.DATABASE_NAME]
files_col_2 = db2["files"]

spell = SpellChecker()

async def search_dual_db(regex, limit):
    c1 = files_col_1.find({"file_name": {"$regex": regex}}).limit(limit)
    c2 = files_col_2.find({"file_name": {"$regex": regex}}).limit(limit)
    res1, res2 = await asyncio.gather(c1.to_list(length=limit), c2.to_list(length=limit))
    return res1 + res2

@Client.on_message(filters.text & ~filters.private & ~filters.command)
async def group_autofilter_engine(client: Client, message: Message):
    chat_id = message.chat.id
    settings = await get_settings(chat_id)
    if not settings["auto_filter"]:
        return

    raw_query = message.text.strip()
    if len(raw_query) < 2:
        return

    query = raw_query
    if settings.get("spell_check", True):
        words = raw_query.split()
        corrected = [spell.correction(w) or w for w in words]
        query = " ".join(corrected)

    regex = re.compile(re.escape(query), re.IGNORECASE)
    limit = settings["max_results"]
    files = await search_dual_db(regex, limit)

    if not files and query != raw_query:
        query = raw_query
        regex = re.compile(re.escape(query), re.IGNORECASE)
        files = await search_dual_db(regex, limit)

    if not files:
        return

    if settings["result_mode"]:
        text = f"🎯 **Results for:** `{query}`\n\n(Dual DB Active ⚡)"
        buttons = [[InlineKeyboardButton(f.get("file_name", "File"), callback_data=f"get_file#{f.get('_id')}")] for f in files[:limit]]
        buttons.append([
            InlineKeyboardButton("📥 Send All", callback_data=f"send_all#{query}"),
            InlineKeyboardButton("1/1 📄", callback_data="page_info"),
            InlineKeyboardButton("Next >>", callback_data="next_page#1")
        ])
        await message.reply_text(text, reply_markup=InlineKeyboardMarkup(buttons))
    else:
        text = f"🎯 **Results for:** `{query}` (Dual DB Active)\n\n"
        for i, f in enumerate(files[:limit], 1):
            text += f"{i}. {f.get('file_name', 'File')}\n"
        buttons = [
            [InlineKeyboardButton("📥 Send All", callback_data=f"send_all#{query}")],
            [InlineKeyboardButton("<<", callback_data="prev#0"), InlineKeyboardButton("1/1", callback_data="page_info"), InlineKeyboardButton("Next >>", callback_data="next#1")]
        ]
        await message.reply_text(text, reply_markup=InlineKeyboardMarkup(buttons))
