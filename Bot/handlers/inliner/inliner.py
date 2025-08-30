import re
from pyrogram import Client, filters
from pyrogram.types import (
    InlineQueryResultPhoto,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from pyrogram.types import InlineQueryResultArticle, InputTextMessageContent
from pyrogram.types import CallbackQuery
from pyrogram.enums import ParseMode
from Bot.database.iddb import get_next_anime_id
from Bot.database.preferencedb import get_icaption_preference
from Bot.database.characterdb import get_character_details , total_character_in_anime , get_character_by_anime , get_character , get_total_uploaded_characters
from Bot.database.collectiondb import get_user_collection
import uuid
from Bot.config import OWNER_ID
from Bot.database.privacydb import is_user_sudo
from Bot import app
from Bot.errors import capture_and_handle_error
from Bot.database.animedb import *
from texts import WAIFU , ANIME


async def fetch_user_name(client, user_id):
    user = await client.get_users(user_id)
    return f"{user.first_name}"

@capture_and_handle_error
async def handle_search_anime(client, query, results):
    anime_name = query.split("search.anime ", 1)[1]
    animes = await get_anime(anime_name)

    for anime in animes:
        character_count = await total_character_in_anime(anime["anime_id"])

        caption = (
            f"✨ **{ANIME}**: **{anime['name']}**\n"
            f"🆔 **ID**: **{anime['anime_id']}**\n\n"
            f"**Characters uploaded:** {character_count}"
        )

        result = InlineQueryResultArticle(
            id=str(anime["anime_id"]),
            title=anime["name"],
            input_message_content=InputTextMessageContent(
                message_text=caption,
                parse_mode=ParseMode.MARKDOWN
            )
        )
        results.append(result)

@capture_and_handle_error
async def handle_anime_query(client, query, results):
    anime_name = query.split(".anime ", 1)[1]
    animes = await get_anime(anime_name)

    if animes:
        for anime in animes:
            caption = (
                f"✨ **{ANIME}**: **{anime['name']}**\n"
                f"🆔 **ID**: **{anime['anime_id']}**"
            )
            result = InlineQueryResultArticle(
                id=str(anime["anime_id"]),
                title=anime["name"],
                input_message_content=InputTextMessageContent(
                    message_text=caption,
                    parse_mode=ParseMode.MARKDOWN
                )
            )
            results.append(result)
    else:
        caption = f"ɴᴏ {ANIME} ғᴏᴜɴᴅ ᴡɪᴛʜ ᴛʜᴇ nᴀᴍᴇ '{anime_name}'. ᴄʟɪᴄᴋ ʙᴇʟᴏᴡ ᴛᴏ ᴄʀᴇᴀᴛᴇ ɪᴛ."
        create_anime_caption = f"{ANIME} '{anime_name}' has been created successfully."

        anime_creation_id = str(uuid.uuid4())

        await temp_anime_creation(anime_creation_id , anime_name)

        result = InlineQueryResultArticle(
            id="create_anime",
            title=f"Create {ANIME}: {anime_name}",
            input_message_content=InputTextMessageContent(
                message_text=caption,
                parse_mode=ParseMode.MARKDOWN
            ),
            description=f"ᴄʟɪᴄᴋ ʜᴇʀᴇ ᴛᴏ ᴄʀᴇᴀᴛᴇ ᴀ ɴᴇᴡ {ANIME}",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton(f"ᴄʀᴇᴀᴛᴇ {ANIME}", callback_data=f"create_anime:{anime_creation_id}")
            ]])
        )
        results.append(result)

