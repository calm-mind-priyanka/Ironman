from pyrogram import filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from db import users_col
from core.keyboards import start_kb

def register(app):
    @app.on_message(filters.command("start") & filters.private, group=0)
    async def start(_, m):
        await users_col.update_one({"user_id": m.from_user.id},
            {"$set": {"user_id": m.from_user.id, "name": m.from_user.first_name},
             "$setOnInsert": {"joined": True}}, upsert=True)
        await m.reply_text(
            "👋 **Welcome!**\n\nSend a movie/series/file name and I'll search the database.",
            reply_markup=start_kb()
        )

    @app.on_message(filters.command("help") & filters.private, group=0)
    async def help_cmd(_, m):
        await m.reply_text(
            "**AutoFilter Bot Help**\n\n"
            "• Send a movie or series name to search\n"
            "• Use the result buttons for language, quality and season filters\n"
            "• `/settings` — admin settings\n"
            "• `/stats` — admin database stats\n"
            "• `/index` — admin bulk indexing\n"
            "• `/add_premium ID DAYS` — admin premium\n"
            "• `/broadcast` — reply to a message and broadcast it"
        )

    @app.on_callback_query(filters.regex("^help$"))
    async def help_cb(_, q):
        await q.answer()
        await q.message.edit_text(
            "**Help**\n\nSend a movie/series name to search. Use the filter buttons below results."
        )

    @app.on_callback_query(filters.regex("^plan$"))
    async def plan_cb(_, q):
        from handlers.premium import plan_text
        await q.answer()
        await q.message.edit_text(await plan_text(q.from_user.id),
                                  reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Back", callback_data="back_start")]]))

    @app.on_callback_query(filters.regex("^back_start$"))
    async def back_start(_, q):
        await q.answer()
        await q.message.edit_text("👋 **Welcome back!**", reply_markup=start_kb())
