from pyrogram import Client, filters
from pyrogram.types import Message
from config import Config

@Client.on_message(filters.command("ban"))
async def ban_user_cmd(client: Client, message: Message):
    if message.chat.type == "private":
        return await message.reply_text("⚠️ This command can only be used inside group chats!")
    
    chat_id = message.chat.id
    try:
        member = await client.get_chat_member(chat_id, message.from_user.id)
        if member.status not in ["creator", "administrator"] and message.from_user.id not in Config.ADMINS:
            return await message.reply_text("⚠️ Only admins can use this command!")
    except Exception:
        if message.from_user.id not in Config.ADMINS:
            return await message.reply_text("⚠️ Only admins can use this command!")

    if not message.reply_to_message:
        return await message.reply_text("⚠️ Reply to the user you want to ban!")
    
    user_to_ban = message.reply_to_message.from_user.id
    try:
        await client.ban_chat_member(chat_id, user_to_ban)
        await message.reply_text(f"✅ Banned user (`{user_to_ban}`).")
    except Exception as e:
        await message.reply_text(f"⚠️ Error: {e}")

@Client.on_message(filters.command("kick"))
async def kick_user_cmd(client: Client, message: Message):
    if message.chat.type == "private":
        return await message.reply_text("⚠️ This command can only be used inside group chats!")
    
    chat_id = message.chat.id
    try:
        member = await client.get_chat_member(chat_id, message.from_user.id)
        if member.status not in ["creator", "administrator"] and message.from_user.id not in Config.ADMINS:
            return await message.reply_text("⚠️ Only admins can use this command!")
    except Exception:
        if message.from_user.id not in Config.ADMINS:
            return await message.reply_text("⚠️ Only admins can use this command!")

    if not message.reply_to_message:
        return await message.reply_text("⚠️ Reply to the user you want to kick!")
    
    user_to_kick = message.reply_to_message.from_user.id
    try:
        await client.ban_chat_member(chat_id, user_to_kick)
        await client.unban_chat_member(chat_id, user_to_kick)
        await message.reply_text(f"✅ Kicked user (`{user_to_kick}`).")
    except Exception as e:
        await message.reply_text(f"⚠️ Error: {e}")

@Client.on_message(filters.command("leave"))
async def leave_group_cmd(client: Client, message: Message):
    if message.from_user.id not in Config.ADMINS:
        return await message.reply_text("⚠️ Only global bot admins can run this!")
    try:
        await message.reply_text("👋 Leaving this group...")
        await client.leave_chat(message.chat.id)
    except Exception as e:
        await message.reply_text(f"⚠️ Error: {e}")
