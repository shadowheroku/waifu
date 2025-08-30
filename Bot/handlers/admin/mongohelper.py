from pyrogram import filters
from Bot.database.mongohelperdb import rename_anime_names_db, rename_character_names_db
from Bot import app, Command
from Bot.config import OWNERS 

@app.on_message(Command("mongoacap") & filters.user(OWNERS))
async def handle_rename_anime_names(client, message):
    """Command to trigger renaming of all anime names in the database."""
    response = await rename_anime_names_db()
    await message.reply_text(response)

@app.on_message(Command("mongoccap") & filters.user(OWNERS))
async def handle_rename_character_names(client, message):
    """Command to trigger renaming of all character names."""
    response = await rename_character_names_db()
    await message.reply_text(response)

