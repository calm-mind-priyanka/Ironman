from datetime import datetime, timedelta
from pyrogram import filters
from db import premium_col, users_col
from config import Config

def is_admin(uid): return uid in Config.ADMINS

def register(app):
    @app.on_message(filters.command("add_premium") & filters.private, group=0)
    async def add_premium(_, m):
        if not is_admin(m.from_user.id): return await m.reply_text("⚠️ Unauthorized.")
        a = m.text.split()
        if len(a) != 3: return await m.reply_text("Usage: `/add_premium USER_ID DAYS`")
        try: uid, days = int(a[1]), int(a[2])
        except: return await m.reply_text("⚠️ Invalid user ID/days.")
        if days <= 0: return await m.reply_text("⚠️ Days must be greater than 0.")
        expiry = datetime.utcnow() + timedelta(days=days)
        await premium_col.update_one({"user_id": uid}, {"$set": {"user_id": uid, "expiry": expiry}}, upsert=True)
        await m.reply_text(f"✅ Premium added for `{uid}` for `{days}` days.")

    @app.on_message(filters.command("remove_premium") & filters.private, group=0)
    async def remove_premium(_, m):
        if not is_admin(m.from_user.id): return await m.reply_text("⚠️ Unauthorized.")
        a = m.text.split()
        if len(a) != 2: return await m.reply_text("Usage: `/remove_premium USER_ID`")
        try: uid = int(a[1])
        except: return await m.reply_text("⚠️ Invalid user ID.")
        r = await premium_col.delete_one({"user_id": uid})
        await m.reply_text("✅ Premium removed." if r.deleted_count else "⚠️ User has no premium record.")

    @app.on_message(filters.command("broadcast") & filters.private, group=0)
    async def broadcast(_, m):
        if not is_admin(m.from_user.id): return await m.reply_text("⚠️ Unauthorized.")
        if not m.reply_to_message: return await m.reply_text("⚠️ Reply to the message you want to broadcast.")
        users = await users_col.find({}, {"user_id": 1}).to_list(length=None)
        status = await m.reply_text(f"🚀 Broadcasting to `{len(users)}` users...")
        ok = bad = 0
        for u in users:
            try:
                await m.reply_to_message.copy(u["user_id"])
                ok += 1
            except Exception:
                bad += 1
        await status.edit_text(f"✅ **Broadcast complete**\n\nSuccessful: `{ok}`\nFailed: `{bad}`")

    @app.on_message(filters.command("stats") & filters.private, group=0)
    async def stats(_, m):
        if not is_admin(m.from_user.id): return await m.reply_text("⚠️ Unauthorized.")
        c1 = await __import__("db").files_col_1.count_documents({})
        c2 = await __import__("db").files_col_2.count_documents({})
        users = await users_col.count_documents({})
        prem = await premium_col.count_documents({})
        await m.reply_text(f"📊 **Stats**\n\nDB1 files: `{c1}`\nDB2 files: `{c2}`\nUsers: `{users}`\nPremium records: `{prem}`")
