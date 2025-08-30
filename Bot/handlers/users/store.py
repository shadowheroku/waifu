from datetime import datetime, timedelta
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, Message, InputMediaVideo
import random
from Bot import app , Command
from Bot.database.characterdb import get_all_images, get_character_details
from Bot.database.grabtokendb import get_user_balance, decrease_grab_token
from Bot.database.smashdb import update_smashed_image, get_global_smash_count
from Bot.database.storedb import get_user_store, update_user_store, get_purchase_record, add_purchase_record
from Bot import PRICE_MAPPING
from texts import WAIFU , ANIME

# Local cache for free refresh tracking
FREE_REFRESH_CACHE = {}
GRAB_TOKEN_COST = 50000
RARITY_TO_PRICE = {v["name"]: int(v["price"]) for v in PRICE_MAPPING.values()}
STORE = "https://files.catbox.moe/ho85s1.jpg"


async def create_new_store(user_id):
    """Generate a new store with 10 random characters and save it in the database."""
    all_characters = await get_all_images()
    
    # Filter out video waifus
    non_video_characters = [char for char in all_characters if not char.get("is_video", False)]
    
    if len(non_video_characters) < 10:
        raise ValueError("Not enough non-video characters in the database to create a store.")

    # Choose 10 random characters from non-video characters
    selected_characters = random.sample(non_video_characters, 10)
    player_ids = [character["id"] for character in selected_characters]

    # Save the new store to the database
    await update_user_store(user_id, player_ids)

    return player_ids


# Command: /mystore
@app.on_message(Command("mystore") & filters.private)
async def my_store(client: Client, message: Message):
    user_id = message.from_user.id
    x = await message.reply_text("**Please Wait And Let Me Fetch Today's Store For You....**")

    # Check if the user has a store saved
    user_store = await get_user_store(user_id)
    current_time = datetime.utcnow()

    if user_store:
        stored_time = user_store["stored_at"]
        if (current_time - stored_time) < timedelta(hours=24):
            # Retrieve existing store
            player_ids = user_store["player_ids"]
        else:
            # Update with a new store after 24 hours
            player_ids = await create_new_store(user_id)
    else:
        # Create a new store for first-time users
        player_ids = await create_new_store(user_id)

    # Retrieve character details for the store
    characters = [await get_character_details(player_id) for player_id in player_ids]

    # Create the store message
    store_message = "**This Is Your Today's Store:**\n\n"
    for character in characters:
        rarity = character['rarity']
        price = RARITY_TO_PRICE.get(rarity, 0)  # Use 0 as fallback if rarity is unknown
        store_message += (
            f"{character['rarity_sign']} {character['id']} **{character['name']}**\n"
            f"Rarity: {rarity} | Price: {price} Grab Tokens\n\n"
        )
    store_message += "\n> You are entitled to 1 free store refresh per day."
    store_message += "\n> Once the free refresh limit is exceeded, subsequent refreshes will incur a charge of 25,000 Grab Tokens."

    # Inline buttons for refreshing and buying
    store_buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton("🛒 Buy", callback_data=f"xbuy_player_{user_id}")]
    ])
    await x.delete()
    await message.reply_photo(STORE ,caption= store_message, reply_markup=store_buttons, quote=True)


@app.on_callback_query(filters.regex(r"xbuy_player_(\d+)"))
async def buy_player(client: Client, callback_query: CallbackQuery):
    user_id = int(callback_query.matches[0].group(1))
    if callback_query.from_user.id != user_id:
        await callback_query.answer("This is not your store!", show_alert=True)
        return

    await callback_query.answer()
    msg = await client.ask(
        callback_query.message.chat.id,
        f"**Please enter the ID of the {WAIFU} you want to buy:**",
        timeout=60
    )

    player_id = msg.text.strip()

    user_store = await get_user_store(user_id)
    if not user_store or player_id not in user_store["player_ids"]:
        await callback_query.message.reply_text(f"**The {WAIFU} ID you entered is not in your today's store!**")
        return

    character = await get_character_details(player_id)
    price = RARITY_TO_PRICE.get(character["rarity"], 0)
    img_url = character['img_url']

    confirmation_buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton("Yes", callback_data=f"ce_{user_id}_{player_id}_{price}")],
        [InlineKeyboardButton("No", callback_data="cancel_purchase")]
    ])

    await client.send_photo(
        chat_id=callback_query.message.chat.id,
        photo=img_url,
        caption=(
            f"**Do You Really Want To Purchase?**\n\n"
            f"**Name: **{character['name']}\n"
            f"**{character['rarity_sign']} Rarity:** {character['rarity']}\n"
            f"**Price:** {price} Grab Tokens"
        ),
        reply_markup=confirmation_buttons
    )
    await callback_query.message.delete()