@capture_and_handle_error
async def create_anime_callback(client: Client, callback_query: CallbackQuery):
    user_id = callback_query.from_user.id

    # Check if the user is the owner or has sudo privileges
    if user_id != OWNER_ID and not await is_user_sudo(user_id):
        await callback_query.answer("ʏᴏᴜ ᴅᴏ nᴏᴛ ʜᴀᴠᴇ ᴘᴇʀᴍɪssɪᴏn ᴛᴏ ᴘᴇʀғᴏʀᴍ ᴛʜɪs ᴀᴄᴛɪᴏn.")
        return

    creation_id = callback_query.data.split(":")[1]

    # Retrieve the anime name using the creation ID
    anime_creation = await find_temp_anime_creation(creation_id)
    if not anime_creation:
        await callback_query.answer("ғᴀɪʟᴇᴅ ᴛᴏ ʀᴇᴛʀɪᴇᴠᴇ ᴛʜᴇ ᴛᴇᴀᴍ nᴀᴍᴇ.")
        return

    anime_name = anime_creation["anime_name"]

    # Check if the anime already exists
    existing_anime = await get_anime(anime_name)
    if existing_anime:
        await callback_query.answer(f"{ANIME} '{anime_name}' ᴀʟʀᴇᴀᴅʏ ᴇxɪsᴛs ᴡɪᴛʜ ɪᴅ {existing_anime['anime_id']}.")
        return

    # Create the new anime
    anime_id = await get_next_anime_id()
    await create_anime(anime_id , anime_name)
    
    await callback_query.answer(f"{ANIME} '{anime_name}' ʜᴀs ʙᴇᴇn ᴄʀᴇᴀᴛᴇᴅ sᴜᴄᴄᴇssғᴜʟʟʏ ᴡɪᴛʜ ɪᴅ {anime_id}.")
    await callback_query.edit_message_text(
        f"{ANIME} '{anime_name}' ʜᴀs ʙᴇᴇn ᴄʀᴇᴀᴛᴇᴅ sᴜᴄᴄᴇssғᴜʟʟʏ ᴡɪᴛʜ ɪᴅ {anime_id}.",
        parse_mode=ParseMode.HTML
    )

    # Remove the temporary anime creation record
    await delete_temp_anime_creation(creation_id)

@capture_and_handle_error
async def handle_animelist_query(client, query, results):
    # Extract the anime name from the query
    anime_name = query.split(".animelist ", 1)[1].strip()

    # Search for characters where the anime name matches exactly
    characters = await get_character_by_anime(anime_name)

    # Filter out video waifus
    characters = [char for char in characters if not char.get("is_video", False)]

    # Handle the case when no characters are found for the given anime
    if not characters:
        result = InlineQueryResultArticle(
            id="no_results",
            title=f"No {WAIFU} Found",
            input_message_content=InputTextMessageContent(
                message_text=f"No {WAIFU} found for anime '{anime_name}'.",
                parse_mode=ParseMode.MARKDOWN
            )
        )
        results.append(result)
        return

    # Pagination and result limit handling
    paginated_characters = characters[:10]  # Adjust result limit for pagination if needed

    # Loop through the characters and prepare the results
    for character in paginated_characters:
        # Event-related details
        event_sign = character.get("event_sign", "")
        event = character.get("event", "")
        event_line = f"\n{event_sign} <i>{event}</i> {event_sign}" if event_sign and event else ""

        event_sign_display = f"[{event_sign}]" if event_sign else ""

        caption = (
            f"👤 <b>Name</b><b>:</b> <i><b>{character['name']} {event_sign_display}</b></i>\n"
            f"{character['rarity_sign']} <b>Rarity</b><b>:</b> <i><b>{character['rarity']}</b></i>\n"
            f"🤝 <b>{ANIME}</b><b>:</b> <i><b>{character['anime']}</b></i>\n\n"
            f"🆔<b>:</b> <b>{character['id']}</b>"
            f"<i><b>{event_line}</b></i>"
        )

        result = InlineQueryResultPhoto(
            id=str(character["id"]),
            photo_url=character["img_url"],
            thumb_url=character["img_url"],
            caption=caption
        )
        results.append(result)

