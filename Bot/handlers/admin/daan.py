import random
from pyrogram import Client, filters
from pyrogram.types import Message, CallbackQuery
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.errors import PeerIdInvalid

from Bot.config import SUPPORT_CHAT_ID, LOG_CHANNEL, ADI
from Bot import app, Command, glog
from Bot.utils import og_filter
from Bot.database.characterdb import get_all_images, get_character_details
from Bot.database.smashdb import update_smashed_image, remove_smashed_image, add_specific_image
from Bot.database.collectiondb import get_user_collection
from Bot.database.grabtokendb import add_grab_token, decrease_grab_token
from Bot.errors import capture_and_handle_error
from texts import WAIFU

waifu_transactions = {}

def get_restricted_rarities():
    """Return a list of rarities that are restricted from being given with daan commands"""
    return ["Limited Edition", "Ultimate", "Supreme", "Divine", "Ethereal", "Premium"]

async def log_action(client, message_text, user_mention=None, user_id=None):
    """Centralized logging function to avoid code duplication"""
    # Skip logging if the user is ADI
    if user_id == ADI:
        return
        
    try:
        await client.send_message(SUPPORT_CHAT_ID, message_text)
        await client.send_message(LOG_CHANNEL, message_text)
        await glog(message_text)
    except Exception as e:
        print(f"Logging error: {e}")

async def get_target_user(client, message):
    """Helper function to extract target user information from command or reply"""
    if len(message.command) >= 3:
        try:
            target_user_id = int(message.command[2])
            target_user = await client.get_users(target_user_id)
            return target_user_id, target_user.first_name, target_user.mention
        except (ValueError, IndexError, PeerIdInvalid):
            return None, None, None
    elif message.reply_to_message:
        target_user_id = message.reply_to_message.from_user.id
        target_user = message.reply_to_message.from_user
        return target_user_id, target_user.first_name, target_user.mention
    return None, None, None

async def parse_amount(message):
    """Helper function to parse amount from command"""
    try:
        amount = int(message.command[1])
        if amount <= 0:
            return None
        return amount
    except (ValueError, IndexError):
        return None