@app.on_callback_query(filters.regex(r"ce_(\d+)_(\d+)_(\d+)"))
async def confirm_purchase(client: Client, callback_query: CallbackQuery):
    # Parse callback data: user_id, player_id, and price
    user_id, player_id, price = map(int, callback_query.data.split("_")[1:])

    # Format today's date as a string (e.g., "2025-02-10")
    today_str = datetime.utcnow().strftime("%Y-%m-%d")

    # Check if this user has already purchased this player today
    purchase_record = await get_purchase_record(user_id, today_str)
    if purchase_record and player_id in purchase_record.get("player_ids", []):
        await callback_query.answer(f"You have already purchased this {WAIFU} today!", show_alert=True)
        return

    # Check user balance
    user_balance = await get_user_balance(user_id)
    if user_balance < price:
        await callback_query.answer("You don't have enough grab tokens to make this purchase!", show_alert=True)
        return

    # Deduct tokens and update user collection
    await decrease_grab_token(user_id, price)
    await update_smashed_image(user_id, str(player_id))

    # Record the purchase
    await add_purchase_record(user_id, today_str, player_id)

    # Notify the user and clean up the callback
    await callback_query.message.reply_text(
        f"Congratulations! You have successfully purchased the {WAIFU} with ID **{player_id}**."
    )
    await callback_query.answer()
    await callback_query.message.delete()


@app.on_callback_query(filters.regex(r"cancel_purchase"))
async def cancel_purchase(client: Client, callback_query: CallbackQuery):
    await callback_query.answer("Purchase canceled!", show_alert=True)
    await callback_query.message.edit_text("The purchase process has been canceled.")
    
    
@app.on_message(Command("mystore") & filters.group)
async def my_store(client: Client, message: Message):
    user_id = message.from_user.id
    x = await message.reply_text("**Please Wait And Let Me Fetch Today's Store For You....**")

    # Check if the user has a store saved
    user_store = await get_user_store(user_id)
    current_time = datetime.utcnow()

    if user_store:
        stored_time = user_store["stored_at"]
        if (current_time - stored_time) < timedelta(hours=24):
            # Retrieve existing store
            player_ids = user_store["player_ids"]
        else:
            # Update with a new store after 24 hours
            player_ids = await create_new_store(user_id)
    else:
        # Create a new store for first-time users
        player_ids = await create_new_store(user_id)

    # Retrieve character details for the store
    characters = [await get_character_details(player_id) for player_id in player_ids]

    # Create the store message
    store_message = "**This Is Your Today's Store:**\n\n"
    for character in characters:
        rarity = character['rarity']
        price = RARITY_TO_PRICE.get(rarity, 0)  # Use 0 as fallback if rarity is unknown
        store_message += (
            f"{character['rarity_sign']} {character['id']} **{character['name']}**\n"
            f"Rarity: {rarity} | Price: {price} Grab Tokens\n\n"
        )
    store_message += "\n> To Purchase From Store You Need To Go To Bot's PM."

    await x.delete()
    await message.reply_photo(STORE ,caption= store_message, quote=True)

