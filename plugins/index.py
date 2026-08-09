import asyncio
from pyrogram import Client, filters
from pyrogram.types import Message
from motor.motor_asyncio import AsyncIOMotorClient
from config import Config

db1_client = AsyncIOMotorClient(Config.DATABASE_URI)
db1 = db1_client[Config.DATABASE_NAME]
files_col_1 = db1["files"]

db2_client = AsyncIOMotorClient(Config.DATABASE_URI_2)
db2 = db2_client[Config.DATABASE_NAME]
files_col_2 = db2["files"]

INDEX_STATE = {}

@Client.on_message((filters.document | filters.video))
async def auto_index_uploaded_files(client: Client, message: Message):
    if not Config.AUTO_INDEX_CHANNEL or message.chat.id != Config.AUTO_INDEX_CHANNEL:
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
        "chat_id": message.chat.id
    }

    if await files_col_1.find_one({"file_id": file_id}):
        return

    await files_col_1.insert_one(file_data)
    await files_col_2.insert_one(file_data)
    print(f"📥 [AUTO-INDEXED LIVE] -> {clean_name}")


@Client.on_message(filters.command("index") & filters.private)
async def index_start_command(client: Client, message: Message):
    if message.from_user.id not in Config.ADMINS:
        return await message.reply_text("⚠️ You are not authorized!")

    INDEX_STATE[message.from_user.id] = {"step": "waiting_bulk_index_message"}
    await message.reply_text(
        "📊 **Bulk Database Indexing**\n\n"
        "Please **forward the LAST message** from the source channel you want to bulk scan.\n\n"
        "⚠️ **Important:** Make sure the bot is an **Admin** in that source channel!\n\n"
        "Type /cancel to abort."
    )


@Client.on_message(filters.private & filters.text)
async def process_bulk_index_state(client: Client, message: Message):
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
    
    INDEX_STATE.pop(user_id, None)
    await start_indexing_loop(client, message, chat_id, last_msg_id)


async def start_indexing_loop(client: Client, message: Message, chat_id: int, last_msg_id: int):
    status_msg = await message.reply_text("⏳ Initializing Live Bulk Indexing...")
    indexed, skipped, failed = 0, 0, 0
    
    try:
        for msg_id in range(1, last_msg_id + 1):
            try:
                msg = await client.get_messages(chat_id, msg_id)
                if not msg or not (msg.document or msg.video):
                    continue

                media = msg.document or msg.video
                if not media.file_name:
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
                    "chat_id": chat_id
                }

                if await files_col_1.find_one({"file_id": file_id}):
                    skipped += 1
                else:
                    await files_col_1.insert_one(file_data)
                    await files_col_2.insert_one(file_data)
                    indexed += 1

                # Live update every 5 items so you see real-time progress without hitting Telegram FloodLimits
                if (indexed + skipped) % 5 == 0:
                    await status_msg.edit_text(
                        f"🔄 **Live Bulk Indexing in Progress...**\n\n"
                        f"• Total Scanned: `{msg_id}/{last_msg_id}`\n"
                        f"• Successfully Indexed: `{indexed}`\n"
                        f"• Skipped (Duplicates): `{skipped}`"
                    )
            except Exception:
                failed += 1
                continue

        await status_msg.edit_text(
            f"✅ **Bulk Index Complete!**\n\n"
            f"• Total Indexed: `{indexed}`\n"
            f"• Total Skipped: `{skipped}`\n"
            f"• Errors/Bypassed: `{failed}`"
        )
    except Exception as e:
        await status_msg.edit_text(f"⚠️ Indexing Error: {e}")
