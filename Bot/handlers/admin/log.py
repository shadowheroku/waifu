from pyrogram import filters
import os
from Bot import app , Command
from Bot.config import OWNERS

LOG_FILE_PATH = "/root/Collect-Cricket-Atheletes/cricket.log"

@app.on_message(Command("logs") & filters.user(OWNERS))
async def send_logs(client, message):
    """Send the log file to the user when /logs is called."""

    # Check if the log file exists in the specified location
    if os.path.exists(LOG_FILE_PATH):
        await message.reply_document(document=LOG_FILE_PATH, caption="Here are the latest logs.")
    else:
        await message.reply_text(f"Log file not found at {LOG_FILE_PATH}!")
