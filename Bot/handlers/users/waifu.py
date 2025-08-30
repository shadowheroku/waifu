from pyrogram import filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, InputMediaPhoto, InputMediaVideo
from Bot.database.animedb import get_anime_by_first_letter, get_anime_details_by_anime_id
from Bot.database.characterdb import get_top_five_less_smashed_character_by_rarity , get_character_details
from Bot import app , Command
from Bot.utils import command_filter , warned_user_filter
from texts import WAIFU , ANIME

# Define the rarity mapping
RARITY_MAPPING = {
    "1": "Common",
    "2": "Medium",
    "3": "Rare",
    "4": "Legendary",
    "5": "Exclusive",
    "6": "Cosmic",
    "7": "Limited Edition"
}

STYLISH_ALPHABET_MAPPING = {
    "0": "0", "1": "1", "2": "2", "3": "3", "4": "4", "5": "5", "6": "6", "7": "7", "8": "8", "9": "9",
    "ᴀ": "A", "ʙ": "B", "ᴄ": "C", "ᴅ": "D", "ᴇ": "E", "ғ": "F", "ɢ": "G", "ʜ": "H", "ɪ": "I", "ᴊ": "J", 
    "ᴋ": "K", "ʟ": "L", "ᴍ": "M", "ɴ": "N", "ᴏ": "O", "ᴘ": "P", "ǫ": "Q", "ʀ": "R", "s": "S", "ᴛ": "T", 
    "ᴜ": "U", "ᴠ": "V", "ᴡ": "W", "x": "X", "ʏ": "Y", "ᴢ": "Z"
}


# Define the emoji rarity mapping
EMOJI_RARITY_MAPPING = {
    "1": "⚪️ Common",
    "2": "🟢 Medium",
    "3": "🟠 Rare",
    "4": "🟡 Legendary",
    "5": "💮 Exclusive",
    "6": "💠 Cosmic",
    "7": "🔮 Limited Edition"
}


@app.on_message(Command("player") & command_filter)
@warned_user_filter
async def waifu_command(client, message):
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("Sᴇᴀʀᴄʜ Bʏ Rᴀʀɪᴛʏ", callback_data=f"search_rarity_{message.from_user.id}")],
        [InlineKeyboardButton(f"Sᴇᴀʀᴄʜ Bʏ {ANIME}", callback_data=f"search_anime_{message.from_user.id}_0")],  # Start from page 0
        [InlineKeyboardButton("Cʟᴏsᴇ", callback_data=f"close_{message.from_user.id}")]
    ])
    await message.reply(f"Cʜᴏᴏsᴇ ᴀɴ ᴏᴘᴛɪᴏɴ ʙᴇʟᴏᴡ:\n\nsᴇᴀʀᴄʜ ʙʏ ʀᴀʀɪᴛʏ : sᴇᴀʀᴄʜ ғᴏʀ ʟᴇᴀsᴛ Collected {WAIFU}s ʙʏ ᴛʜᴇɪʀ ʀᴀʀɪᴛʏ\n\n sᴇᴀʀᴄʜ ʙʏ {ANIME} : sᴇᴀʀᴄʜ ᴀʟʟ ᴜᴘʟᴏᴀᴅᴇᴅ {WAIFU}s ʙʏ ᴛʜᴇɪʀ {ANIME}", reply_markup=keyboard)

@app.on_callback_query(filters.regex(r"search_rarity_\d+"))
async def search_by_rarity(client, query: CallbackQuery):
    user_id = int(query.data.split("_")[2])
    if query.from_user.id != user_id:
        return  # Ignore if not the user who initiated the command

    # Use emoji rarity names in buttons
    keyboard = InlineKeyboardMarkup(
        [
            [InlineKeyboardButton(EMOJI_RARITY_MAPPING[str(rarity)], callback_data=f"rarity_{rarity}_{user_id}")]
            for rarity in EMOJI_RARITY_MAPPING.keys()
        ] + [
            [InlineKeyboardButton("Cʟᴏsᴇ", callback_data=f"close_{user_id}")]
        ]
    )
    await query.message.edit_text("Cʜᴏᴏsᴇ ᴀ ʀᴀʀɪᴛʏ:", reply_markup=keyboard)