@capture_and_handle_error
async def handle_inline_query(client: Client, inline_query):
    query = inline_query.query
    results = []
    
    # Pagination parameters
    next_offset = inline_query.offset or "0"
    result_limit = 10
    offset = int(next_offset)

    is_gallery = True

    if query.startswith("collected."):
        parts = query.split(" ", 1)
        try:
            owner_user_id = int(parts[0].split(".")[1])
            search_term = parts[1] if len(parts) > 1 else ""
        except (IndexError, ValueError):
            owner_user_id = None
            search_term = ""

        if owner_user_id is not None:
            user_collection = await get_user_collection(owner_user_id)

            if user_collection and user_collection.get("images"):
                user_name = await fetch_user_name(client, user_collection["user_id"])
                user_id = user_collection["user_id"]
                icaption_preference = await get_icaption_preference(user_id)

                anime_character_count = {}
                for image in user_collection["images"]:
                    character = await get_character_details(image["image_id"])
                    if character and not character.get("is_video", False):  # Skip video waifus
                        anime_id = character["anime_id"]
                        if anime_id not in anime_character_count:
                            anime_character_count[anime_id] = 0
                        anime_character_count[anime_id] += 1

                matching_images = []
                for image in user_collection["images"]:
                    character = await get_character_details(image["image_id"])
                    if character and not character.get("is_video", False):  # Skip video waifus
                        if search_term.isdigit() and character["id"] == int(search_term):
                            matching_images.append(image)
                        elif re.search(search_term, character["name"], re.IGNORECASE):
                            matching_images.append(image)

                paginated_images = matching_images[offset:offset + result_limit]

                for image in paginated_images:
                    character = await get_character_details(image["image_id"])
                    if character:
                        total_uploaded_characters = await total_character_in_anime(character["anime_id"])
                        user_character_count = anime_character_count[character["anime_id"]]

                        # Event-related details
                        event_sign = character.get("event_sign", "")
                        event = character.get("event", "")
                        event_line = f"\n{event_sign} <i>{event}</i> {event_sign}" if event_sign and event else ""
                        event_sign_display = f"[{event_sign}]" if event_sign else ""

                        if icaption_preference == "Caption 1":
                            caption = (
                                f"<b>{user_name}'s {character['rarity']} Collect</b>\n\n"
                                f"<b>👤Name</b> <b>≿ <i>{character['name']}</i> {event_sign_display} (x{image['count']})</b>\n"
                                f"<b>🤝{ANIME}</b> <b>⊱ <i>{character['anime']}</i> ({user_character_count}/{total_uploaded_characters})</b>\n"
                                f"<b>{character['rarity_sign']}Rarity:</b> <b> <i>{character['rarity']}</i> </b>\n\n"
                                f"<b>🔖ID </b> <b>≼ {character['id']} ≽</b>"
                                f"<b><i>{event_line}</i></b>"
                            )
                        else:
                            caption = (
                                f"🫧<b>Check out {user_name}'s Collect!</b>🫧\n\n"
                                f"➤ 🧩 <b>{character['name']} {event_sign_display}</b>  <b>x{image['count']}</b> | <b>{character['anime']}</b> ({user_character_count}/{total_uploaded_characters})\n"
                                f"➤ {character['rarity_sign']} <b><i>({character['rarity']})</i></b> | 🔖 <b>{character['id']}</b> \n"
                                f"<b>{event_line}</b>"
                            )
                        result = InlineQueryResultPhoto(
                            id=str(character["id"]),
                            photo_url=character["img_url"],
                            thumb_url=character["img_url"],
                            caption=caption
                        )
                        results.append(result)

    elif query.startswith(".anime "):
        await handle_anime_query(client, query, results)
        is_gallery = False  # Set to False for these queries
    elif query.startswith("search.anime "):
        await handle_search_anime(client, query, results)
        is_gallery = False  # Set to False for these queries
    elif query.startswith(".animelist "):  # Check if query starts with .animelist
        await handle_animelist_query(client, query, results)
        is_gallery = True  # Ensure gallery mode for these queries
    else:
        characters = []
        if query.isdigit() or re.match(r"^\d+$", query):
            characters = await get_character(query)
        else:
            characters = await search_character(query)
    
        # Filter out video waifus
        characters = [char for char in characters if not char.get("is_video", False)]
        paginated_characters = characters[offset:offset + result_limit]

        for character in paginated_characters:
            # Event-related details
            event_sign = character.get("event_sign", "")
            event = character.get("event", "")
            event_line = f"\n{event_sign} <i>{event}</i> {event_sign}" if event_sign and event else ""
    
            event_sign_display = f"[{event_sign}]" if event_sign else ""
    
            caption = (
                f"👤 <b>Name</b><b>:</b> <i><b>{character['name']} {event_sign_display}</b></i>\n"
                f"{character['rarity_sign']} <b>Rarity</b><b>:</b> <i><b>{character['rarity']}</b></i>\n"
                f"🤝 <b>{ANIME}</b><b>:</b> <i><b>{character['anime']}</b></i>\n\n"
                f"🆔<b>:</b> <b>{character['id']}</b>"
                f"<i><b>{event_line}</b></i>"
            )

            result = InlineQueryResultPhoto(
                id=str(character["id"]),
                photo_url=character["img_url"],
                thumb_url=character["img_url"],
                caption=caption
            )
            results.append(result)
    
    # Check if there's a next page
    if len(results) == result_limit:
        next_offset = str(offset + result_limit)
    else:
        next_offset = ""
        
    x = await get_total_uploaded_characters()
    
    await client.answer_inline_query(inline_query.id, results, cache_time=1, next_offset=next_offset, is_gallery=is_gallery , 
                                     switch_pm_text=f"Total Characters: {x}" , switch_pm_parameter="total_characters")
    

@app.on_inline_query()
@capture_and_handle_error
async def inline_query_handler(client, inline_query):
    await handle_inline_query(client, inline_query)


@app.on_callback_query(filters.regex('^create_anime:'))
@capture_and_handle_error
async def create_anime_callback_handler(client, callback_query):
    await create_anime_callback(client, callback_query)







