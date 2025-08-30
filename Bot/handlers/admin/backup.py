import os
import subprocess
import shutil
from pyrogram import Client, filters
from pyrogram.types import Message
from Bot import config
from Bot import app , Command
from pyrogram import Client
from Bot.config import DATABASE_NAME

PATH = f"./backup/{DATABASE_NAME}"

def backup_db(db_name: str, path: str):
    try:
        subprocess.run(
            ["mongodump", "--uri", config.MONGO_URL, "--db", db_name, "--out", path],
            check=True
        )
        shutil.make_archive(path, 'zip', path)
        return f"{path}.zip"
    except subprocess.CalledProcessError as e:
        return f"Backup failed: {str(e)}"

def restore_db(zip_path: str):
    try:
        extract_path = zip_path.replace(".zip", "")
        shutil.unpack_archive(zip_path, extract_path)
        subprocess.run(
            ["mongorestore", "--uri", config.MONGO_URL, extract_path],
            check=True
        )
        return "Restore successful!"
    except (subprocess.CalledProcessError, shutil.ReadError) as e:
        return f"Restore failed: {str(e)}"

async def handle_backup(client: Client, message: Message):
    path = PATH
    db_name = config.DATABASE_NAME  
    zip_path = backup_db(db_name, path)
    if zip_path.endswith(".zip"):
        await client.send_document(chat_id=config.OWNER_ID, document=zip_path)
        shutil.rmtree(path) 
        os.remove(zip_path)  
        response = "Backup successful!"
    else:
        response = zip_path
    await message.reply_text(response)

async def handle_restore(client: Client, message: Message):
    if not message.reply_to_message or not message.reply_to_message.document:
        await message.reply_text("Please reply to a backup zip file to restore.")
        return

    document = message.reply_to_message.document
    file_path = await client.download_media(document.file_id)
    response = restore_db(file_path)
    os.remove(file_path)  
    await message.reply_text(response)

@app.on_message(Command("backup") & filters.user(config.OWNERS))
async def backup_command(client: Client, message: Message):
    await handle_backup(client, message)

@app.on_message(Command("restore") & filters.user(config.OWNERS))
async def restore_command(client: Client, message: Message):
    await handle_restore(client, message)


async def scheduled_backup():
    path = PATH
    db_name = config.DATABASE_NAME
    zip_path = backup_db(db_name, path)
    if zip_path.endswith(".zip"):
        await app.send_document(chat_id=config.LOG_CHANNEL, document=zip_path)
        shutil.rmtree(path)  
        os.remove(zip_path)  


