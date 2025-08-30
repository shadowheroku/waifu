from pyrogram import Client
from pyrogram.types import Message
from Bot.database.statsdb import get_bot_stats
from Bot import app, Command
from Bot.utils import sudo_filter
from texts import WAIFU , ANIME

@app.on_message(Command("stats") & sudo_filter)
async def handle_stats(client: Client, message: Message):
    # Get the stats from database
    stats = await get_bot_stats()
    
    # Format the stats message
    stats_message = (
        f"📊 **Bot Stats** 📊\n\n"
        f"👥 **Total Groups:** `{stats['group_count']}`\n"
        f"👤 **Total Users:** `{stats['user_count']}`\n"
        f"🎴 **Total {WAIFU}** : `{stats['total_characters']}`\n"
        f"🔢 **Harem Count:** `{stats['harem_count']}`\n"
        f"⚜️ **{WAIFU} Count Sorted By Rarity**\n\n"
    )
    
    # Add rarity counts with signs to the stats message
    for rarity, (sign, count) in stats['rarity_counts'].items():
        stats_message += f"{sign} **{rarity}:** `{count}`\n"
    
    # Send the stats message to the owner
    await message.reply_text(stats_message)

