from db import settings_col

DEFAULTS = {
    "auto_filter": True,
    "file_secure": True,
    "imdb": True,
    "spell_check": True,
    "auto_delete": False,
    "result_mode": True,
    "files_mode": True,
    "files_caption": "📂 **{file_name}**\n💾 Size: {file_size}",
    "tutorial_link": "https://t.me/your_tutorial_channel",
    "movie_req_chat": "Not Set ❌",
    "max_results": 10,
}

async def get(chat_id):
    doc = await settings_col.find_one({"chat_id": chat_id})
    if not doc:
        doc = {"chat_id": chat_id, **DEFAULTS}
        await settings_col.insert_one(doc)
    else:
        missing = {k: v for k, v in DEFAULTS.items() if k not in doc}
        if missing:
            await settings_col.update_one({"chat_id": chat_id}, {"$set": missing})
            doc.update(missing)
    return doc

async def update(chat_id, key, value):
    await settings_col.update_one({"chat_id": chat_id}, {"$set": {key: value}}, upsert=True)
    return await get(chat_id)