@app.on_message(Command(["videolist", "videos"]) & filters.private)
async def list_video_waifus(client: Client, message: Message):
    user_id = message.from_user.id
    
    # Get all characters
    all_characters = await get_all_images()
    
    # Filter video waifus
    video_characters = [char for char in all_characters if char.get("is_video", False)]
    
    if not video_characters:
        await message.reply(f"**No video {WAIFU}s found in the database.**")
        return
        
    # Sort by ID for consistent ordering
    video_characters.sort(key=lambda x: x["id"])
    
    # Initialize pagination
    items_per_page = 1
    total_pages = len(video_characters)
    
    # Function to generate message for a video character
    async def get_video_details(character):
        char_details = await get_character_details(character["id"])
        global_count, unique_users = await get_global_smash_count(character["id"])
        
        return (
            f"**💫 Name:** {char_details['name']}\n"
            f"**🆔 ID:** `{char_details['id']}`\n"
            f"{char_details['rarity_sign']} **Rarity:** {char_details['rarity']}\n"
            f"**🤝 {ANIME}:** {char_details['anime']}\n"
            f"**📊 Stats:**\n"
            f"- Global Count: {global_count}\n"
            f"- Unique Owners: {unique_users}\n"
            f"**📽️ Type:** Video {WAIFU}"
        )
    
    async def show_page(page_num):
        character = video_characters[page_num - 1]
        char_details = await get_character_details(character["id"])
        
        # Create navigation buttons
        buttons = []
        nav_row = []
        
        if page_num > 1:
            nav_row.append(InlineKeyboardButton("⬅️ Previous", callback_data=f"vidlist_{user_id}_{page_num-1}"))
            
        nav_row.append(InlineKeyboardButton("❌ Close", callback_data=f"close_vidlist_{user_id}"))
        
        if page_num < total_pages:
            nav_row.append(InlineKeyboardButton("Next ➡️", callback_data=f"vidlist_{user_id}_{page_num+1}"))
            
        buttons.append(nav_row)
        keyboard = InlineKeyboardMarkup(buttons)
        
        # Get character details and create message
        details = await get_video_details(character)
        caption = f"**Video {WAIFU}s List (Page {page_num}/{total_pages})**\n\n{details}"
        
        return char_details.get("video_url"), caption, keyboard
    
    # Show first page
    video_url, caption, keyboard = await show_page(1)
    await message.reply_video(
        video=video_url,
        caption=caption,
        reply_markup=keyboard
    )

@app.on_callback_query(filters.regex(r"vidlist_(\d+)_(\d+)"))
async def video_list_pagination(client: Client, callback_query: CallbackQuery):
    user_id = int(callback_query.data.split("_")[1])
    page_num = int(callback_query.data.split("_")[2])
    
    if callback_query.from_user.id != user_id:
        await callback_query.answer("This is not your list!", show_alert=True)
        return
        
    # Get all characters again (could be optimized with caching if needed)
    all_characters = await get_all_images()
    video_characters = [char for char in all_characters if char.get("is_video", False)]
    video_characters.sort(key=lambda x: x["id"])
    
    # Function to generate message for a video character
    async def get_video_details(character):
        char_details = await get_character_details(character["id"])
        global_count, unique_users = await get_global_smash_count(character["id"])
        
        return (
            f"**💫 Name:** {char_details['name']}\n"
            f"**🆔 ID:** `{char_details['id']}`\n"
            f"{char_details['rarity_sign']} **Rarity:** {char_details['rarity']}\n"
            f"**🤝 {ANIME}:** {char_details['anime']}\n"
            f"**📊 Stats:**\n"
            f"- Global Count: {global_count}\n"
            f"- Unique Owners: {unique_users}\n"
            f"**📽️ Type:** Video {WAIFU}"
        )
    
    # Create navigation buttons
    buttons = []
    nav_row = []
    
    if page_num > 1:
        nav_row.append(InlineKeyboardButton("⬅️ Previous", callback_data=f"vidlist_{user_id}_{page_num-1}"))
        
    nav_row.append(InlineKeyboardButton("❌ Close", callback_data=f"close_vidlist_{user_id}"))
    
    if page_num < len(video_characters):
        nav_row.append(InlineKeyboardButton("Next ➡️", callback_data=f"vidlist_{user_id}_{page_num+1}"))
        
    buttons.append(nav_row)
    keyboard = InlineKeyboardMarkup(buttons)
    
    # Get character details and update message
    character = video_characters[page_num - 1]
    char_details = await get_character_details(character["id"])
    details = await get_video_details(character)
    caption = f"**Video {WAIFU}s List (Page {page_num}/{len(video_characters)})**\n\n{details}"
    
    try:
        await callback_query.message.edit_media(
            media=InputMediaVideo(
                media=char_details.get("video_url"),
                caption=caption
            ),
            reply_markup=keyboard
        )
    except Exception as e:
        print(f"Error updating video: {e}")
        await callback_query.answer("Error updating video. Please try again.", show_alert=True)
    
    await callback_query.answer()

@app.on_callback_query(filters.regex(r"close_vidlist_(\d+)"))
async def close_video_list(client: Client, callback_query: CallbackQuery):
    user_id = int(callback_query.data.split("_")[2])
    
    if callback_query.from_user.id != user_id:
        await callback_query.answer("This is not your list!", show_alert=True)
        return
        
    await callback_query.message.delete()
    await callback_query.answer()
