from pyrogram import Client, filters
from pyrogram.types import InlineQueryResultCachedDocument, InlineQueryResultCachedVideo, InlineQueryResultArticle, InputTextMessageContent, InlineKeyboardMarkup, InlineKeyboardButton
from motor.motor_asyncio import AsyncIOMotorClient
from config import Config
import logging

logger = logging.getLogger(__name__)

try:
    db1_client = AsyncIOMotorClient(Config.DATABASE_URI)
    db1 = db1_client[getattr(Config, "DATABASE_NAME", "AutoFilterBot")]
    files_col_1 = db1["files"]
except Exception as e:
    logger.error(f"Failed to initialize database 1 in search.py: {e}")

@Client.on_inline_query()
async def search_inline_files(client: Client, inline_query):
    try:
        query = inline_query.query.strip().lower()
        
        # If the user hasn't typed anything yet, show a welcome tip
        if not query:
            results = [
                InlineQueryResultArticle(
                    title="🔍 Search Movies & Files",
                    description="Type any movie or file name to search...",
                    input_message_content=InputTextMessageContent(
                        message_text="👋 Send any movie name or use inline search to find files!"
                    ),
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("🔍 Click Here to Search", switch_inline_query_current_chat="")]
                    ])
                )
            ]
            await inline_query.answer(results, cache_time=0)
            return

        # Build search filter (supports partial matching)
        search_filter = {"file_name": {"$regex": query, "$options": "i"}}
        
        # Fetch matching files from database 1 (limit to 10 results for speed)
        cursor = files_col_1.find(search_filter).limit(10)
        files = await cursor.to_list(length=10)

        results = []
        if files:
            for file in files:
                file_id = file.get("file_id")
                file_name = file.get("file_name", "Unknown File")
                file_size = file.get("file_size", 0)
                
                # Format file size into MB/GB nicely
                size_mb = round(file_size / (1024 * 1024), 2) if file_size else 0
                caption = f"📂 **{file_name}**\n💾 **Size:** `{size_mb} MB`"
                
                # Add file as cached document result
                results.append(
                    InlineQueryResultCachedDocument(
                        title=file_name,
                        file_id=file_id,
                        caption=caption,
                        description=f"Size: {size_mb} MB | Click to get file",
                        reply_markup=InlineKeyboardMarkup([
                            [InlineKeyboardButton("📥 Download File", url=f"https://t.me/{client.me.username}")]
                        ])
                    )
                )
        else:
            # If no files found, show a clean "Not Found" card
            results.append(
                InlineQueryResultArticle(
                    title="❌ No Results Found",
                    description=f"No files matching '{query}' were found in the database.",
                    input_message_content=InputTextMessageContent(
                        message_text=f"❌ Sorry, no results found for **'{query}'**."
                    )
                )
            )

        await inline_query.answer(results, cache_time=0)

    except Exception as err:
        logger.error(f"🚨 [INLINE SEARCH ERROR]: {err}", exc_info=True)
