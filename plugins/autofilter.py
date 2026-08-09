import re
import asyncio
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from spellchecker import SpellChecker
from motor.motor_asyncio import AsyncIOMotorClient
from config import Config
from plugins.settings import get_settings

# Database Clients using your Config class
db1_client = AsyncIOMotorClient(Config.DATABASE_URI)
db1 = db1_client[Config.DATABASE_NAME]
files_col_1 = db1["files"]

db2_client = AsyncIOMotorClient(Config.DATABASE_URI_2)
db2 = db2_client[Config.DATABASE_NAME]
files_col_2 = db2["files"]

spell = SpellChecker()

# Standard lists for filters
LANGUAGES = ["hindi", "english", "tamil", "telugu", "kannada", "malayalam", "bengali", "marathi", "punjabi", "gujarati"]
QUALITIES = ["240p", "360p", "480p", "720p", "1080p", "2160p", "HDRip", "WEB-DL", "BluRay", "WEBRip", "CAM", "HDTC", "HDTS"]
SEASONS = [f"season {i}" for i in range(1, 21)]

async def search_dual_db(regex, limit):
    c1 = files_col_1.find({"file_name": {"$regex": regex}}).limit(limit)
    c2 = files_col_2.find({"file_name": {"$regex": regex}}).limit(limit)
    res1, res2 = await asyncio.gather(c1.to_list(length=limit), c2.to_list(length=limit))
    return res1 + res2

@Client.on_message(filters.text & ~filters.private & ~filters.command())
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

    text = f"📂 **Here I Found For Your Search** `{query}`\n\n"
    for i, f in enumerate(files[:limit], 1):
        fname = f.get("file_name", "File")
        fsize = round(f.get("file_size", 0) / (1024 * 1024), 2)
        text += f"{i}. `{fsize} MB` | {fname}\n\n"

    text += "⚠️ **THIS MESSAGE WILL BE AUTO DELETE AFTER 5 MINUTES TO AVOID COPYRIGHT ISSUES** 🗑️"

    buttons = [
        [
            InlineKeyboardButton("LANGUAGE", callback_data=f"lang_menu#{query}"),
            InlineKeyboardButton("QUALITY", callback_data=f"qual_menu#{query}")
        ],
        [InlineKeyboardButton("SEASON", callback_data=f"season_menu#{query}")],
        [InlineKeyboardButton("SEND ALL", callback_data=f"send_all#{query}")],
        [InlineKeyboardButton("1 / 1", callback_data="page_info"), InlineKeyboardButton("NEXT >>", callback_data=f"next_page#{query}#1")]
    ]

    await message.reply_text(text, reply_markup=InlineKeyboardMarkup(buttons))

def build_menu_buttons(items, query_text, row_size=3):
    buttons, row = [], []
    for item in items:
        row.append(InlineKeyboardButton(str(item).capitalize(), callback_data=f"apply_filter#{query_text}#{item}"))
        if len(row) == row_size:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    buttons.append([InlineKeyboardButton("<< Back", callback_data=f"back_main#{query_text}")])
    return buttons

@Client.on_callback_query(filters.regex("^lang_menu#"))
async def lang_menu(client, query):
    qt = query.data.split("#")[1]
    await query.message.edit_text(f"🌍 **Select Language for:** `{qt}`", reply_markup=InlineKeyboardMarkup(build_menu_buttons(LANGUAGES, qt, 3)))
    await query.answer()

@Client.on_callback_query(filters.regex("^qual_menu#"))
async def qual_menu(client, query):
    qt = query.data.split("#")[1]
    await query.message.edit_text(f"🎬 **Select Quality for:** `{qt}`", reply_markup=InlineKeyboardMarkup(build_menu_buttons(QUALITIES, qt, 3)))
    await query.answer()

@Client.on_callback_query(filters.regex("^season_menu#"))
async def season_menu(client, query):
    qt = query.data.split("#")[1]
    await query.message.edit_text(f"📺 **Select Season for:** `{qt}`", reply_markup=InlineKeyboardMarkup(build_menu_buttons(SEASONS, qt, 4)))
    await query.answer()

