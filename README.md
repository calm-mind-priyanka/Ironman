Fresh Full AutoFilter Bot
Fresh implementation for Koyeb Free using Dockerfile mode.
Included feature areas
Start/help menu
MongoDB file database
AutoFilter search in private and groups
Result buttons
Pagination
Language / quality / season filters
Send single file / send all
File-secure (protect_content)
Settings menu with toggles
Files caption
Tutorial link
Movie request chat setting
Max-results setting
Multi force-sub channel management
Admin premium add/remove
Broadcast
Database statistics
Automatic indexing from AUTO_INDEX_CHANNEL
Bulk indexing by forwarding the last source message
Shortlink URL configuration storage
Premium plan display
QR/payment callback foundation
Koyeb health endpoint
Deterministic one-time handler registration
No Smart Plugins
No manual importlib plugin discovery
No duplicate admin_actions.py
No .pyc or pycache files
Koyeb
Select Dockerfile deployment. Keep Dockerfile in the repository root.
Required environment variables: API_ID, API_HASH, BOT_TOKEN, DATABASE_URI, ADMINS
Optional: DATABASE_URI_2, DATABASE_NAME, LOG_CHANNEL, AUTO_INDEX_CHANNEL, RESULTS_PER_PAGE, DELETE_AFTER, PORT.
Startup
MongoDB -> indexes -> health server -> handler registration -> Telegram -> idle.
The process intentionally raises a visible traceback if startup fails; it does not silently exit after database checks.
