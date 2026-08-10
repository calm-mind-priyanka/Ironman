from pyrogram import filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from pyrogram.errors import UserNotParticipant
from config import Config
from db import forcesub_col
from core.state import INPUT

def register(app):
    @app.on_callback_query(filters.regex("^forcesub$"))
    async def menu(_, q):
        if q.from_user.id not in Config.ADMINS: return await q.answer("Admin only.", show_alert=True)
        chans = await forcesub_col.find({"chat_id": q.message.chat.id}).to_list(length=20)
        text = "👥 **Force Subscribe Channels**\n\n" + ("\n".join(f"• {x.get('title','Channel')} `{x['channel_id']}`" for x in chans) if chans else "No channels added ❌")
        await q.message.edit_text(text, reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("➕ Add Channel", callback_data="fs_add"), InlineKeyboardButton("🗑️ Remove", callback_data="fs_remove")],
            [InlineKeyboardButton("⬅️ Back", callback_data="back_settings")]
        ]))
        await q.answer()

    @app.on_callback_query(filters.regex("^fs_add$"))
    async def add(_, q):
        if q.from_user.id not in Config.ADMINS: return await q.answer("Admin only.", show_alert=True)
        INPUT[q.from_user.id] = {"kind":"force_channel","chat_id":q.message.chat.id}
        await q.message.edit_text("➕ Send the channel ID or username. The bot must be an admin there.")
        await q.answer()

    @app.on_callback_query(filters.regex("^fs_remove$"))
    async def remove(_, q):
        chans = await forcesub_col.find({"chat_id": q.message.chat.id}).to_list(length=20)
        buttons = [[InlineKeyboardButton(f"❌ {x.get('title','Channel')}", callback_data=f"fs_del#{x['channel_id']}")] for x in chans]
        buttons.append([InlineKeyboardButton("⬅️ Back", callback_data="forcesub")])
        await q.message.edit_text("🗑️ **Remove channel:**", reply_markup=InlineKeyboardMarkup(buttons))
        await q.answer()

    @app.on_callback_query(filters.regex("^fs_del#"))
    async def delete(_, q):
        cid = int(q.data.split("#",1)[1])
        await forcesub_col.delete_one({"chat_id": q.message.chat.id, "channel_id": cid})
        await q.answer("✅ Removed")
        await menu(_, q)

    @app.on_message(filters.private & filters.text, group=5)
    async def add_input(client, m):
        state = INPUT.get(m.from_user.id)
        if not state or state.get("kind") != "force_channel": return
        try:
            chat = await client.get_chat(m.text.strip())
            await forcesub_col.update_one({"chat_id":state["chat_id"],"channel_id":chat.id},
                {"$set":{"chat_id":state["chat_id"],"channel_id":chat.id,"title":chat.title or "Channel"}}, upsert=True)
            INPUT.pop(m.from_user.id, None)
            await m.reply_text(f"✅ Added **{chat.title or 'Channel'}**")
        except Exception:
            await m.reply_text("⚠️ I can't access that channel. Make sure I'm an admin.")

    @app.on_message(filters.all, group=1)
    async def enforce(client, m):
        # Only enforce in private/group messages where a user is present; admins bypass.
        if not m.from_user or m.from_user.id in Config.ADMINS or m.chat is None: return
        chans = await forcesub_col.find({"chat_id": m.chat.id}).to_list(length=10)
        if not chans: return
        missing = []
        for c in chans:
            try:
                member = await client.get_chat_member(c["channel_id"], m.from_user.id)
                if member.status in ("left", "kicked"):
                    missing.append(c)
            except Exception:
                continue
        if missing:
            buttons = []
            for c in missing:
                try:
                    chat = await client.get_chat(c["channel_id"])
                    if chat.username:
                        buttons.append([InlineKeyboardButton(f"📢 Join {c.get('title','Channel')}", url=f"https://t.me/{chat.username}")])
                except Exception: pass
            buttons.append([InlineKeyboardButton("✅ Try Again", callback_data="check_fs")])
            try:
                await m.reply_text("🔒 **Please join the required channel(s) first.**", reply_markup=InlineKeyboardMarkup(buttons))
            except Exception: pass
            try:
                await m.stop_propagation()
            except Exception: pass

    @app.on_callback_query(filters.regex("^check_fs$"))
    async def check(_, q):
        await q.answer("Please send your message again after joining.", show_alert=True)
