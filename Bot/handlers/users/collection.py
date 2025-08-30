from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup, InputMediaVideo
from pyrogram.enums import ParseMode
from pyrogram.handlers import CallbackQueryHandler
from Bot import app, Command
from Bot.database.collectiondb import (
    get_collection_details,
    get_collection_image,
    get_user_collection
)
from Bot.database.characterdb import get_character_details
from Bot.database.preferencedb import get_user_preferences
from Bot.utils import command_filter, warned_user_filter
from Bot.errors import capture_and_handle_error
import time
from typing import Dict, Tuple, Any
from texts import WAIFU , ANIME

class AsyncCache:
    def __init__(self, timeout: int = 60):  # 600 seconds = 10 minutes
        self.cache: Dict[int, Tuple[float, Any]] = {}
        self.timeout = timeout
        
    async def get_or_set(self, key: int, getter_func):
        # Clean expired entries
        current_time = time.time()
        self.cache = {k: v for k, v in self.cache.items() 
                     if current_time - v[0] < self.timeout}
        
        # Check if we have a valid cached value
        if key in self.cache:
            timestamp, value = self.cache[key]
            if current_time - timestamp < self.timeout:
                return value
        
        # If not in cache or expired, get new value
        value = await getter_func()
        self.cache[key] = (current_time, value)
        return value

# Initialize cache
collection_cache = AsyncCache(timeout=10)  # 10 minutes timeout

async def get_user_collection_data(user_id: int, include_videos: bool = False):
    """Get user collection and preferences"""
    user_collection = await get_user_collection(user_id)
    user_preferences = await get_user_preferences(user_id)
    
    # Filter collection based on video status
    if user_collection and "images" in user_collection:
        filtered_images = []
        for img in user_collection["images"]:
            char_details = await get_character_details(img["image_id"])
            if char_details:
                is_video = char_details.get("is_video", False)
                if include_videos == is_video:  # Only include videos in video collection and vice versa
                    filtered_images.append(img)
        user_collection["images"] = filtered_images
    
    return user_collection, user_preferences

@app.on_message(Command(["harem", "mycollection"]) & command_filter)
@warned_user_filter
@capture_and_handle_error
async def smashes(client: Client, message: Message):
    user_id = message.from_user.id
    await send_collection_page(client, message, user_id, 1, new_message=True)

