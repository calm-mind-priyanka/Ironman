import asyncio
import logging
import re

from pyrogram import Client, filters
from pyrogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)
from spellchecker import SpellChecker

from db import files_col_1, files_col_2
from plugins.settings import get_settings

logger = logging.getLogger(__name__)

spell = SpellChecker()

LANGUAGES = [
    "hindi",
    "english",
    "tamil",
    "telugu",
    "kannada",
    "malayalam",
    "bengali",
    "marathi",
    "punjabi",
    "gujarati",
]

QUALITIES = [
    "240p",
    "360p",
    "480p",
    "720p",
    "1080p",
    "2160p",
    "HDRip",
    "WEB-DL",
    "BluRay",
    "WEBRip",
    "CAM",
    "HDTC",
    "HDTS",
]

SEASONS = [f"season {i}" for i in range(1, 21)]


async def search_dual_db(regex, limit):
    try:
        cursor1 = files_col_1.find({"file_name": {"$regex": regex}}).limit(limit)
        cursor2 = files_col_2.find({"file_name": {"$regex": regex}}).limit(limit)

        results1, results2 = await asyncio.gather(
            cursor1.to_list(length=limit),
            cursor2.to_list(length=limit),
        )
        return results1 + results2
    except Exception as e:
        logger.exception("Dual database search failed: %s", e)
        return []


@Client.on_message(filters.text & ~filters.private)
async def group_autofilter_engine(client: Client, message: Message):
    try:
        if not message.text or message.text.startswith("/") or message.text.startswith("!"):
            return

        chat_id = message.chat.id
        settings = await get_settings(chat_id)

        if not settings.get("auto_filter", True):
            return

        raw_query = message.text.strip()
        if len(raw_query) < 2:
            return

        query = raw_query

        if settings.get("spell_check", True):
            words = raw_query.split()
            corrected = [spell.correction(word) or word for word in words]
            query = " ".join(corrected)

        regex = re.compile(re.escape(query), re.IGNORECASE)
        limit = int(settings.get("max_results", 10))
        files = await search_dual_db(regex, limit)

        if not files and query != raw_query:
            query = raw_query
            regex = re.compile(re.escape(query), re.IGNORECASE)
            files = await search_dual_db(regex, limit)

        if not files:
            return

        text = f"📂 **Here I Found For Your Search** `{query}`\n\n"

        for i, file_data in enumerate(files[:limit], 1):
            file_name = file_data.get("file_name", "File")
            file_size = round(file_data.get("file_size", 0) / (1024 * 1024), 2)
            text += f"{i}. `{file_size} MB` | {file_name}\n\n"

        text += "⚠️ **THIS MESSAGE WILL BE AUTO DELETE AFTER 5 MINUTES TO AVOID COPYRIGHT ISSUES** 🗑️"

        buttons = [
            [
                InlineKeyboardButton("LANGUAGE", callback_data=f"lang_menu#{query}"),
                InlineKeyboardButton("QUALITY", callback_data=f"qual_menu#{query}"),
            ],
            [InlineKeyboardButton("SEASON", callback_data=f"season_menu#{query}")],
            [InlineKeyboardButton("SEND ALL", callback_data=f"send_all#{query}")],
            [
                InlineKeyboardButton("1 / 1", callback_data="page_info"),
                InlineKeyboardButton("NEXT >>", callback_data=f"next_page#{query}#1"),
            ],
        ]

        await message.reply_text(text, reply_markup=InlineKeyboardMarkup(buttons))

    except Exception as e:
        logger.exception("Autofilter engine error: %s", e)


def build_menu_buttons(items, query_text, row_size=3):
    buttons = []
    row = []

    for item in items:
        row.append(
            InlineKeyboardButton(
                str(item).capitalize(),
                callback_data=f"apply_filter#{query_text}#{item}",
            )
        )
        if len(row) == row_size:
            buttons.append(row)
            row = []

    if row:
        buttons.append(row)

    buttons.append([InlineKeyboardButton("<< Back", callback_data=f"back_main#{query_text}")])
    return buttons


@Client.on_callback_query(filters.regex(r"^lang_menu#"))
async def lang_menu(client: Client, query: CallbackQuery):
    try:
        qt = query.data.split("#", 1)[1]
        await query.message.edit_text(
            f"🌍 **Select Language for:** `{qt}`",
            reply_markup=InlineKeyboardMarkup(build_menu_buttons(LANGUAGES, qt, 3)),
        )
        await query.answer()
    except Exception as e:
        logger.exception("Language menu error: %s", e)
        await query.answer("⚠️ Failed to open language menu.", show_alert=True)


@Client.on_callback_query(filters.regex(r"^qual_menu#"))
async def qual_menu(client: Client, query: CallbackQuery):
    try:
        qt = query.data.split("#", 1)[1]
        await query.message.edit_text(
            f"🎬 **Select Quality for:** `{qt}`",
            reply_markup=InlineKeyboardMarkup(build_menu_buttons(QUALITIES, qt, 3)),
        )
        await query.answer()
    except Exception as e:
        logger.exception("Quality menu error: %s", e)
        await query.answer("⚠️ Failed to open quality menu.", show_alert=True)