@app.on_callback_query(filters.regex(r"rarity_\d+_\d+"))
async def show_waifus_by_rarity(client, query: CallbackQuery):
    _, rarity, user_id = query.data.split("_")
    user_id = int(user_id)
    if query.from_user.id != user_id:
        return  # Ignore if not the user who initiated the command

    # Convert emoji rarity to original rarity name
    rarity_name = RARITY_MAPPING[rarity]
    top_characters = await get_top_five_less_smashed_character_by_rarity(rarity_name)

    if not top_characters:
        await query.message.edit_text(f"Nᴏ {WAIFU} ғᴏᴜɴᴅ ғᴏʀ ʀᴀʀɪᴛʏ: {rarity_name}")
        return

    # Initialize pagination data
    query_data = {"rarity": rarity_name, "current_index": 0, "user_id": user_id, "total": len(top_characters), "message_id": query.message.id}

    await send_waifu_details(client, query, top_characters, query_data)

async def send_waifu_details(client, query, top_characters, query_data):
    index = query_data["current_index"]
    character = top_characters[index]

    # Fetch character details including image URL
    character_details = await get_character_details(character["id"])
    is_video = character_details.get("is_video", False)
    media_url = character_details.get("video_url" if is_video else "img_url")

    # Construct message
    message_text = (f"💫 **Name :** {character_details['name']}\n"
                    f"**🆔 :** {character_details['id']}\n"
                    f"{character_details['rarity_sign']} **Rarity** : {character_details['rarity']}\n"
                    f"🌍 **Globally {character['unique_user_count']} Users**\n"
                    f"📽️ **Type** : {'Video' if is_video else 'Photo'} {WAIFU}"
                    )

    # Prepare buttons
    buttons = [
        InlineKeyboardButton("⬅", callback_data=f"waifu_prev_{index}_{query_data['rarity']}_{query_data['user_id']}"),
        InlineKeyboardButton("❌", callback_data=f"close_{query_data['user_id']}"),
        InlineKeyboardButton("➡", callback_data=f"waifu_next_{index}_{query_data['rarity']}_{query_data['user_id']}")
    ]

    if index == 0:
        buttons[0] = InlineKeyboardButton("⬅", callback_data="ignore")  # Disable previous button if at the start
    if index == query_data["total"] - 1:
        buttons[2] = InlineKeyboardButton("➡", callback_data="ignore")  # Disable next button if at the end

    keyboard = InlineKeyboardMarkup([buttons])

    try:
        if is_video:
            # For video waifus
            await query.message.edit_media(
                media=InputMediaVideo(
                    media=media_url,
                    caption=message_text
                ),
                reply_markup=keyboard
            )
        else:
            # For photo waifus
            await query.message.edit_media(
                media=InputMediaPhoto(
                    media=media_url,
                    caption=message_text
                ),
                reply_markup=keyboard
            )
    except Exception as e:
        print(f"Error updating media: {e}")
        # Fallback to just updating caption if media update fails
        await query.message.edit_caption(message_text, reply_markup=keyboard)

@app.on_callback_query(filters.regex(r"waifu_(prev|next)_(\d+)_(\w+)_(\d+)"))
async def paginate_waifus(client, query: CallbackQuery):
    action, index, rarity, user_id = query.data.split("_")[1:]
    user_id = int(user_id)
    index = int(index)
    if query.from_user.id != user_id:
        return  # Ignore if not the user who initiated the command

    rarity_name = rarity.capitalize()
    top_characters = await get_top_five_less_smashed_character_by_rarity(rarity_name)

    if action == "prev":
        index -= 1
    elif action == "next":
        index += 1

    query_data = {"rarity": rarity_name, "current_index": index, "user_id": user_id, "total": len(top_characters), "message_id": query.message.id}
    await send_waifu_details(client, query, top_characters, query_data)

@app.on_callback_query(filters.regex(r"search_anime_\d+_\d+"))
async def search_by_anime(client, query: CallbackQuery):
    user_id = int(query.data.split("_")[2])
    current_page = int(query.data.split("_")[3])

    if query.from_user.id != user_id:
        return  # Ignore if not the user who initiated the command

    # Use stylish letters in buttons
    stylish_letters = list(STYLISH_ALPHABET_MAPPING.keys())
    per_page = 15
    total_pages = (len(stylish_letters) + per_page - 1) // per_page
    start_index = current_page * per_page
    end_index = start_index + per_page
    page_buttons = stylish_letters[start_index:end_index]

    buttons = [
        InlineKeyboardButton(stylish_letter, callback_data=f"letter_{STYLISH_ALPHABET_MAPPING[stylish_letter]}_{user_id}_0")
        for stylish_letter in page_buttons
    ]

    # Navigation and close buttons
    navigation_buttons = []
    if current_page > 0:
        navigation_buttons.append(InlineKeyboardButton("⬅️ Pʀᴇᴠɪᴏᴜs", callback_data=f"search_anime_{user_id}_{current_page - 1}"))
    if current_page < total_pages - 1:
        navigation_buttons.append(InlineKeyboardButton("Nᴇxᴛ ➡️", callback_data=f"search_anime_{user_id}_{current_page + 1}"))

    keyboard = InlineKeyboardMarkup([
        buttons[i:i + 3] for i in range(0, len(buttons), 3)
    ] + [navigation_buttons] + [[InlineKeyboardButton("Cʟᴏsᴇ", callback_data=f"close_{user_id}")]])

    await query.message.edit_text(f"Cʜᴏᴏsᴇ ᴀ ʟᴇᴛᴛᴇʀ ᴏғ ᴡʜɪᴄʜ ʏᴏᴜ ᴡᴀɴᴛ ᴛᴏ sᴇᴀʀᴄʜ {ANIME}:", reply_markup=keyboard)

