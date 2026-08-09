import datetime
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from motor.motor_asyncio import AsyncIOMotorClient
from config import Config

db_client = AsyncIOMotorClient(Config.DATABASE_URI)
db = db_client[Config.DATABASE_NAME]
premium_col = db["premium_users"]
WAITING_SS = set()

@Client.on_callback_query(filters.regex("^my_plan_menu$"))
async def my_plan(client: Client, query: CallbackQuery):
    text = "💎 **SUBSCRIPTION PLAN**\n\nUpgrade to Premium to completely bypass shortlinks."
    buttons = [[InlineKeyboardButton("⚡ Buy Premium (QR Code)", callback_data="buy_qr")], [InlineKeyboardButton("<< Back", callback_data="back_to_settings")]]
    await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(buttons))

@Client.on_callback_query(filters.regex("^buy_qr$"))
async def buy_qr(client: Client, query: CallbackQuery):
    WAITING_SS.add(query.from_user.id)
    await query.message.reply_photo(
        photo="https://envs.sh/QR_SAMPLE.jpg",
        caption="Scan QR code, make payment, and send your receipt screenshot here."
    )

@Client.on_message(filters.photo & filters.private)
async def handle_ss(client: Client, message: Message):
    if message.from_user.id not in WAITING_SS:
        return
    WAITING_SS.remove(message.from_user.id)
    buttons = InlineKeyboardMarkup([[InlineKeyboardButton("✅ Approve 30 Days", callback_data=f"app#{message.from_user.id}")]])
    await client.send_photo(chat_id=Config.LOG_CHANNEL, photo=message.photo.file_id, caption=f"Payment from user `{message.from_user.id}`", reply_markup=buttons)
    await message.reply_text("✅ Screenshot sent to admin for verification.")

@Client.on_callback_query(filters.regex("^app#"))
async def approve_prem(client: Client, query: CallbackQuery):
    uid = int(query.data.split("#")[1])
    exp = datetime.datetime.now() + datetime.timedelta(days=30)
    await premium_col.update_one({"user_id": uid}, {"$set": {"expiry": exp}}, upsert=True)
    await query.message.edit_caption(f"{query.message.caption}\n\n**APPROVED ✅**")
    await client.send_message(uid, "🎉 Your 30-day Premium plan is now active!")