@Client.on_callback_query(filters.regex(r"^season_menu#"))
async def season_menu(client: Client, query: CallbackQuery):
    try:
        qt = query.data.split("#", 1)[1]
        await query.message.edit_text(
            f"📺 **Select Season for:** `{qt}`",
            reply_markup=InlineKeyboardMarkup(build_menu_buttons(SEASONS, qt, 4)),
        )
        await query.answer()
    except Exception as e:
        logger.exception("Season menu error: %s", e)
        await query.answer("⚠️ Failed to open season menu.", show_alert=True)


@Client.on_callback_query(filters.regex(r"^apply_filter#"))
async def apply_filter(client: Client, query: CallbackQuery):
    try:
        parts = query.data.split("#", 2)
        if len(parts) != 3:
            await query.answer("⚠️ Invalid filter.", show_alert=True)
            return

        _, base_q, tag = parts
        search_text = f"{base_q} {tag}"
        files = await search_dual_db(re.compile(re.escape(search_text), re.IGNORECASE), 15)

        if not files:
            await query.answer(f"❌ No files found for '{tag}'!", show_alert=True)
            return

        text = f"📂 **Results for:** `{base_q}`\n**Filter:** `{tag}`\n\n"

        for i, file_data in enumerate(files, 1):
            file_size = round(file_data.get("file_size", 0) / (1024 * 1024), 2)
            text += f"{i}. `{file_size} MB` | {file_data.get('file_name', 'File')}\n\n"

        text += "⚠️ **THIS MESSAGE WILL BE AUTO DELETE AFTER 5 MINUTES** 🗑️"

        buttons = [
            [
                InlineKeyboardButton("LANGUAGE", callback_data=f"lang_menu#{base_q}"),
                InlineKeyboardButton("QUALITY", callback_data=f"qual_menu#{base_q}"),
            ],
            [InlineKeyboardButton("SEASON", callback_data=f"season_menu#{base_q}")],
            [InlineKeyboardButton("SEND ALL", callback_data=f"send_all#{base_q}")],
            [InlineKeyboardButton("<< Back to All Results", callback_data=f"back_main#{base_q}")],
        ]

        await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(buttons))
        await query.answer(f"Filtered by {tag}!")

    except Exception as e:
        logger.exception("Apply filter error: %s", e)
        await query.answer("⚠️ Failed to apply filter.", show_alert=True)


@Client.on_callback_query(filters.regex(r"^send_all#"))
async def send_all(client: Client, query: CallbackQuery):
    try:
        qt = query.data.split("#", 1)[1]
        files = await search_dual_db(re.compile(re.escape(qt), re.IGNORECASE), 15)

        if not files:
            await query.answer("❌ No files found!", show_alert=True)
            return

        await query.answer(f"📤 Sending {len(files)} files...")

        for file_data in files:
            try:
                file_id = file_data.get("file_id")
                if not file_id:
                    continue
                await client.send_cached_media(chat_id=query.message.chat.id, file_id=file_id)
                await asyncio.sleep(0.5)
            except Exception as e:
                logger.warning("Failed to send file: %s", e)

    except Exception as e:
        logger.exception("Send all error: %s", e)
        await query.answer("⚠️ Failed to send files.", show_alert=True)


@Client.on_callback_query(filters.regex(r"^back_main#"))
async def back_main(client: Client, query: CallbackQuery):
    try:
        qt = query.data.split("#", 1)[1]
        files = await search_dual_db(re.compile(re.escape(qt), re.IGNORECASE), 10)

        if not files:
            await query.answer("❌ No results found!", show_alert=True)
            return

        text = f"📂 **Here I Found For Your Search** `{qt}`\n\n"

        for i, file_data in enumerate(files, 1):
            file_size = round(file_data.get("file_size", 0) / (1024 * 1024), 2)
            text += f"{i}. `{file_size} MB` | {file_data.get('file_name', 'File')}\n\n"

        text += "⚠️ **THIS MESSAGE WILL BE AUTO DELETE AFTER 5 MINUTES TO AVOID COPYRIGHT ISSUES** 🗑️"

        buttons = [
            [
                InlineKeyboardButton("LANGUAGE", callback_data=f"lang_menu#{qt}"),
                InlineKeyboardButton("QUALITY", callback_data=f"qual_menu#{qt}"),
            ],
            [InlineKeyboardButton("SEASON", callback_data=f"season_menu#{qt}")],
            [InlineKeyboardButton("SEND ALL", callback_data=f"send_all#{qt}")],
            [
                InlineKeyboardButton("1 / 1", callback_data="page_info"),
                InlineKeyboardButton("NEXT >>", callback_data=f"next_page#{qt}#1"),
            ],
        ]

        await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(buttons))
        await query.answer("Refreshed!")

    except Exception as e:
        logger.exception("Back main error: %s", e)
        await query.answer("⚠️ Failed to refresh results.", show_alert=True)