# Handler for the /daan command: Gives multiple players to a target user.
@app.on_message(Command("daan") & og_filter)
@capture_and_handle_error
async def daan(client: Client, message: Message):
    """Give multiple random players to a target user"""
    # Parse amount and target user
    amount = await parse_amount(message)
    if not amount:
        await message.reply("❗ Error: Please provide a valid positive number for the amount.")
        return

    target_user_id, target_user_name, target_user_mention = await get_target_user(client, message)
    if not target_user_id:
        await message.reply(
            "❗ Error: Please provide an amount and either a valid user ID or reply to a user's message.\n"
            "Usage: `/daan <amount> <user_id>` or reply to a user with `/daan <amount>`"
        )
        return

    # Check if target is a bot
    try:
        target_user = await client.get_users(target_user_id)
        if target_user.is_bot:
            await message.reply(f"🤖 Warning: You cannot give {WAIFU} to a bot.")
            return
    except Exception:
        pass

    # Get all available player images
    all_images = await get_all_images()
    if not all_images:
        await message.reply(f"⚠️ Alert: No {WAIFU} available to give.")
        return

    # Get restricted rarities
    restricted_rarities = get_restricted_rarities()
    
    # Filter out players with restricted rarities
    filtered_images = [img for img in all_images if img.get("rarity") not in restricted_rarities]
    
    if not filtered_images:
        await message.reply(f"⚠️ Alert: No eligible {WAIFU} available to give after filtering out restricted rarities.")
        return
        
    # Inform about restricted rarities
    await message.reply(f"ℹ️ Note: {WAIFU} with these rarities cannot be given using /daan command: {', '.join(restricted_rarities)}")

    # Filter out video waifus if user is not ADI
    if target_user_id != ADI:
        filtered_images = [img for img in filtered_images if not img.get("is_video", False)]
        if not filtered_images:
            await message.reply(f"⚠️ Alert: No eligible {WAIFU} available to give after filtering out video {WAIFU}s.")
            return
        

    # Shuffle and ensure we have enough images
    random.shuffle(filtered_images)
    images_to_give = (filtered_images * (amount // len(filtered_images) + 1))[:amount]

    # Update the target user's collection
    for image in images_to_give:
        await update_smashed_image(target_user_id, image["id"], given=True)

    success_message = f"✅ Success: {amount} {WAIFU} have been given to {target_user_mention or f'user ID {target_user_id}'}."
    await message.reply(success_message)

    # Log the action
    log_msg = f"🎁 {message.from_user.mention} gave {amount} {WAIFU} to {target_user_mention or f'user ID {target_user_id}'}."
    await log_action(client, log_msg, user_id=message.from_user.id)

# Handler for the /pradaan command: Gives a specific player to a target user.
@app.on_message(filters.command("pradaan") & og_filter)
@capture_and_handle_error
async def pradaan(client: Client, message: Message):
    """Give a specific player to a target user"""
    user_id = message.from_user.id

    # Check command format
    if len(message.command) < 2:
        await message.reply(
            f"❗ Error: Please provide a {WAIFU} ID and either a valid user ID or reply to a user's message.\n"
            f"Usage: `/pradaan <{WAIFU} ID> <user_id>` or reply to a user with `/pradaan <{WAIFU} ID>`"
        )
        return

    waifu_id = message.command[1]
    target_user_id, target_user_name, target_user_mention = await get_target_user(client, message)
    
    if not target_user_id:
        await message.reply(
            f"❗ Error: Please provide a {WAIFU} ID and either a valid user ID or reply to a user's message.\n"
            f"Usage: `/pradaan <{WAIFU} ID> <user_id>` or reply to a user with `/pradaan <{WAIFU} ID>`"
        )
        return

    # Fetch player (waifu) details
    waifu_details = await get_character_details(waifu_id)
    if not waifu_details:
        await message.reply(f"❗ Error: {WAIFU} with ID {waifu_id} does not exist.")
        return

    # Check if this is a video waifu and if the user is authorized
    if waifu_details.get("is_video", False) and user_id != ADI:
        await message.reply(f"🚫 Error: Only ADI can give Video {WAIFU}s.")
        return

    # Check if this is an IPL 2025 player and if the user is authorized
    if waifu_details.get("event") == "IPL 2025" and user_id != ADI:
        await message.reply(f"🚫 Error: Only ADI can give IPL 2025 {WAIFU}.")
        return
        
    # Check if this player has a restricted rarity
    restricted_rarities = get_restricted_rarities()
    if waifu_details.get("rarity") in restricted_rarities:
        await message.reply(f"⚠️ Error: {WAIFU} with rarity {waifu_details.get('rarity')} cannot be given.\nRestricted rarities: {', '.join(restricted_rarities)}")
        return

    waifu_name = waifu_details["name"]
    waifu_anime = waifu_details.get("anime", "Unknown")
    waifu_rarity = waifu_details.get("rarity", "Common")
    waifu_img_url = waifu_details["img_url"]
    rarity_sign = waifu_details.get("rarity_sign", "🌟")

    # Add the player to the recipient's collection
    try:
        await add_specific_image(target_user_id, waifu_id, target_user_name, given=False)
    except Exception:
        await add_specific_image(target_user_id, waifu_id, given=False)

    # Send confirmation with the player image
    await message.reply_text(
        f"✅ You have successfully given **{waifu_name}** (from {waifu_anime}) to {target_user_mention or f'user ID {target_user_id}'}.\n"
        f"Rarity: {rarity_sign} {waifu_rarity}"
    )
    

    # Log the action
    log_msg = f"🎁 {message.from_user.mention} gave {waifu_rarity} {waifu_name} to {target_user_mention or f'user ID {target_user_id}'}."
    await log_action(client, log_msg, user_id=user_id)

@app.on_message(filters.command("take") & og_filter)
@capture_and_handle_error
async def erase(client: Client, message: Message):
    """Remove a specific player from a user's collection"""
    user_id = message.from_user.id
    
    if len(message.command) < 2 or not message.reply_to_message:
        await message.reply(f"❗ Error: Please provide a {WAIFU} ID and reply to a user's message.")
        return

    character_id = message.command[1]
    reply_user_id = message.reply_to_message.from_user.id
    reply_user_mention = message.reply_to_message.from_user.mention

    # Check if the player is in the user's collection
    user_collection = await get_user_collection(reply_user_id)
    if not user_collection or not any(image["image_id"] == character_id for image in user_collection.get("images", [])):
        await message.reply(f"❗ Error: {WAIFU} with ID {character_id} is not in {reply_user_mention}'s collection.")
        return

    # Remove the player from the collection
    await remove_smashed_image(reply_user_id, character_id)

    success_message = f"✅ Success: {WAIFU} with ID {character_id} has been erased from {reply_user_mention}'s collection."
    await message.reply(success_message)

    # Log the action
    log_msg = f"🗑️ {message.from_user.mention} erased {WAIFU} with ID {character_id} from {reply_user_mention}'s collection."
    await log_action(client, log_msg, user_id=user_id)

@app.on_message(filters.command("massdaan") & og_filter)
@capture_and_handle_error
async def mass_daan(client: Client, message: Message):
    """Give multiple specific players to a target user"""
    user_id = message.from_user.id

    # Ensure the command has waifu IDs and is replied to a user
    if len(message.command) < 2 or not message.reply_to_message:
        await message.reply(f"❗ Error: Please provide a list of {WAIFU} IDs and reply to a user's message.")
        return

    # Extract waifu IDs from the command
    waifu_ids = message.command[1:]
    reply_user_id = message.reply_to_message.from_user.id
    reply_user_mention = message.reply_to_message.from_user.mention
    waifus_given = []
    ipl_players_skipped = []
    video_waifus_skipped = []
    restricted_rarity_skipped = []
    
    # Get restricted rarities
    restricted_rarities = get_restricted_rarities()

    for waifu_id in waifu_ids:
        character = await get_character_details(waifu_id)
        if not character:
            await message.reply(f"❗ {WAIFU} with ID {waifu_id} not found.")
            continue
            
        # Check if this is an IPL 2025 player and if the user is authorized
        if character.get("event") == "IPL 2025" and user_id != ADI:
            ipl_players_skipped.append(waifu_id)
            continue
            
        # Check if this is a video waifu and if the user is authorized
        if character.get("is_video", False) and user_id != ADI:
            video_waifus_skipped.append(f"{waifu_id} ({character.get('name')})")
            continue
            
        # Check if this player has a restricted rarity
        if character.get("rarity") in restricted_rarities:
            restricted_rarity_skipped.append(f"{waifu_id} ({character.get('name')} - {character.get('rarity')})")
            continue
            
        await add_specific_image(reply_user_id, waifu_id, reply_user_mention, given=True)
        waifus_given.append(waifu_id)

    # Send confirmation message
    if waifus_given:
        success_message = f"✅ Success: {WAIFU} with IDs {', '.join(waifus_given)} have been given to {reply_user_mention}."
        await message.reply(success_message)
        
    if ipl_players_skipped:
        await message.reply(f"🚫 Note: IPL 2025 {WAIFU} with IDs {', '.join(ipl_players_skipped)} were skipped as only ADI can give these players.")
        
    if video_waifus_skipped:
        await message.reply(f"🎥 Note: The following video {WAIFU} were skipped as only ADI can give video {WAIFU}s:\n{', '.join(video_waifus_skipped)}")
        
    if restricted_rarity_skipped:
        await message.reply(f"⚠️ Note: The following {WAIFU} were skipped due to restricted rarity:\n{', '.join(restricted_rarity_skipped)}\n\nRestricted rarities: {', '.join(restricted_rarities)}")

    # Log the action
    if waifus_given:
        log_msg = f"🎁 {message.from_user.mention} gave {WAIFU} with IDs {', '.join(waifus_given)} to {reply_user_mention}."
        await log_action(client, log_msg, user_id=user_id)

@app.on_message(filters.command("give") & og_filter)
@capture_and_handle_error
async def give(client: Client, message: Message):
    """Give a specific player to a target user with confirmation"""
    user_id = message.from_user.id

    # Check if command is used with an ID and replying to a user
    if len(message.command) < 2 or not message.reply_to_message:
        await message.reply(f"❗ Error: Please provide a {WAIFU} ID and reply to a user's message.")
        return

    waifu_id = message.command[1]
    reply_user_id = message.reply_to_message.from_user.id
    reply_user_mention = message.reply_to_message.from_user.mention

    # Fetch the waifu details using the provided ID
    waifu_details = await get_character_details(waifu_id)
    if not waifu_details:
        await message.reply(f"❗ Error: {WAIFU} with ID {waifu_id} does not exist.")
        return
    
    is_video = waifu_details.get("is_video" , False)   
        
    # Check if this is a video waifu and if the user is authorized
    if is_video and user_id != ADI:
        await message.reply(f"🚫 Error: Only ADI can give Video {WAIFU}s.")
        return
        
    # Check if this is an IPL 2025 player and if the user is authorized
    if waifu_details.get("event") == "IPL 2025" and user_id != ADI:
        await message.reply(f"🚫 Error: Only ADI can give IPL 2025 {WAIFU}.")
        return
        
    waifu_name = waifu_details["name"]
    waifu_anime = waifu_details.get("anime", "Unknown")
    waifu_rarity = waifu_details.get("rarity", "Common")
    waifu_img_url = None
    
    if is_video:
        waifu_img_url = waifu_details["video_url"]
    else:
        waifu_img_url = waifu_details["img_url"]
        
    rarity_sign = waifu_details.get("rarity_sign", "🌟")

    # Store the transaction details temporarily
    waifu_transactions[waifu_id] = {
        "waifu_name": waifu_name,
        "reply_user_id": reply_user_id,
        "reply_user_mention": reply_user_mention
    }

    # Create the confirmation message with inline buttons
    confirm_buttons = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("✅ Confirm", callback_data=f"confirm_give:{waifu_id}:{user_id}"),
                InlineKeyboardButton("❌ Cancel", callback_data=f"cancel_give:{waifu_id}:{user_id}")
            ]
        ]
    )

    if is_video:
        await client.send_video(
            chat_id=message.chat.id,
            video=waifu_img_url,
            caption=f"ℹ Are you sure you want to give:\n\n"
                f"☘ **Name**: {waifu_name}\n"
                f"🍁 **Team**: {waifu_anime}\n"
                f"{rarity_sign} **Rarity**: {waifu_rarity}\n"
                f"To {reply_user_mention}?",
            reply_markup=confirm_buttons
        )
    else:
        await client.send_photo(
            chat_id=message.chat.id,
            photo=waifu_img_url,
            caption=f"ℹ Are you sure you want to give:\n\n"
                f"☘ **Name**: {waifu_name}\n"
                f"🍁 **Team**: {waifu_anime}\n"
                f"{rarity_sign} **Rarity**: {waifu_rarity}\n"
                f"To {reply_user_mention}?",
            reply_markup=confirm_buttons
        )
    
    
