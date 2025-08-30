import os
import json
import shutil
from Bot import app
from Bot.config import SUPPORT_CHAT_ID

RESTART_DATA_FILE = "restart_data.json"

def save_restart_data(chat_id, message_id):
    with open(RESTART_DATA_FILE, "w") as f:
        json.dump({"chat_id": chat_id, "message_id": message_id}, f)

def load_restart_data():
    if os.path.exists(RESTART_DATA_FILE):
        with open(RESTART_DATA_FILE, "r") as f:
            return json.load(f)
    return None

def clear_restart_data():
    if os.path.exists(RESTART_DATA_FILE):
        os.remove(RESTART_DATA_FILE)

def edit_restart_message():
    restart_data = load_restart_data()
    if restart_data:
        try:
            chat_id = restart_data["chat_id"]
            message_id = restart_data["message_id"]
            app.edit_message_text(
                chat_id=chat_id,
                message_id=message_id,
                text="**𝖱𝖾𝗌𝗍𝖺𝗋𝗍𝖾𝖽 𝖲𝗎𝖼𝖼𝖾𝗌𝖿𝗎𝗅𝗅𝗒!** ✅"
            )
        except Exception as e:
            print(f"𝖥𝖺𝗂𝗅𝖾𝖽 𝗍𝗈 𝖾𝖽𝗂𝗍 𝗋𝖾𝗌𝗍𝖺𝗋𝗍 𝗆𝖾𝗌𝗌𝖺𝗀𝖾 : {e}")
        finally:
            clear_restart_data()

def clear_downloads_folder():
    downloads_path = "downloads"  
    if os.path.exists(downloads_path):
        try:
            shutil.rmtree(downloads_path)
            os.makedirs(downloads_path) 
            print("Downloads folder cleared successfully.")
        except Exception as e:
            print(f"Failed to clear downloads folder: {e}")

def notify_startup():
    app.send_message(
        chat_id=SUPPORT_CHAT_ID,
        text="**Bot Started Successfully** ✅"
    )

def notify_stop():
    app.send_message(
        chat_id=SUPPORT_CHAT_ID,
        text="**Bot Stopped Successfully** ✅"
    )