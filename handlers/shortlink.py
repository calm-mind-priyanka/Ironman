from pyrogram import filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from db import shortlink_col
from config import Config
from core.state import INPUT

def register(app):
    @app.on_callback_query(filters.regex("^shortlink$"))
    async def menu(_,q):
        if q.from_user.id not in Config.ADMINS: return await q.answer("Admin only.",show_alert=True)
        s=await shortlink_col.find_one({"chat_id":q.message.chat.id}) or {}
        await q.message.edit_text(
            "🔗 **Shortlink Settings**\n\n"
            f"1st URL: `{s.get('first','Not set')}`\n"
            f"2nd URL: `{s.get('second','Not set')}`",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("1st Shortlink",callback_data="sl#1"),
                 InlineKeyboardButton("2nd Shortlink",callback_data="sl#2")],
                [InlineKeyboardButton("🗑️ Delete Shortlinks",callback_data="sl_delete")],
                [InlineKeyboardButton("⬅️ Back",callback_data="back_settings")]
            ])); await q.answer()

    @app.on_callback_query(filters.regex(r"^sl#"))
    async def edit(_,q):
        if q.from_user.id not in Config.ADMINS: return await q.answer("Admin only.",show_alert=True)
        slot=q.data.split("#")[1]; INPUT[q.from_user.id]={"kind":f"sl{slot}","chat_id":q.message.chat.id}
        await q.message.edit_text(f"🔗 Send the URL for shortlink #{slot}.")
        await q.answer()

    @app.on_callback_query(filters.regex("^sl_delete$"))
    async def delete(_,q):
        await shortlink_col.delete_one({"chat_id":q.message.chat.id})
        await q.answer("✅ Deleted")
        await menu(_,q)

    @app.on_message(filters.private & filters.text,group=5)
    async def capture(_,m):
        st=INPUT.get(m.from_user.id)
        if not st or not st.get("kind","").startswith("sl"): return
        kind=st["kind"]; slot="first" if kind=="sl1" else "second"
        await shortlink_col.update_one({"chat_id":st["chat_id"]},{"$set":{slot:m.text.strip()}},upsert=True)
        INPUT.pop(m.from_user.id,None); await m.reply_text("✅ Shortlink URL saved.")
