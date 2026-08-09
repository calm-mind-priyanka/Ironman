import datetime
from pyrogram import Client, filters
from pyrogram.types import Message
from motor.motor_asyncio import AsyncIOMotorClient
from config import Config
import logging

logger = logging.getLogger(__name__)

try:
    db_client = AsyncIOMotorClient(Config.DATABASE_URI)
    db = db_client[getattr(Config, "DATABASE_NAME", "AutoFilterBot")]
    premium_col = db["premium_users"]
    users_col = db["users"]
except Exception as e:
    logger.error(f"Failed to initialize collections in admin.py: {e}")

@Client.on_message(filters.command("add_premium") & filters.private)
async def add_premium_cmd(client: Client, message: Message):
    try:
        if message.from_user.id not in getattr(Config, "ADMINS", []):
            return await message.reply_text("⚠️ Unauthorized!")
        args = message.text.split()
        if len(args) < 3:
            return await message.reply_text("⚠️ Usage: `/add_premium [User_ID] [Days]`")
        try:
            uid, days = int(args[1]), int(args[2])
        except ValueError:
            return await message.reply_text("⚠️ Invalid format.")
            
        exp = datetime.datetime.now() + datetime.timedelta(days=days)
        await premium_col.update_one({"user_id": uid}, {"$set": {"expiry": exp}}, upsert=True)
        await message.reply_text(f"✅ Added user `{uid}` to Premium for `{days}` days.")
        
        try:
            await client.send_message(uid, f"🎉 You have been upgraded to Premium for {days} days!")
        except Exception:
            pass
    except Exception as err:
        logger.error(f"🚨 [CRITICAL COMMAND ERROR in admin.py]: /add_premium failed", exc_info=True)
        await message.reply_text("⚠️ An internal error occurred while processing this command.")

@Client.on_message(filters.command("remove_premium") & filters.private)
async def remove_premium_cmd(client: Client, message: Message):
    try:
        if message.from_user.id not in getattr(Config, "ADMINS", []):
            return await message.reply_text("⚠️ Unauthorized!")
        args = message.text.split()
        if len(args) < 2:
            return await message.reply_text("⚠️ Usage: `/remove_premium [User_ID]`")
        try:
            uid = int(args[1])
        except ValueError:
            return await message.reply_text("⚠️ Invalid User ID.")
            
        res = await premium_col.delete_one({"user_id": uid})
        if res.deleted_count > 0:
            await message.reply_text(f"✅ Removed user `{uid}` from Premium.")
        else:
            await message.reply_text(f"⚠️ User not found.")
    except Exception as err:
        logger.error(f"🚨 [CRITICAL COMMAND ERROR in admin.py]: /remove_premium failed", exc_info=True)
        await message.reply_text("⚠️ An internal error occurred while processing this command.")

@Client.on_message(filters.command("broadcast") & filters.private)
async def broadcast_cmd(client: Client, message: Message):
    try:
        if message.from_user.id not in getattr(Config, "ADMINS", []):
            return await message.reply_text("⚠️ Unauthorized!")
        if not message.reply_to_message:
            return await message.reply_text("⚠️ Please reply to a message to broadcast it!")
        
        all_users = await users_col.find({}).to_list(length=None)
        sent, failed = 0, 0
        status_msg = await message.reply_text(f"🚀 Broadcasting to `{len(all_users)}` users...")
        
        for user in all_users:
            try:
                await message.reply_to_message.copy(chat_id=user["user_id"])
                sent += 1
            except Exception:
                failed += 1
                
        await status_msg.edit_text(f"✅ **Broadcast Completed:**\n• Successful: `{sent}`\n• Failed: `{failed}`")
    except Exception as err:
        logger.error(f"🚨 [CRITICAL COMMAND ERROR in admin.py]: /broadcast failed", exc_info=True)
        await message.reply_text("⚠️ An internal error occurred while running the broadcast.")