@capture_and_handle_error
async def send_collection_page(client: Client, message: Message, user_id: int, page_number: int, new_message: bool):
    # Get cached collection and preferences using the async cache
    user_collection, user_preferences = await collection_cache.get_or_set(
        user_id,
        lambda: get_user_collection_data(user_id)
    )

    # Check if user has any characters
    if not user_collection or not user_collection.get("images"):
        await message.reply(f"**ʏᴏᴜ ʜᴀᴠᴇɴ'ᴛ ᴄᴏʟʟᴇᴄᴛᴇᴅ ᴀɴʏ {WAIFU} ʏᴇᴛ.**")
        return

    # Get collection details
    result = await get_collection_details(user_collection, user_preferences)
    if not result:
        return

    sorted_images, characters_details, anime_character_count, anime_total_characters = result


    # Calculate pagination
    ITEMS_PER_PAGE = 10 if user_preferences.get("detailed") == "enable" else 5
    total_pages = max(1, (len(sorted_images) - 1) // ITEMS_PER_PAGE + 1)
    page_number = min(max(1, page_number), total_pages)
    start_index = (page_number - 1) * ITEMS_PER_PAGE
    end_index = min(start_index + ITEMS_PER_PAGE, len(sorted_images))
    current_page_images = sorted_images[start_index:end_index]

    # Generate response text based on display mode
    if user_preferences.get("detailed") == "enable":
        # Sort by anime for detailed view
        current_page_images = sorted(
            current_page_images, 
            key=lambda img: (
                characters_details.get(img["image_id"], {}).get("anime", "").lower(), 
                img["image_id"]
            )
        )
        
        response_text = f"<b>{message.from_user.first_name}'s ᴅᴇᴛᴀɪʟᴇᴅ ᴄᴏʟʟᴇᴄᴛɪᴏn (ᴘᴀɢᴇ {page_number} ᴏғ {total_pages}):</b>\n\n"
        
        current_anime = None
        for image in current_page_images:
            character = characters_details.get(image["image_id"])
            if not character:
                continue
                
            anime_name = character.get('anime', 'Unknown')
            if anime_name != current_anime:
                if current_anime is not None:
                    response_text += "\n"
                response_text += f"🤝 <b>{anime_name}</b>\n"
                current_anime = anime_name

            response_text += (
                f"{character.get('rarity_sign', '❓')} ({character['id']}) {character.get('name', 'Unknown')} [x{image['count']}]\n"
            )
    else:
        # Standard view
        response_text = f"<b>{message.from_user.first_name}'s ᴄᴏʟʟᴇᴄᴛɪᴏn (ᴘᴀɢᴇ {page_number} ᴏғ {total_pages}):</b>\n\n"

        for image in current_page_images:
            character = characters_details.get(image["image_id"])
            if not character:
                continue
                
            anime_id = character.get("anime_id", "")
            user_anime_count = anime_character_count.get(anime_id, 0)
            total_anime_count = anime_total_characters.get(anime_id, 0)
            
            response_text += (
                f"👤<b>{character.get('name', 'Unknown')} [x{image['count']}]</b>\n"
                f"<i>{character.get('rarity_sign', '❓')} | {character.get('rarity', 'Unknown')}</i>\n"
                f"<b>🤝 {character.get('anime', 'Unknown')} ({user_anime_count}/{total_anime_count})</b>\n\n"
            )

    # Get image URL for display
    img_url = await get_collection_image(user_collection, user_id)

    # Create pagination buttons with horizontal layout
    total_unique_characters = len(user_collection["images"])
    buttons = [
        [InlineKeyboardButton(
            f"📜 ᴄᴏʟʟᴇᴄᴛᴇᴅ  ({total_unique_characters})", 
            switch_inline_query_current_chat=f"collected.{user_id}"
        )]
    ]
    
    # Add navigation buttons horizontally
    nav_buttons = []
    if page_number > 1:
        nav_buttons.append(InlineKeyboardButton("⬅️ ᴘʀᴇᴠɪᴏᴜs", callback_data=f"page_{user_id}_{page_number-1}"))
    if page_number < total_pages:
        nav_buttons.append(InlineKeyboardButton("ɴᴇxᴛ ➡️", callback_data=f"page_{user_id}_{page_number+1}"))
    
    if nav_buttons:
        buttons.append(nav_buttons)

    reply_markup = InlineKeyboardMarkup(buttons)

    try:
        # Send or edit message based on whether we have an image and if it's a new message
        if img_url:
            if new_message:
                await client.send_photo(
                    chat_id=message.chat.id,
                    photo=img_url,
                    caption=response_text,
                    parse_mode=ParseMode.HTML,
                    reply_markup=reply_markup,
                    reply_to_message_id=message.id
                )
            else:
                await client.edit_message_caption(
                    chat_id=message.chat.id,
                    message_id=message.id,
                    caption=response_text,
                    parse_mode=ParseMode.HTML,
                    reply_markup=reply_markup
                )
        else:
            if new_message:
                await message.reply(
                    response_text, 
                    reply_markup=reply_markup,
                    parse_mode=ParseMode.HTML
                )
            else:
                await client.edit_message_text(
                    chat_id=message.chat.id,
                    message_id=message.id,
                    text=response_text,
                    parse_mode=ParseMode.HTML,
                    reply_markup=reply_markup
                )
    except Exception as e:
        print(f"Error sending collection page: {e}")
        if new_message:
            await message.reply(f"Error displaying collection: {str(e)}")

@capture_and_handle_error
async def paginate_collection(client: Client, callback_query):
    """
    Handle pagination callbacks for collection pages.
    
    Args:
        client: The Pyrogram client
        callback_query: The callback query to handle
    """
    # Parse callback data
    try:
        user_id, page_number = map(int, callback_query.data.split("_")[1:])
    except (ValueError, IndexError) as e:
        print(f"Error parsing callback data: {e}")
        await callback_query.answer("Invalid callback data")
        return

    # Verify user identity
    if callback_query.from_user.id != user_id:
        await callback_query.answer("🚫 ᴀᴄᴄᴇss ᴅᴇnɪᴇᴅ: ᴛʜɪs ɪsn'ᴛ ʏᴏᴜʀ ᴄᴏʟʟᴇᴄᴛɪᴏn.", show_alert=True)
        return

    # Set up message for pagination
    message = callback_query.message
    message.from_user = callback_query.from_user  # Set the correct user for the message
    
    # Display the requested page
    await send_collection_page(client, message, user_id, page_number, new_message=False)
    await callback_query.answer()

# Register the handler
app.add_handler(CallbackQueryHandler(paginate_collection, filters.regex(r"^page_(\d+)_(\d+)$")))

@app.on_message(Command(["myvidcollection", "vidharem"]) & command_filter)
@warned_user_filter
@capture_and_handle_error
async def video_collection(client: Client, message: Message):
    user_id = message.from_user.id
    await send_video_collection_page(client, message, user_id, 1, new_message=True)

async def send_video_collection_page(client: Client, message: Message, user_id: int, page_number: int, new_message: bool):
    # Get video collection
    user_collection, _ = await get_user_collection_data(user_id, include_videos=True)

    # Check if user has any video characters
    if not user_collection or not user_collection.get("images"):
        if new_message:
            await message.reply(f"**ʏᴏᴜ ʜᴀᴠᴇɴ'ᴛ ᴄᴏʟʟᴇᴄᴛᴇᴅ ᴀɴʏ ᴠɪᴅᴇᴏ {WAIFU} ʏᴇᴛ.**")
        return

    # Calculate pagination
    total_videos = len(user_collection["images"])
    total_pages = total_videos  # One video per page
    page_number = min(max(1, page_number), total_pages)
    current_video = user_collection["images"][page_number - 1]

    # Get video details
    video_char = await get_character_details(current_video["image_id"])
    if not video_char:
        await message.reply(f"Error: Could not find video {WAIFU} details.")
        return

    # Create caption
    caption = (
        f"<b>{message.from_user.first_name}'s ᴠɪᴅᴇᴏ {WAIFU} ᴄᴏʟʟᴇᴄᴛɪᴏɴ</b>\n"
        f"<b>ᴘᴀɢᴇ {page_number} ᴏғ {total_pages}</b>\n\n"
        f"👤 <b>Name</b>: {video_char['name']}\n"
        f"{video_char.get('rarity_sign', '❓')} <b>Rarity</b>: {video_char.get('rarity', 'Unknown')}\n"
        f"🤝 <b>{ANIME}</b>: {video_char.get('anime', 'Unknown')}\n"
        f"🆔 <b>ID</b>: {video_char['id']}\n"
        f"📥 <b>Count</b>: x{current_video['count']}"
    )

    # Create navigation buttons
    buttons = []
    nav_buttons = []
    
    if page_number > 1:
        nav_buttons.append(
            InlineKeyboardButton("⬅️ ᴘʀᴇᴠɪᴏᴜs", callback_data=f"vidpage_{user_id}_{page_number-1}")
        )
    
    nav_buttons.append(
        InlineKeyboardButton("❌ ᴄʟᴏsᴇ", callback_data=f"close_vid_{user_id}")
    )
    
    if page_number < total_pages:
        nav_buttons.append(
            InlineKeyboardButton("ɴᴇxᴛ ➡️", callback_data=f"vidpage_{user_id}_{page_number+1}")
        )
    
    buttons.append(nav_buttons)
    reply_markup = InlineKeyboardMarkup(buttons)

    try:
        if new_message:
            await client.send_video(
                chat_id=message.chat.id,
                video=video_char.get("video_url"),  # Using img_url as it contains the video URL for video waifus
                caption=caption,
                parse_mode=ParseMode.HTML,
                reply_markup=reply_markup
            )
        else:
            await client.edit_message_media(
                chat_id=message.chat.id,
                message_id=message.id,
                media=InputMediaVideo(
                    media=video_char.get("video_url"),
                    caption=caption,
                    parse_mode=ParseMode.HTML
                ),
                reply_markup=reply_markup
            )
    except Exception as e:
        print(f"Error sending video collection page: {e}")
        if new_message:
            await message.reply(f"Error displaying video collection: {str(e)}")

@app.on_callback_query(filters.regex(r"^vidpage_(\d+)_(\d+)$"))
@capture_and_handle_error
async def paginate_video_collection(client: Client, callback_query):
    try:
        user_id, page_number = map(int, callback_query.data.split("_")[1:])
    except (ValueError, IndexError) as e:
        print(f"Error parsing callback data: {e}")
        await callback_query.answer("Invalid callback data")
        return

    if callback_query.from_user.id != user_id:
        await callback_query.answer("🚫 ᴀᴄᴄᴇss ᴅᴇɴɪᴇᴅ: ᴛʜɪs ɪsɴ'ᴛ ʏᴏᴜʀ ᴄᴏʟʟᴇᴄᴛɪᴏɴ.", show_alert=True)
        return

    message = callback_query.message
    message.from_user = callback_query.from_user
    
    await send_video_collection_page(client, message, user_id, page_number, new_message=False)
    await callback_query.answer()

@app.on_callback_query(filters.regex(r"^close_vid_(\d+)$"))
@capture_and_handle_error
async def close_video_collection(client: Client, callback_query):
    user_id = int(callback_query.data.split("_")[2])
    
    if callback_query.from_user.id != user_id:
        await callback_query.answer("🚫 ᴀᴄᴄᴇss ᴅᴇɴɪᴇᴅ: ᴛʜɪs ɪsɴ'ᴛ ʏᴏᴜʀ ᴄᴏʟʟᴇᴄᴛɪᴏɴ.", show_alert=True)
        return
        
    await callback_query.message.delete()
    await callback_query.answer()


