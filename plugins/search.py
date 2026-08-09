from pyrogram import Client
from pyrogram.types import (
    InlineQueryResultCachedDocument,
    InlineQueryResultCachedVideo,
    InlineQueryResultArticle,
    InputTextMessageContent,
    InlineKeyboardMarkup,
    InlineKeyboardButton
)
import logging

from db import files_col_1

logger = logging.getLogger(__name__)


@Client.on_inline_query()
async def search_inline_files(client: Client, inline_query):
    try:
        query = inline_query.query.strip().lower()

        if not query:
            results = [
                InlineQueryResultArticle(
                    title="🔍 Search Movies & Files",
                    description="Type any movie or file name to search...",
                    input_message_content=InputTextMessageContent(
                        message_text=(
                            "👋 Send any movie name or use "
                            "inline search to find files!"
                        )
                    ),
                    reply_markup=InlineKeyboardMarkup(
                        [
                            [
                                InlineKeyboardButton(
                                    "🔍 Click Here to Search",
                                    switch_inline_query_current_chat=""
                                )
                            ]
                        ]
                    )
                )
            ]

            await inline_query.answer(
                results,
                cache_time=5,
                is_personal=True
            )

            return

        cursor = files_col_1.find(
            {
                "file_name": {
                    "$regex": query,
                    "$options": "i"
                }
            }
        ).limit(20)

        files = await cursor.to_list(
            length=20
        )

        results = []

        for file in files:
            file_id = file.get("file_id")
            file_name = file.get(
                "file_name",
                "Unknown File"
            )

            if not file_id:
                continue

            if file.get("file_type") == "video":
                results.append(
                    InlineQueryResultCachedVideo(
                        id=str(file.get("_id")),
                        video_file_id=file_id,
                        title=file_name,
                        caption=file_name
                    )
                )
            else:
                results.append(
                    InlineQueryResultCachedDocument(
                        id=str(file.get("_id")),
                        document_file_id=file_id,
                        title=file_name,
                        caption=file_name
                    )
                )

        if not results:
            results.append(
                InlineQueryResultArticle(
                    title="❌ No Results Found",
                    description="No matching files were found.",
                    input_message_content=InputTextMessageContent(
                        message_text=(
                            f"❌ No files found for: `{query}`"
                        )
                    )
                )
            )

        await inline_query.answer(
            results,
            cache_time=5,
            is_personal=True
        )

    except Exception as e:
        logger.exception(
            "Inline search error: %s",
            e
        )

        try:
            await inline_query.answer(
                [
                    InlineQueryResultArticle(
                        title="⚠️ Search Error",
                        description="An error occurred while searching.",
                        input_message_content=InputTextMessageContent(
                            message_text=(
                                "⚠️ Search failed. "
                                "Please try again later."
                            )
                        )
                    )
                ],
                cache_time=1,
                is_personal=True
            )
        except Exception:
            pass
