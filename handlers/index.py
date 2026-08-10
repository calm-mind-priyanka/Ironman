import asyncio
from pyrogram import filters
from config import Config
from db import files_col_1, files_col_2
from core.state import INPUT
from core.utils import clean_query

def media_data(m):
    media = m.document or m.video or m.audio or m.animation
    if not media: return None
    name = getattr(media, "file_name", None) or m.caption or "Unnamed File"
    return {
        "file_id": media.file_id,
        "file_name": clean_query(name),
        "raw_name": getattr(media, "file_name", None) or name,
        "file_size": getattr(media, "file_size", 0),
        "message_id": m.id,
        "chat_id": m.chat.id,
    }

def register(app):
    @app.on_message(filters.document | filters.video | filters.audio | filters.animation, group=20)
    async def live_index(_, m):
        if Config.AUTO_INDEX_CHANNEL and m.chat.id != Config.AUTO_INDEX_CHANNEL: return
        data = media_data(m)
        if not data: return
        await files_col_1.update_one({"file_id":data["file_id"]},{"$set":data},upsert=True)
        try: await files_col_2.update_one({"file_id":data["file_id"]},{"$set":data},upsert=True)
        except Exception: pass

    @app.on_message(filters.command("index") & filters.private, group=0)
    async def index(_, m):
        if m.from_user.id not in Config.ADMINS: return await m.reply_text("⚠️ Admin only.")
        INPUT[m.from_user.id] = {"kind":"bulk_index"}
        await m.reply_text("📊 **Bulk Indexing**\n\nForward the LAST message from the source channel here.\nThe bot must be an admin in that channel.\n\n/cancel to stop.")

    @app.on_message(filters.private & filters.text, group=5)
    async def index_state(client, m):
        state = INPUT.get(m.from_user.id)
        if not state or state.get("kind") != "bulk_index": return
        if m.text.lower() == "/cancel":
            INPUT.pop(m.from_user.id,None); return await m.reply_text("❌ Cancelled.")
        if not m.forward_from_chat or not m.forward_from_message_id:
            return await m.reply_text("⚠️ Forward a message from the source channel.")
        INPUT.pop(m.from_user.id,None)
        chat_id, last_id = m.forward_from_chat.id, m.forward_from_message_id
        status = await m.reply_text("⏳ Starting bulk index...")
        indexed = skipped = failed = 0
        for mid in range(1, last_id + 1):
            try:
                msg = await client.get_messages(chat_id, mid)
                data = media_data(msg) if msg else None
                if not data: continue
                if await files_col_1.find_one({"file_id":data["file_id"]}):
                    skipped += 1; continue
                await files_col_1.insert_one(data); indexed += 1
                try: await files_col_2.update_one({"file_id":data["file_id"]},{"$set":data},upsert=True)
                except Exception: pass
                if (indexed + skipped + failed) % 10 == 0:
                    await status.edit_text(f"🔄 **Indexing...**\n\nScanned: `{mid}/{last_id}`\nIndexed: `{indexed}`\nSkipped: `{skipped}`\nFailed: `{failed}`")
            except Exception:
                failed += 1
        await status.edit_text(f"✅ **Index Complete**\n\nIndexed: `{indexed}`\nSkipped: `{skipped}`\nFailed: `{failed}`")
