from pyrogram import filters , Client
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message, CallbackQuery
from Bot.database.animedb import rename_anime_logic, has_permission, list_animes
from Bot import app , Command
from Bot.errors import capture_and_handle_error
from Bot.utils import sudo_filter 
from texts import ANIME

ANIME_LIST_PAGE_SIZE = 10


@app.on_message(Command("team") & filters.private)
@capture_and_handle_error
async def anime_menu(client, message: Message):
    user_id = message.from_user.id
    if not await has_permission(user_id):
        return

    keyboard = [
        [InlineKeyboardButton(f"ʟɪsᴛ {ANIME}", callback_data="list_animes:1")],
        [InlineKeyboardButton(f"ʀᴇnᴀᴍᴇ {ANIME}", callback_data="rename_anime")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await message.reply_text("ᴄʜᴏᴏsᴇ ᴛʜᴇ ᴏᴘᴛɪᴏn ʏᴏᴜ ᴡᴀnᴛ !!:", reply_markup=reply_markup)

@app.on_callback_query(filters.regex(r'^list_animes:(\d+)$'))
@capture_and_handle_error
async def list_animes_callback(client, callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    if not await has_permission(user_id):
        return

    page = int(callback_query.data.split(":")[1])  # Get page number from callback data

    animes, total_animes = await list_animes(page, ANIME_LIST_PAGE_SIZE)

    if not animes:
        await callback_query.edit_message_text(f"ɴᴏ {ANIME}s ғᴏᴜnᴅ.")
        return

    response = f"{ANIME} ʟɪsᴛ (ᴘᴀɢᴇ {page}):"
    for anime in animes:
        response += f"\nID: {anime['anime_id']}, Name: {anime['name']}\n"

    buttons = []
    if page > 1:
        buttons.append(InlineKeyboardButton("ᴘʀᴇᴠɪᴏᴜs", callback_data=f"list_animes:{page-1}"))
    if page * ANIME_LIST_PAGE_SIZE < total_animes:
        buttons.append(InlineKeyboardButton("ɴᴇxᴛ", callback_data=f"list_animes:{page+1}"))
    
    # Add the "Back" button in a new row
    buttons.append(InlineKeyboardButton("ʙᴀᴄᴋ", callback_data="back_to_anime_menu"))

    keyboard = InlineKeyboardMarkup([buttons])
    await callback_query.edit_message_text(response, reply_markup=keyboard)

@app.on_callback_query(filters.regex(r'^back_to_anime_menu$'))
@capture_and_handle_error
async def back_to_anime_menu(client, callback_query: CallbackQuery):
    keyboard = [
        [InlineKeyboardButton(f"ʟɪsᴛ {ANIME}", callback_data="list_animes:1")],
        [InlineKeyboardButton(f"ʀᴇnᴀᴍᴇ {ANIME}", callback_data="rename_anime")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await callback_query.edit_message_text("ᴄʜᴏᴏsᴇ ᴛʜᴇ ᴏᴘᴛɪᴏn ʏᴏᴜ ᴡᴀnᴛ !!:", reply_markup=reply_markup)

@app.on_callback_query(filters.regex(r'^rename_anime$'))
@capture_and_handle_error
async def rename_anime(client, callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    if not await has_permission(user_id):
        await callback_query.message.reply_text("ʏᴏᴜ ᴅᴏ nᴏᴛ ʜᴀᴠᴇ ᴘᴇʀᴍɪssɪᴏn ᴛᴏ ᴘᴇʀғᴏʀᴍ ᴛʜɪs ᴀᴄᴛɪᴏn.")
        return


    try:
        response: Message = await app.ask(user_id, f"ᴘʟᴇᴀsᴇ ᴇnᴛᴇʀ ᴛʜᴇ {ANIME} ɪᴅ ᴀnᴅ nᴇᴡ nᴀᴍᴇ ɪn ᴛʜᴇ ғᴏʀᴍᴀᴛ: {ANIME}_ɪᴅ nᴇᴡ_nᴀᴍᴇ", timeout=60)
        anime_id, new_anime_name = response.text.split(" ", 1)
        anime_id = int(anime_id)

        result_message = await rename_anime_logic(anime_id, new_anime_name)
        await response.reply_text(result_message)
    except ValueError:
        await response.reply_text(f"ɪnᴠᴀʟɪᴅ ғᴏʀᴍᴀᴛ. ᴘʟᴇᴀsᴇ ᴇnᴛᴇʀ ᴛʜᴇ {ANIME} ɪᴅ ᴀnᴅ nᴇᴡ nᴀᴍᴇ ᴄᴏʀʀᴇᴄᴛʟʏ.")
    except Exception as e:
        await callback_query.message.reply_text(f"An error occurred: {str(e)}")


@app.on_message(Command("createteam") & sudo_filter & filters.private)
async def lol(c : Client , m : Message):
    
    btn = InlineKeyboardMarkup([[InlineKeyboardButton(f"ꜱᴇᴀʀᴄʜ {ANIME}", switch_inline_query_current_chat=".anime ")]])
    
    await m.reply_text(f"**ʜᴇʀᴇ ɪꜱ ᴛʜᴇ ʙᴛɴ ᴜꜱᴇ ɪᴛ ᴛᴏ ᴄʀᴇᴀᴛᴇ {ANIME} !!**" , reply_markup=btn)