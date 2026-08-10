from motor.motor_asyncio import AsyncIOMotorClient
from config import Config

db1_client = AsyncIOMotorClient(Config.DATABASE_URI, serverSelectionTimeoutMS=10000)
db1 = db1_client[Config.DATABASE_NAME]

db2_client = AsyncIOMotorClient(Config.DATABASE_URI_2, serverSelectionTimeoutMS=10000)
db2 = db2_client[Config.DATABASE_NAME]

users_col = db1["users"]
premium_col = db1["premium_users"]
settings_col = db1["settings"]
forcesub_col = db1["forcesub_channels"]
shortlink_col = db1["shortlinks"]
files_col_1 = db1["files"]
files_col_2 = db2["files"]

async def ping():
    await db1_client.admin.command("ping")
    if Config.DATABASE_URI_2 != Config.DATABASE_URI:
        await db2_client.admin.command("ping")

async def ensure_indexes():
    await users_col.create_index("user_id", unique=True)
    await premium_col.create_index("user_id", unique=True)
    await settings_col.create_index("chat_id", unique=True)
    await forcesub_col.create_index([("chat_id", 1), ("channel_id", 1)], unique=True)
    await shortlink_col.create_index("chat_id", unique=True)
    await files_col_1.create_index("file_id", unique=True)
    await files_col_1.create_index("file_name")
    await files_col_2.create_index("file_id", unique=True)
    await files_col_2.create_index("file_name")