@app.on_callback_query(filters.regex(r"letter_(\w)_(\d+)_(\d+)"))
async def anime_by_letter(client, query: CallbackQuery):
    letter = query.data.split("_")[1]
    user_id = int(query.data.split("_")[2])
    current_page = int(query.data.split("_")[3])

    if query.from_user.id != user_id:
        return  # Ignore if not the user who initiated the command

    anime_list = await get_anime_by_first_letter(letter)
    per_page = 8
    total_pages = (len(anime_list) + per_page - 1) // per_page
    start_index = current_page * per_page
    end_index = start_index + per_page
    anime_page = anime_list[start_index:end_index]

    if not anime_list:
        await query.answer(f"Nᴏ {ANIME} ғᴏᴜɴᴅ sᴛᴀʀᴛɪɴɢ ᴡɪᴛʜ {letter}", show_alert=True)
        return

    buttons = [
        InlineKeyboardButton(anime["name"], callback_data=f"anime_{anime['anime_id']}_{user_id}")
        for anime in anime_page
    ]

    # Always show previous and next buttons at the bottom
    navigation_buttons = []
    if current_page > 0:
        navigation_buttons.append(InlineKeyboardButton("⬅️ Pʀᴇᴠɪᴏᴜs", callback_data=f"letter_{letter}_{user_id}_{current_page - 1}"))
    if current_page < total_pages - 1:
        navigation_buttons.append(InlineKeyboardButton("Nᴇxᴛ ➡️", callback_data=f"letter_{letter}_{user_id}_{current_page + 1}"))

    keyboard = InlineKeyboardMarkup([
        buttons[i:i + 1] for i in range(0, len(buttons), 1)
    ] + [navigation_buttons] + [[InlineKeyboardButton("Bᴀᴄᴋ", callback_data=f"search_anime_{user_id}_0")]])

    await query.message.edit_text(f"Sᴇʟᴇᴄᴛ ᴀɴ {ANIME}:", reply_markup=keyboard)

@app.on_callback_query(filters.regex(r"anime_(\d+)_(\d+)"))
async def anime_details(client, query: CallbackQuery):
    anime_id = int(query.data.split("_")[1])
    user_id = int(query.data.split("_")[2])
    if query.from_user.id != user_id:
        return  # Ignore if not the user who initiated the command

    anime_details = await get_anime_details_by_anime_id(anime_id)
    if not anime_details:
        await query.message.edit_text(f"{ANIME} ᴅᴇᴛᴀɪʟs ɴᴏᴛ ғᴏᴜɴᴅ.")
        return

    message_text = (f"🎌 **{ANIME} Name :** {anime_details['name']}\n"
                    f"**🆔 :** {anime_details['anime_id']}")

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton(f"Sᴇᴀʀᴄʜ {WAIFU}", switch_inline_query_current_chat=f".animelist {anime_details['name']}")],
        [InlineKeyboardButton("Bᴀᴄᴋ", callback_data=f"letter_{anime_details['name'][0].upper()}_{user_id}_0")],
        [InlineKeyboardButton("Cʟᴏsᴇ", callback_data=f"close_{user_id}")]
    ])
    await query.message.edit_text(message_text, reply_markup=keyboard)

@app.on_callback_query(filters.regex(r"close_\d+"))
async def close(client, query: CallbackQuery):
    user_id = int(query.data.split("_")[1])
    if query.from_user.id == user_id:
        await query.message.delete()

@app.on_callback_query(filters.regex(r"ignore"))
async def ignore_callback(client, query: CallbackQuery):
    pass  # Do nothing on 'ignore' callbacks