@Client.on_callback_query(filters.regex("^apply_filter#"))
async def apply_filter(client, query):
    _, base_q, tag = query.data.split("#")
    files = await search_dual_db(re.compile(re.escape(f"{base_q} {tag}"), re.IGNORECASE), 15)
    
    if not files:
        await query.answer(f"❌ No files found for '{tag}'!", show_alert=True)
        return

    text = f"📂 **Results for:** `{base_q}` | **Filter:** `{tag}`\n\n"
    for i, f in enumerate(files, 1):
        fsize = round(f.get("file_size", 0) / (1024 * 1024), 2)
        text += f"{i}. `{fsize} MB` | {f.get('file_name', 'File')}\n\n"
    text += "⚠️ **THIS MESSAGE WILL BE AUTO DELETE AFTER 5 MINUTES** 🗑️"

    buttons = [
        [InlineKeyboardButton("LANGUAGE", callback_data=f"lang_menu#{base_q}"), InlineKeyboardButton("QUALITY", callback_data=f"qual_menu#{base_q}")],
        [InlineKeyboardButton("SEASON", callback_data=f"season_menu#{base_q}")],
        [InlineKeyboardButton("SEND ALL", callback_data=f"send_all#{base_q}")],
        [InlineKeyboardButton("<< Back to All Results", callback_data=f"back_main#{base_q}")]
    ]
    await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(buttons))
    await query.answer(f"Filtered by {tag}!")

@Client.on_callback_query(filters.regex("^send_all#"))
async def send_all(client, query):
    qt = query.data.split("#")[1]
    files = await search_dual_db(re.compile(re.escape(qt), re.IGNORECASE), 15)
    if not files:
        await query.answer("❌ No files found!", show_alert=True)
        return
    await query.answer(f"📤 Sending {len(files)} files...", show_alert=False)
    for f in files:
        try:
            await client.send_cached_media(chat_id=query.message.chat.id, file_id=f.get("file_id"))
            await asyncio.sleep(0.5)
        except Exception:
            pass

@Client.on_callback_query(filters.regex("^back_main#"))
async def back_main(client, query):
    qt = query.data.split("#")[1]
    files = await search_dual_db(re.compile(re.escape(qt), re.IGNORECASE), 10)
    if not files:
        await query.answer("❌ No results found!", show_alert=True)
        return
    text = f"📂 **Here I Found For Your Search** `{qt}`\n\n"
    for i, f in enumerate(files, 1):
        fsize = round(f.get("file_size", 0) / (1024 * 1024), 2)
        text += f"{i}. `{fsize} MB` | {f.get('file_name', 'File')}\n\n"
    text += "⚠️ **THIS MESSAGE WILL BE AUTO DELETE AFTER 5 MINUTES TO AVOID COPYRIGHT ISSUES** 🗑️"
    
    buttons = [
        [InlineKeyboardButton("LANGUAGE", callback_data=f"lang_menu#{qt}"), InlineKeyboardButton("QUALITY", callback_data=f"qual_menu#{qt}")],
        [InlineKeyboardButton("SEASON", callback_data=f"season_menu#{qt}")],
        [InlineKeyboardButton("SEND ALL", callback_data=f"send_all#{qt}")],
        [InlineKeyboardButton("1 / 1", callback_data="page_info"), InlineKeyboardButton("NEXT >>", callback_data=f"next_page#{qt}#1")]
    ]
    await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(buttons))
    await query.answer("Refreshed!")
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
        # --- BUTTON MODE WITH WARNING & NUMBERED LAYOUT ---
        text = f"📂 **Here are your results for:** `{query}`\n\n"
        text += "⚠️ **Warning:** Files may be deleted automatically or protected. Please use them quickly!\n\n"
        text += "✨ Quality & Season matched successfully (Dual DB Active ⚡)"

        buttons = []
        for index, f in enumerate(files[:limit], 1):
            fname = f.get("file_name", "File")
            buttons.append([InlineKeyboardButton(f"{index}. {fname[:45]}", callback_data=f"get_file#{f.get('_id')}M")])

        buttons.append([
            InlineKeyboardButton("📥 Send All", callback_data=f"send_all#{query}"),
            InlineKeyboardButton("1/2 📄", callback_data="page_info"),
            InlineKeyboardButton("Next >>", callback_data="next_page#1")
        ])
        await message.reply_text(text, reply_markup=InlineKeyboardMarkup(buttons))
    else:
        # --- TEXT MODE ---
        text = f"🎯 **Results for:** `{query}` (Dual DB Active)\n\n"
        for i, f in enumerate(files[:limit], 1):
            text += f"{i}. {f.get('file_name', 'File')}\n"
        
        text += "\n⚠️ **Warning:** Files may be protected or auto-deleted."
        
        buttons = [
            [InlineKeyboardButton("📥 Send All", callback_data=f"send_all#{query}")],
            [InlineKeyboardButton("<<", callback_data="prev#0"), InlineKeyboardButton("1/2", callback_data="page_info"), InlineKeyboardButton("Next >>", callback_data="next#1")]
        ]
        await message.reply_text(text, reply_markup=InlineKeyboardMarkup(buttons))
