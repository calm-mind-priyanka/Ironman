import datetime
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from motor.motor_asyncio import AsyncIOMotorClient
from config import Config
import logging

logger = logging.getLogger(__name__)

try:
    db_client = AsyncIOMotorClient(Config.DATABASE_URI)
    db = db_client[getattr(Config, "DATABASE_NAME", "AutoFilterBot")]
    premium_col = db["premium_users"]
except Exception as e:
    logger.error(f"Failed to initialize premium collection in premium.py: {e}")

WAITING_SS = set()

@Client.on_callback_query(filters.regex("^my_plan_menu$"))
async def my_plan(client: Client, query: CallbackQuery):
    try:
        text = "💎 **SUBSCRIPTION PLAN**\n\nUpgrade to Premium to completely bypass shortlinks."
        buttons = [
            [InlineKeyboardButton("⚡ Buy Premium (QR Code)", callback_data="buy_qr")], 
            [InlineKeyboardButton("<< Back", callback_data="back_to_settings")]
        ]
        await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(buttons))
        await query.answer()
    except Exception as err:
        logger.error(f"🚨 [CALLBACK ERROR in premium.py]: my_plan failed", exc_info=True)
        await query.answer("⚠️ Failed to load subscription menu.", show_alert=True)

@Client.on_callback_query(filters.regex("^buy_qr$"))
async def buy_qr(client: Client, query: CallbackQuery):
    try:
        WAITING_SS.add(query.from_user.id)
        await query.message.reply_photo(
            photo="https://envs.sh/QR_SAMPLE.jpg",
            caption="Scan QR code, make payment, and send your receipt screenshot here."
        )
        await query.answer()
    except Exception as err:
        logger.error(f"🚨 [CALLBACK ERROR in premium.py]: buy_qr failed", exc_info=True)
        await query.answer("⚠️ Failed to load QR code.", show_alert=True)

@Client.on_message(filters.photo & filters.private)
async def handle_ss(client: Client, message: Message):
    try:
        user_id = message.from_user.id
        if user_id not in WAITING_SS:
            return
        
        WAITING_SS.remove(user_id)
        
        log_channel = getattr(Config, "LOG_CHANNEL", None)
        if not log_channel:
            logger.error("LOG_CHANNEL is missing in config.py! Cannot forward payment screenshot.")
            return await message.reply_text("⚠️ Configuration error: Log channel is not configured.")

        buttons = InlineKeyboardMarkup([[InlineKeyboardButton("✅ Approve 30 Days", callback_data=f"app#{user_id}")]])
        await client.send_photo(
            chat_id=log_channel, 
            photo=message.photo.file_id, 
            caption=f"Payment from user `{user_id}`", 
            reply_markup=buttons
        )
        await message.reply_text("✅ Screenshot sent to admin for verification.")
    except Exception as err:
        logger.error(f"🚨 [CRITICAL INPUT ERROR in premium.py]: handle_ss failed", exc_info=True)
        await message.reply_text("⚠️ An error occurred while submitting your payment screenshot.")

@Client.on_callback_query(filters.regex("^app#"))
async def approve_prem(client: Client, query: CallbackQuery):
    try:
        uid = int(query.data.split("#")[1])
        exp = datetime.datetime.now() + datetime.timedelta(days=30)
        await premium_col.update_one({"user_id": uid}, {"$set": {"expiry": exp}}, upsert=True)
        
        current_caption = query.message.caption or ""
        await query.message.edit_caption(f"{current_caption}\n\n**APPROVED ✅**")
        
        try:
            await client.send_message(uid, "🎉 Your 30-day Premium plan is now active!")
        except Exception:
            pass
            
        await query.answer("✅ User approved successfully!")
    except Exception as err:
        logger.error(f"🚨 [CALLBACK ERROR in premium.py]: approve_prem failed", exc_info=True)
        await query.answer("⚠️ Failed to approve premium status.", show_alert=True)