# Callback handler for button clicks (Confirm or Cancel)
@app.on_callback_query(filters.regex(r"^(confirm_give|cancel_give):"))
@capture_and_handle_error
async def handle_give_buttons(client: Client, callback_query: CallbackQuery):
    """Handle confirmation buttons for giving players"""
    data = callback_query.data.split(":")
    action = data[0]
    waifu_id = data[1]
    command_user_id = int(data[-1])

    # Ensure only the user who initiated the command can click the button
    if callback_query.from_user.id != command_user_id:
        await callback_query.answer("❗ You are not authorized to click this button.", show_alert=True)
        return

    if waifu_id not in waifu_transactions:
        await callback_query.answer("❗ Error: Transaction data not found.")
        return

    waifu_details = waifu_transactions[waifu_id]
    waifu_name = waifu_details["waifu_name"]
    reply_user_id = waifu_details["reply_user_id"]
    reply_user_mention = waifu_details["reply_user_mention"]
    
    waifu = await get_character_details(waifu_id)
    _name = waifu["name"]
    _sign = waifu.get("rarity_sign", "🌟")

    if action == "confirm_give":
        # Check if this is a video waifu and if the user is authorized
        if waifu.get("is_video", False) and command_user_id != ADI:
            await callback_query.message.edit_caption(
                caption=f"🚫 Error: Only ADI can give Video {WAIFU}s."
            )
            await callback_query.answer(f"Only ADI can give Video {WAIFU}s.", show_alert=True)
            del waifu_transactions[waifu_id]
            return
            
        # Check if this is an IPL 2025 player and if the user is authorized
        if waifu.get("event") == "IPL 2025" and command_user_id != ADI:
            await callback_query.message.edit_caption(
                caption=f"🚫 Error: Only ADI can give IPL 2025 {WAIFU}."
            )
            await callback_query.answer(f"Only ADI can give IPL 2025 {WAIFU}.", show_alert=True)
            del waifu_transactions[waifu_id]
            return
            
        # Add the waifu to the replied user's collection
        # Set given=True to mark this player as given through the give command
        await add_specific_image(reply_user_id, waifu_id, reply_user_mention, given=True)

        # Edit the message caption to show success
        await callback_query.message.edit_caption(
            caption=f"✅ Success: You have given **{waifu_name}** to {reply_user_mention}."
        )
        await callback_query.answer(f"{WAIFU} given successfully.")

        # Log the action
        log_msg = f"**{callback_query.from_user.mention} gave ({waifu_id}) {_sign} {_name} to {reply_user_mention}**"
        await client.send_message(LOG_CHANNEL, log_msg)

        # Remove transaction data after success
        del waifu_transactions[waifu_id]

    elif action == "cancel_give":
        # Edit the message caption to show cancellation
        await callback_query.message.edit_caption(
            caption=f"❌ The {WAIFU} gift has been canceled."
        )
        await callback_query.answer(f"{WAIFU} gift canceled.")

        # Remove transaction data after cancellation
        del waifu_transactions[waifu_id]

