import logging
from pyrogram import Client, filters
from pyrogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from db import forcesub_col

logger = logging.getLogger(__name__)

USER_FS_STATE = {}


@Client.on_callback_query(filters.regex("^set_force_channel$"))
async def force_channel_menu(client: Client, query: CallbackQuery):
    try:
        chat_id = query.message.chat.id
        cursor = forcesub_col.find({"chat_id": chat_id})
        channels = await cursor.to_list(length=10)

        text = "👥 **Multi-Force Subscribe Settings**\n\nLinked channels:\n"

        if channels:
            for idx, channel in enumerate(channels, 1):
                text += f"{idx}. {channel.get('title', 'Channel')} (`{channel.get('channel_id', 'N/A')}`)\n"
        else:
            text += "No channels added yet ❌\n"

        buttons = [
            [
                InlineKeyboardButton("➕ Add Channel", callback_data="fs_add"),
                InlineKeyboardButton("🗑️ Remove", callback_data="fs_remove"),
            ],
            [InlineKeyboardButton("<< Back", callback_data="back_to_settings")],
        ]

        await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(buttons))
        await query.answer()

    except Exception as e:
        logger.exception("Force-sub menu error: %s", e)
        try:
            await query.answer("⚠️ Failed to load force-sub settings.", show_alert=True)
        except Exception:
            pass


@Client.on_callback_query(filters.regex("^fs_add$"))
async def force_add_start(client: Client, query: CallbackQuery):
    try:
        USER_FS_STATE[query.from_user.id] = {"action": "add", "chat_id": query.message.chat.id}
        buttons = [[InlineKeyboardButton("❌ Cancel", callback_data="set_force_channel")]]

        await query.message.edit_text(
            "➕ **Add Force-Subscribe Channel**\n\n"
            "Send the channel ID or forward a message from the channel here.",
            reply_markup=InlineKeyboardMarkup(buttons),
        )
        await query.answer()

    except Exception as e:
        logger.exception("Force-sub add error: %s", e)


@Client.on_message(filters.private & filters.text, group=1)
async def force_sub_state_handler(client: Client, message: Message):
    user_id = message.from_user.id
    state = USER_FS_STATE.get(user_id)

    if not state or state.get("action") != "add":
        return

    try:
        channel_id = message.text.strip()

        try:
            channel_id = int(channel_id)
        except ValueError:
            await message.reply_text("⚠️ Please send a valid numeric channel ID.")
            return

        try:
            chat = await client.get_chat(channel_id)
        except Exception:
            await message.reply_text(
                "⚠️ I couldn't access that channel.\n\nMake sure the bot is an administrator in the channel."
            )
            return

        await forcesub_col.update_one(
            {"chat_id": state["chat_id"], "channel_id": channel_id},
            {"$set": {"chat_id": state["chat_id"], "channel_id": channel_id, "title": chat.title or "Channel"}},
            upsert=True,
        )

        USER_FS_STATE.pop(user_id, None)
        await message.reply_text(f"✅ Force-sub channel added:\n\n**{chat.title or 'Channel'}**\n`{channel_id}`")

    except Exception as e:
        logger.exception("Force-sub state handler error: %s", e)
        await message.reply_text("⚠️ Failed to add the channel.")


@Client.on_callback_query(filters.regex("^fs_remove$"))
async def force_remove_menu(client: Client, query: CallbackQuery):
    try:
        chat_id = query.message.chat.id
        cursor = forcesub_col.find({"chat_id": chat_id})
        channels = await cursor.to_list(length=10)

        if not channels:
            await query.answer("No force-sub channels found.", show_alert=True)
            return

        buttons = []
        for channel in channels:
            channel_id = channel.get("channel_id")
            title = channel.get("title", "Channel")
            buttons.append([InlineKeyboardButton(f"❌ {title}", callback_data=f"fs_delete:{channel_id}")])

        buttons.append([InlineKeyboardButton("⬅️ Back", callback_data="set_force_channel")])

        await query.message.edit_text(
            "🗑️ **Select a channel to remove:**",
            reply_markup=InlineKeyboardMarkup(buttons),
        )
        await query.answer()

    except Exception as e:
        logger.exception("Force-sub remove menu error: %s", e)


@Client.on_callback_query(filters.regex(r"^fs_delete:"))
async def force_delete(client: Client, query: CallbackQuery):
    try:
        channel_id = int(query.data.split(":", 1)[1])

        await forcesub_col.delete_one({"chat_id": query.message.chat.id, "channel_id": channel_id})

        await query.answer("✅ Channel removed.")
        await force_channel_menu(client, query)

    except Exception as e:
        logger.exception("Force-sub delete error: %s", e)
        await query.answer("⚠️ Failed to remove channel.", show_alert=True)
