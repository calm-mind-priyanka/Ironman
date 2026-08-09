import logging
from pyrogram import Client
from config import Config
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Simple health check server for hosting platforms (Port 8000)
class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is alive!")
    
    def log_message(self, format, *args):
        # Suppress noisy HTTP access logs if desired
        return

def run_server():
    server = HTTPServer(("0.0.0.0", 8000), HealthCheckHandler)
    server.serve_forever()

app = Client(
    "AutoFilterBot",
    api_id=Config.API_ID,
    api_hash=Config.API_HASH,
    bot_token=Config.BOT_TOKEN,
    plugins=dict(root="plugins")
)

if __name__ == "__main__":
    print("🤖 Advanced Auto-Filter Bot is starting up...")
    # Start the web server in the background so port 8000 passes health checks
    threading.Thread(target=run_server, daemon=True).start()
    app.run()
