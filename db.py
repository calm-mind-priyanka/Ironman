from motor.motor_asyncio import AsyncIOMotorClient
from config import Config

# Database 1 Clients & Collections
db1_client = AsyncIOMotorClient(Config.DATABASE_URI)
db1 = db1_client[Config.DATABASE_NAME]

users_col = db1["users"]
premium_col = db1["premium_users"]
settings_col = db1["settings"]
forcesub_col = db1["forcesub_channels"]
shortlink_col = db1["shortlinks"]
files_col_1 = db1["files"]

# Database 2 Clients & Collections
db2_client = AsyncIOMotorClient(Config.DATABASE_URI_2)
db2 = db2_client[Config.DATABASE_NAME]

files_col_2 = db2["files"]

# Backward Compatibility
db = db1
