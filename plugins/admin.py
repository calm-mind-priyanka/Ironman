import datetime
import logging

from pyrogram import Client, filters
from pyrogram.types import Message

from config import Config
from db import premium_col, users_col

logger = logging.getLogger(__name__)


@Client.on_message(filters.command("add_premium") & filters.private)
async def add_premium_cmd(client: Client, message: Message):
    try:
        if message.from_user.id not in getattr(Config, "ADMINS", []):
            return await message.reply_text("⚠️ Unauthorized!")

        args = message.text.split()
        if len(args) < 3:
            return await message.reply_text("⚠️ Usage: `/add_premium [User_ID] [Days]`")

        try:
            uid = int(args[1])
            days = int(args[2])
        except ValueError:
            return await message.reply_text("⚠️ Invalid format.")

        if days <= 0:
            return await message.reply_text("⚠️ Days must be greater than 0.")

        expiry = datetime.datetime.now() + datetime.timedelta(days=days)

        await premium_col.update_one(
            {"user_id": uid},
            {"$set": {"user_id": uid, "expiry": expiry}},
            upsert=True,
        )

        await message.reply_text(f"✅ Added user `{uid}` to Premium for `{days}` days.")

        try:
            await client.send_message(uid, f"🎉 You have been upgraded to Premium for {days} days!")
        except Exception:
            pass

    except Exception:
        logger.error("🚨 [CRITICAL COMMAND ERROR]: /add_premium failed", exc_info=True)
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

        result = await premium_col.delete_one({"user_id": uid})

        if result.deleted_count > 0:
            await message.reply_text(f"✅ Removed user `{uid}` from Premium.")
        else:
            await message.reply_text("⚠️ User not found.")

    except Exception:
        logger.error("🚨 [CRITICAL COMMAND ERROR]: /remove_premium failed", exc_info=True)
        await message.reply_text("⚠️ An internal error occurred while processing this command.")


@Client.on_message(filters.command("broadcast") & filters.private)
async def broadcast_cmd(client: Client, message: Message):
    try:
        if message.from_user.id not in getattr(Config, "ADMINS", []):
            return await message.reply_text("⚠️ Unauthorized!")

        if not message.reply_to_message:
            return await message.reply_text("⚠️ Please reply to a message to broadcast it!")

        all_users = await users_col.find({}).to_list(length=None)
        sent = 0
        failed = 0

        status_msg = await message.reply_text(f"🚀 Broadcasting to `{len(all_users)}` users...")

        for user in all_users:
            try:
                user_id = user.get("user_id")
                if not user_id:
                    failed += 1
                    continue

                await message.reply_to_message.copy(chat_id=user_id)
                sent += 1
            except Exception:
                failed += 1

        await status_msg.edit_text(
            f"✅ **Broadcast Completed:**\n\n• Successful: `{sent}`\n• Failed: `{failed}`"
        )

    except Exception:
        logger.error("🚨 [CRITICAL COMMAND ERROR]: /broadcast failed", exc_info=True)
        await message.reply_text("⚠️ An internal error occurred while running the broadcast.")
