from pyrogram import Client
from pyrogram.types import Message
from Bot import app
from Bot.utils import admin_filter
from Bot.errors import capture_and_handle_error
from Bot import Command

@app.on_message(Command("id") & admin_filter)
@capture_and_handle_error
async def id_command(client: Client, m: Message):
    if m.reply_to_message:
        if m.reply_to_message.sticker:
            id = m.reply_to_message.sticker.file_id
            await m.reply_text(f"Sticker File ID: `{id}`")
            return
        else:
            id = m.reply_to_message.from_user.id
            await m.reply_text(f"Replied User ID: `{id}`")
            return
    else:
        id = m.from_user.id
        await m.reply_text(f"Your ID: `{id}`")