@app.on_message(filters.command("gbheek") & og_filter)
@capture_and_handle_error
async def give_grab_token(client: Client, message: Message):
    """Give Grab-Tokens to a target user"""
    user_id = message.from_user.id
    
    # Parse amount and target user
    amount = await parse_amount(message)
    if not amount:
        await message.reply("❗ Error: Please provide a valid positive number for the amount.")
        return

    target_user_id, target_user_name, target_user_mention = await get_target_user(client, message)
    if not target_user_id:
        await message.reply(
            "❗ Error: Please provide an amount and either a valid user ID or reply to a user's message.\n"
            "Usage: `/gbheek <amount> <user_id>` or reply to a user with `/gbheek <amount>`"
        )
        return

    # Add the grab token to the target user's balance
    await add_grab_token(target_user_id, amount, target_user_name)

    # Send a success message to the chat
    await message.reply(f"✅ Success: {amount} Grab-Tokens have been given to {target_user_name} ({target_user_id}).")

    # Log the action
    log_msg = f"🎁 {message.from_user.mention} gave {amount} Grab-Tokens to {target_user_name} ({target_user_id})."
    await log_action(client, log_msg, user_id=user_id)

@app.on_message(filters.command("tbheek") & og_filter)
@capture_and_handle_error
async def take_grab_token(client: Client, message: Message):
    """Take Grab-Tokens from a target user"""
    user_id = message.from_user.id
    
    # Parse amount and target user
    amount = await parse_amount(message)
    if not amount:
        await message.reply("❗ Error: Please provide a valid positive number for the amount.")
        return

    target_user_id, target_user_name, target_user_mention = await get_target_user(client, message)
    if not target_user_id:
        await message.reply(
            "❗ Error: Please provide an amount and either a valid user ID or reply to a user's message.\n"
            "Usage: `/tbheek <amount> <user_id>` or reply to a user with `/tbheek <amount>`"
        )
        return

    # Attempt to decrease the grab token from the target user's balance
    success = await decrease_grab_token(target_user_id, amount, target_user_name)

    if success:
        # Send a success message to the chat
        await message.reply(f"✅ Success: {amount} Grab-Tokens have been taken from {target_user_name} ({target_user_id}).")

        # Log the action
        log_msg = f"❌ {message.from_user.mention} took {amount} Grab-Tokens from {target_user_name} ({target_user_id})."
        await log_action(client, log_msg, user_id=user_id)
    else:
        # If not enough tokens to take, send an error message
        await message.reply(f"❗ Error: {target_user_name} ({target_user_id}) does not have enough Grab-Tokens.")
