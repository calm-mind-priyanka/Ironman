from datetime import datetime
from db import premium_col

async def plan_text(uid):
    doc = await premium_col.find_one({"user_id": uid})
    if not doc: return "💎 **My Plan**\n\nYou are currently on the **Free Plan**."
    expiry = doc.get("expiry")
    if not expiry or expiry <= datetime.utcnow():
        return "💎 **My Plan**\n\nYour Premium plan has expired."
    return f"💎 **My Plan**\n\n✅ Premium active\n📅 Expiry: `{expiry:%Y-%m-%d %H:%M UTC}`"

def register(app):
    pass
