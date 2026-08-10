from pyrogram import filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from config import Config
from core.settings import get, update
from core.keyboards import settings_kb
from core.state import INPUT

def register(app):
    @app.on_message(filters.command("settings") & filters.private, group=0)
    async def settings(_, m):
        if m.from_user.id not in Config.ADMINS: return await m.reply_text("⚠️ Admin only.")
        s = await get(m.chat.id)
        await m.reply_text("⚙️ **Settings Menu:**", reply_markup=settings_kb(s))

    @app.on_callback_query(filters.regex(r"^set#"))
    async def toggle(_, q):
        if q.from_user.id not in Config.ADMINS: return await q.answer("Admin only.", show_alert=True)
        key = q.data.split("#", 1)[1]
        s = await get(q.message.chat.id)
        await update(q.message.chat.id, key, not bool(s.get(key, True)))
        await q.message.edit_reply_markup(await settings_kb(await get(q.message.chat.id)))
        await q.answer("✅ Updated")

    @app.on_callback_query(filters.regex("^(caption|tutorial|movie_req|max_results)$"))
    async def input_menu(_, q):
        if q.from_user.id not in Config.ADMINS: return await q.answer("Admin only.", show_alert=True)
        kind = q.data
        s = await get(q.message.chat.id)
        labels = {
            "caption": f"📋 Current caption:\n\n`{s.get('files_caption','')}`\n\nSend the new caption.",
            "tutorial": f"🥁 Current tutorial:\n\n`{s.get('tutorial_link','')}`\n\nSend the new link.",
            "movie_req": f"📢 Current request chat:\n\n`{s.get('movie_req_chat','')}`\n\nSend the new username/ID.",
            "max_results": f"ℹ️ Current max results: `{s.get('max_results',10)}`\n\nSend a number from 1 to 20.",
        }
        INPUT[q.from_user.id] = {"kind": kind, "chat_id": q.message.chat.id}
        await q.message.edit_text(labels[kind], reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Back", callback_data="back_settings")]]))
        await q.answer()

    @app.on_callback_query(filters.regex("^details$"))
    async def details(_, q):
        if q.from_user.id not in Config.ADMINS: return await q.answer("Admin only.", show_alert=True)
        s = await get(q.message.chat.id)
        await q.answer(
            f"AutoFilter: {s.get('auto_filter')}\nFile secure: {s.get('file_secure')}\n"
            f"IMDb: {s.get('imdb')}\nSpell check: {s.get('spell_check')}\n"
            f"Auto delete: {s.get('auto_delete')}\nMax results: {s.get('max_results')}",
            show_alert=True
        )

    @app.on_callback_query(filters.regex("^back_settings$"))
    async def back(_, q):
        s = await get(q.message.chat.id)
        await q.message.edit_text("⚙️ **Settings Menu:**", reply_markup=settings_kb(s))
        await q.answer()

    @app.on_callback_query(filters.regex("^close_settings$"))
    async def close(_, q):
        await q.message.delete()
        await q.answer()

    @app.on_message(filters.private & filters.text, group=5)
    async def capture(_, m):
        if m.from_user.id not in INPUT or m.text.startswith("/"): return
        state = INPUT.pop(m.from_user.id)
        value = m.text.strip()
        kind = state["kind"]
        if kind == "max_results":
            try:
                value = max(1, min(20, int(value)))
            except ValueError:
                INPUT[m.from_user.id] = state
                return await m.reply_text("⚠️ Send a number from 1 to 20.")
        field = {"caption":"files_caption","tutorial":"tutorial_link","movie_req":"movie_req_chat","max_results":"max_results"}[kind]
        await update(state["chat_id"], field, value)
        await m.reply_text("✅ Setting updated.")
