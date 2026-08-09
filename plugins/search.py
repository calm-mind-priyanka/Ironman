import asyncio
import logging
import re

from pyrogram import Client
from pyrogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    InlineQueryResultArticle,
    InlineQueryResultCachedDocument,
    InlineQueryResultCachedVideo,
    InputTextMessageContent,
)

from db import files_col_1, files_col_2

logger = logging.getLogger(__name__)


@Client.on_inline_query()
async def search_inline_files(client: Client, inline_query):
    try:
        query = inline_query.query.strip()

        if not query:
            results = [
                InlineQueryResultArticle(
                    title="🔍 Search Movies & Files",
                    description="Type any movie or file name to search...",
                    input_message_content=InputTextMessageContent(
                        message_text="👋 Send any movie name or use inline search to find files!"
                    ),
                    reply_markup=InlineKeyboardMarkup(
                        [[InlineKeyboardButton("🔍 Click Here to Search", switch_inline_query_current_chat="")]]
                    ),
                )
            ]
            await inline_query.answer(results, cache_time=0, is_personal=True)
            return

        safe_query = re.escape(query)
        search_filter = {"file_name": {"$regex": safe_query, "$options": "i"}}

        cursor1 = files_col_1.find(search_filter).limit(10)
        cursor2 = files_col_2.find(search_filter).limit(10)

        files1, files2 = await asyncio.gather(
            cursor1.to_list(length=10),
            cursor2.to_list(length=10),
        )

        files = []
        seen_ids = set()

        for file_data in files1 + files2:
            file_id = file_data.get("file_id")
            if not file_id or file_id in seen_ids:
                continue
            seen_ids.add(file_id)
            files.append(file_data)
            if len(files) >= 10:
                break

        results = []

        for file_data in files:
            file_id = file_data.get("file_id")
            file_name = file_data.get("file_name", "Unknown File")
            file_size = file_data.get("file_size", 0)

            size_mb = round(file_size / (1024 * 1024), 2) if file_size else 0
            caption = f"📂 **{file_name}**\n💾 **Size:** `{size_mb} MB`"

            buttons = InlineKeyboardMarkup(
                [[InlineKeyboardButton("📥 Download File", switch_inline_query_current_chat="")]]
            )

            if file_data.get("file_type") == "video":
                results.append(
                    InlineQueryResultCachedVideo(
                        title=file_name,
                        video_file_id=file_id,
                        caption=caption,
                        description=f"Size: {size_mb} MB",
                        reply_markup=buttons,
                    )
                )
            else:
                results.append(
                    InlineQueryResultCachedDocument(
                        title=file_name,
                        document_file_id=file_id,
                        caption=caption,
                        description=f"Size: {size_mb} MB",
                        reply_markup=buttons,
                    )
                )

        if not results:
            results.append(
                InlineQueryResultArticle(
                    title="❌ No Results Found",
                    description=f"No files matching '{query}' were found.",
                    input_message_content=InputTextMessageContent(
                        message_text=f"❌ Sorry, no results found for **'{query}'**."
                    ),
                )
            )

        await inline_query.answer(results, cache_time=0, is_personal=True)

    except Exception as err:
        logger.error("🚨 [INLINE SEARCH ERROR]: %s", err, exc_info=True)
        try:
            await inline_query.answer(
                [
                    InlineQueryResultArticle(
                        title="⚠️ Search Error",
                        description="An error occurred while searching.",
                        input_message_content=InputTextMessageContent(
                            message_text="⚠️ Search temporarily unavailable."
                        ),
                    )
                ],
                cache_time=0,
                is_personal=True,
            )
        except Exception:
            pass
