import asyncio
import logging
from pyrogram import Client, filters
from pyrogram.types import Message

from config import Config
from db import files_col_1, files_col_2

logger = logging.getLogger(__name__)

INDEX_STATE = {}


@Client.on_message(filters.document | filters.video)
async def auto_index_uploaded_files(client: Client, message: Message):
    try:
        auto_index_channel = getattr(Config, "AUTO_INDEX_CHANNEL", None)
        if not auto_index_channel or message.chat.id != auto_index_channel:
            return

        media = message.document or message.video
        if not media or not media.file_name:
            return

        file_id = media.file_id
        file_name = media.file_name
        clean_name = file_name.replace("_", " ").replace(".", " ")

        file_data = {
            "file_name": clean_name,
            "raw_name": file_name,
            "file_id": file_id,
            "file_size": media.file_size,
            "message_id": message.id,
            "chat_id": message.chat.id,
        }

        if await files_col_1.find_one({"file_id": file_id}):
            return

        await files_col_1.insert_one(file_data)

        try:
            if not await files_col_2.find_one({"file_id": file_id}):
                await files_col_2.insert_one(file_data)
        except Exception:
            logger.exception("Failed to insert file into database 2")

        logger.info("📥 [AUTO-INDEXED LIVE] -> %s", clean_name)

    except Exception:
        logger.error("🚨 [AUTO-INDEX ERROR]: auto_index_uploaded_files failed", exc_info=True)


@Client.on_message(filters.command("index") & filters.private)
async def index_start_command(client: Client, message: Message):
    try:
        admins = getattr(Config, "ADMINS", [])
        if message.from_user.id not in admins:
            return await message.reply_text("⚠️ You are not authorized!")

        INDEX_STATE[message.from_user.id] = {"step": "waiting_bulk_index_message"}

        await message.reply_text(
            "📊 **Bulk Database Indexing**\n\n"
            "Please **forward the LAST message** from the source channel you want to bulk scan.\n\n"
            "⚠️ **Important:** Make sure the bot is an **Admin** in that source channel!\n\n"
            "Type /cancel to abort."
        )

    except Exception:
        logger.error("🚨 [CRITICAL COMMAND ERROR]: /index failed", exc_info=True)
        await message.reply_text("⚠️ An error occurred while starting the index process.")


@Client.on_message(filters.command("stats") & filters.private)
async def database_stats_command(client: Client, message: Message):
    try:
        admins = getattr(Config, "ADMINS", [])
        if message.from_user.id not in admins:
            return await message.reply_text("⚠️ You are not authorized!")

        count_db1 = await files_col_1.count_documents({})
        count_db2 = await files_col_2.count_documents({})

        database_status = (
            "ℹ️ Both collections use the same MongoDB URI."
            if Config.DATABASE_URI == Config.DATABASE_URI_2
            else "✅ Both databases are configured."
        )

        stats_text = (
            "📊 **Database File Statistics:**\n\n"
            f"• **Database 1 (`files`):** `{count_db1}` files\n"
            f"• **Database 2 (`files`):** `{count_db2}` files\n\n"
            f"{database_status}"
        )

        await message.reply_text(stats_text)

    except Exception:
        logger.error("🚨 [CRITICAL COMMAND ERROR]: /stats failed", exc_info=True)
        await message.reply_text("⚠️ Failed to fetch database statistics.")


@Client.on_message(filters.private & filters.text)
async def process_bulk_index_state(client: Client, message: Message):
    try:
        user_id = message.from_user.id
        if user_id not in INDEX_STATE:
            return

        if message.text and message.text.lower() == "/cancel":
            INDEX_STATE.pop(user_id, None)
            return await message.reply_text("❌ Cancelled.")

        forward_from = message.forward_from_chat
        if not forward_from:
            return await message.reply_text("⚠️ Please forward a message from the source channel.")

        chat_id = forward_from.id
        last_msg_id = message.forward_from_message_id

        if not last_msg_id:
            return await message.reply_text("⚠️ Could not determine the forwarded message ID.")

        INDEX_STATE.pop(user_id, None)
        await start_indexing_loop(client, message, chat_id, last_msg_id)

    except Exception:
        logger.error("🚨 [CRITICAL INPUT ERROR]: process_bulk_index_state failed", exc_info=True)
        await message.reply_text("⚠️ An error occurred during bulk index configuration.")


async def start_indexing_loop(client: Client, message: Message, chat_id: int, last_msg_id: int):
    status_msg = await message.reply_text("⏳ Initializing Live Bulk Indexing...")

    indexed = 0
    skipped = 0
    failed = 0

    try:
        for msg_id in range(1, last_msg_id + 1):
            try:
                msg = await client.get_messages(chat_id, msg_id)
                if not msg:
                    continue

                media = msg.document or msg.video
                if not media or not media.file_name:
                    continue

                file_id = media.file_id
                file_name = media.file_name
                clean_name = file_name.replace("_", " ").replace(".", " ")

                file_data = {
                    "file_name": clean_name,
                    "raw_name": file_name,
                    "file_id": file_id,
                    "file_size": media.file_size,
                    "message_id": msg.id,
                    "chat_id": chat_id,
                }

                exists = await files_col_1.find_one({"file_id": file_id})

                if exists:
                    skipped += 1
                else:
                    await files_col_1.insert_one(file_data)
                    indexed += 1

                    try:
                        exists_db2 = await files_col_2.find_one({"file_id": file_id})
                        if not exists_db2:
                            await files_col_2.insert_one(file_data)
                    except Exception:
                        logger.exception("Database 2 insert failed for file %s", file_id)

                processed = indexed + skipped + failed
                if processed % 5 == 0:
                    try:
                        await status_msg.edit_text(
                            "🔄 **Live Bulk Indexing in Progress...**\n\n"
                            f"• Scanned Msg ID: `{msg_id}/{last_msg_id}`\n"
                            f"• Successfully Indexed: `{indexed}`\n"
                            f"• Skipped (Duplicates): `{skipped}`\n"
                            f"• Failed/Non-Media: `{failed}`"
                        )
                    except Exception:
                        pass

            except Exception:
                failed += 1
                logger.exception("Error processing message ID %s", msg_id)
                continue

        await status_msg.edit_text(
            "✅ **Bulk Index Complete!**\n\n"
            f"• Total Indexed: `{indexed}`\n"
            f"• Total Skipped: `{skipped}`\n"
            f"• Errors/Bypassed: `{failed}`"
        )

    except Exception as e:
        logger.error("🚨 [INDEX LOOP ERROR]: %s", e, exc_info=True)
        try:
            await status_msg.edit_text(f"⚠️ **Indexing Error:**\n\n`{e}`")
        except Exception:
            pass
