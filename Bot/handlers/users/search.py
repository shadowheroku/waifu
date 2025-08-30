from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton 
from Bot import app , Command
from Bot.utils import command_filter , warned_user_filter , sudo_filter
from texts import WAIFU , ANIME

@app.on_message(Command("search") & command_filter)
@warned_user_filter
async def search(client, message):
    keyboard = InlineKeyboardMarkup(
        [
            [InlineKeyboardButton(f"Sᴇᴀʀᴄʜ {WAIFU} 🌃", switch_inline_query_current_chat="")]
        ]
    )
    await message.reply(f"☘️ **Sᴇᴀʀᴄʜ ᴀʟʟ ᴛʜᴇ [{WAIFU}] ᴜᴘʟᴏᴀᴅᴇᴅ ʙʏ ᴄʟɪᴄᴋɪɴɢ ᴛʜᴇ ʙᴜᴛᴛᴏɴ ʙᴇʟᴏᴡ**", reply_markup=keyboard)

@app.on_message(Command("sanime") & sudo_filter)
async def search_anime(client, message):
    keyboard = InlineKeyboardMarkup(
        [
            [InlineKeyboardButton(f"Sᴇᴀʀᴄʜ {ANIME} 🌆", switch_inline_query_current_chat="search.anime ")]
        ]
    )
    await message.reply(f"☘️ **Sᴇᴀʀᴄʜ ᴀʟʟ ᴛʜᴇ [{ANIME}] ɪɴ ᴛʜɪs ʙᴏᴛ ʙʏ ᴄʟɪᴄᴋɪɴɢ ᴛʜᴇ ʙᴜᴛᴛᴏɴ ʙᴇʟᴏᴡ**", reply_markup=keyboard)