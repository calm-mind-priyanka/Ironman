# Optional QR/premium approval foundation. No payment gateway is hard-coded.
from pyrogram import filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from config import Config
from core.state import INPUT

def register(app):
    @app.on_callback_query(filters.regex("^buy_qr$"))
    async def qr(_,q):
        if not Config.ADMINS: return await q.answer("Premium purchase is not configured.",show_alert=True)
        await q.answer("Configure your payment QR flow in your own deployment.",show_alert=True)

    @app.on_callback_query(filters.regex(r"^app#"))
    async def approve(_,q):
        if q.from_user.id not in Config.ADMINS: return await q.answer("Admin only.",show_alert=True)
        await q.answer("Use /add_premium USER_ID DAYS for approval.",show_alert=True)
