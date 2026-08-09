from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
import logging

from config import Config
from db import users_col

logger = logging.getLogger(__name__)


@Client.on_message(filters.command("start") & filters.private)
async def start_cmd(client: Client, message: Message):
    try:
        user_id = message.from_user.id

        existing_user = await users_col.find_one(
            {"user_id": user_id}
        )

        if not existing_user:
            await users_col.insert_one(
                {
                    "user_id": user_id,
                    "name": message.from_user.first_name
                }
            )

        text = (
            f"👋 Hello **{message.from_user.first_name}**!\n\n"
            "I am your Advanced Auto-Filter Bot.\n"
            "🎯 Send me any movie name to search."
        )

        buttons = [
            [
                InlineKeyboardButton(
                    "🔍 Search Here",
                    switch_inline_query_current_chat=""
                ),
                InlineKeyboardButton(
                    "💎 My Plan",
                    callback_data="my_plan_menu"
                )
            ],
            [
                InlineKeyboardButton(
                    "⚙️ Help",
                    callback_data="help_menu"
                )
            ]
        ]

        await message.reply_text(
            text,
            reply_markup=InlineKeyboardMarkup(buttons)
        )

    except Exception as e:
        logger.exception(
            "Error in /start: %s",
            e
        )

        await message.reply_text(
            "⚠️ Something went wrong. Please try again later."
        )


@Client.on_callback_query(filters.regex("^help_menu$"))
async def help_menu(
    client: Client,
    query
):
    try:
        text = (
            "📚 **Help Menu**\n\n"
            "🔍 Use the search button to search for files.\n"
            "🎬 You can also send a movie name in supported groups.\n\n"
            "If you need help, contact the bot administrator."
        )

        buttons = [
            [
                InlineKeyboardButton(
                    "⬅️ Back",
                    callback_data="back_to_start"
                )
            ]
        ]

        await query.message.edit_text(
            text,
            reply_markup=InlineKeyboardMarkup(buttons)
        )

        await query.answer()

    except Exception as e:
        logger.exception(
            "Error in help menu: %s",
            e
        )

        try:
            await query.answer(
                "⚠️ Failed to open help.",
                show_alert=True
            )
        except Exception:
            pass


@Client.on_callback_query(filters.regex("^back_to_start$"))
async def back_to_start(
    client: Client,
    query
):
    try:
        first_name = query.from_user.first_name

        text = (
            f"👋 Hello **{first_name}**!\n\n"
            "I am your Advanced Auto-Filter Bot.\n"
            "🎯 Send me any movie name to search."
        )

        buttons = [
            [
                InlineKeyboardButton(
                    "🔍 Search Here",
                    switch_inline_query_current_chat=""
                ),
                InlineKeyboardButton(
                    "💎 My Plan",
                    callback_data="my_plan_menu"
                )
            ],
            [
                InlineKeyboardButton(
                    "⚙️ Help",
                    callback_data="help_menu"
                )
            ]
        ]

        await query.message.edit_text(
            text,
            reply_markup=InlineKeyboardMarkup(buttons)
        )

        await query.answer()

    except Exception as e:
        logger.exception(
            "Error returning to start menu: %s",
            e
        )

        try:
            await query.answer(
                "⚠️ Failed to go back.",
                show_alert=True
            )
        except Exception:
            pass
