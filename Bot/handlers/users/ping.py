import time
from pyrogram import Client, filters
from pyrogram.types import Message
from Bot.config import OWNER_ID  # Ensure OWNER_ID is correctly defined
from Bot import app , Command

@app.on_message(Command("ping") & filters.user(OWNER_ID))
async def ping(client: Client, message: Message):
    if message.from_user.id != OWNER_ID:
        await message.reply_text("🚫 This command is restricted to the bot owner.")
        return
    
    start_time = time.time()
    sent_message = await message.reply_text('🏓 Pong!')
    end_time = time.time()
    elapsed_time = round((end_time - start_time) * 1000, 3)
    await sent_message.edit_text(f'🏓 Pong! `{elapsed_time}ms`')

