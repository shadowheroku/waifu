from pyrogram import Client
from pyrogram.types import Message
from pyrogram.enums import ParseMode, ChatType
from Bot import app , Command
from Bot.utils import command_filter, warned_users, ignore_duration
import time
from Bot.config import OWNERS
from Bot.database.privacydb import is_user_sudo , is_user_og
from Bot.database.characterdb import get_character_details , get_total_uploaded_characters
from Bot.database.preferencedb import get_custom_title_by_user_id, get_custom_pfp_url_by_user_id
from Bot.database.grabtokendb import get_user_balance
from Bot.database.smashdb import get_user_smash_count
from Bot.database.leaderboarddb import get_leaderboard_data, get_chat_leaderboard_data
from Bot.database.collectiondb import get_user_collection


@app.on_message(Command("status") & command_filter)
async def sstatus(client: Client, message: Message):
    user_id = message.from_user.id
    user_name = message.from_user.first_name

    # Check if user is the owner or a sudo user
    is_owner = user_id in OWNERS
    is_sudo = await is_user_sudo(user_id) or await is_user_og(user_id)
    
    x = await message.reply_text("Please Wait Getting Your Info....")

    # Fetch user collection
    user_collection = await get_user_collection(user_id)
    if not user_collection:
        await message.reply("**Nᴏ ᴄᴏʟʟᴇᴄᴛɪᴏɴ ғᴏᴜɴᴅ ғᴏʀ ᴛʜɪs ᴜsᴇʀ.**")
        return
    
    total_uploaded_characters = await get_total_uploaded_characters()

    # Calculate total waifus and harem count
    total_waifus = sum(image["count"] for image in user_collection.get("images", []))
    unique_waifus = len(user_collection.get("images", []))
    harem_percentage = (unique_waifus / total_uploaded_characters) * 100 if total_uploaded_characters > 0 else 0

    # Determine user level
    level = unique_waifus // 50 + 1

    # Get rarities count
    rarities = {"Legendary": 0, "Rare": 0, "Medium": 0, "Common": 0 , "Uncommon" : 0 , "Divine" : 0 , "Mythic" : 0 , "Ethereal" : 0 , "Epic" : 0 , "Exclusive": 0 , "Cosmic": 0 , "Limited Edition": 0 , "Ultimate":0 , "Supreme": 0 }
    for image in user_collection.get("images", []):
        character = await get_character_details(image["image_id"])
        if character and character["rarity"] in rarities:
            rarities[character["rarity"]] += 1

    # Fetch user's smash count
    user_smash_count = await get_user_smash_count(user_id)

    # Assign title based on smash count or if the user is the owner/sudo
    if is_owner:
        user_title = "Owner"
        rank_emoji = "👾" 
    elif is_sudo:
        user_title = "Corps"
        rank_emoji = "⚡"
    elif user_smash_count >= 4000:
        user_title = "Conqueror"
        rank_emoji = "🔱" 
    elif user_smash_count >= 2400:
        user_title = "Titan"
        rank_emoji = "🪬" 
    elif user_smash_count >= 1500:
        user_title = "Ace"
        rank_emoji = "🔰" 
    elif user_smash_count >= 1000:
        user_title = "Inferno"
        rank_emoji = " 🛸" 
    elif user_smash_count >= 600:
        user_title = "Diamond"
        rank_emoji = "💎" 
    elif user_smash_count >= 300:
        user_title = "Platinum"
        rank_emoji = "🗡️" 
    elif user_smash_count >= 150:
        user_title = "Gold"
        rank_emoji = "🥇"   
    elif user_smash_count >= 50:
        user_title = "Silver"
        rank_emoji = "🥈"
    else:
        user_title = "Bronze"
        rank_emoji = "🥉"

    # Fetch global leaderboard data
    global_leaderboard = await get_leaderboard_data()

    # Get chat position if in group
    if message.chat.type != ChatType.PRIVATE:
        # Fetch all member IDs in the group chat
        member_ids = [member.user.id async for member in client.get_chat_members(message.chat.id)]
        chat_leaderboard = await get_chat_leaderboard_data(member_ids)
        chat_position = next((index + 1 for index, entry in enumerate(chat_leaderboard) if entry["user_id"] == user_id), len(chat_leaderboard))
    else:
        chat_position = 1

    # Calculate global position
    global_position = next((index + 1 for index, entry in enumerate(global_leaderboard) if entry["user_id"] == user_id), len(global_leaderboard))

    # Fetch custom profile picture (pfp) URL
    custom_pfp_url = await get_custom_pfp_url_by_user_id(user_id)

    # If no custom pfp URL, fetch the default profile picture
    pfp_url = custom_pfp_url
    if not pfp_url:
        async for photo in client.get_chat_photos(user_id):
            pfp_url = photo.file_id
            break  # Get the first profile photo only

    # If no pfp, fallback to one character's image
    if not pfp_url and user_collection.get("images"):
        character = await get_character_details(user_collection["images"][0]["image_id"])
        pfp_url = character["img_url"]

    # Check if the user is currently banned
    remaining_time = None
    if user_id in warned_users:
        elapsed_time = time.time() - warned_users[user_id]
        if elapsed_time < ignore_duration:
            remaining_time = ignore_duration - elapsed_time

    # Fetch custom title, if available
    custom_title = await get_custom_title_by_user_id(user_id)
    if custom_title:
        user_name_with_title = f"{user_name} [{custom_title}]"
    else:
        user_name_with_title = user_name

    # Format the remaining time if the user is banned
    ban_status = ""
    if remaining_time:
        minutes, seconds = divmod(int(remaining_time), 60)
        ban_status = f"━━━━━━━━━━━━━━━\n━|⛔|<b> Banned:</b> → {minutes}m {seconds}s remaining\n━━━━━━━━━━━━━━━\n\n"

    # Generate the bar meter based on harem percentage
    filled_bars = int(harem_percentage // 10)
    unfilled_bars = 10 - filled_bars
    bar_meter = "▰" * filled_bars + "▱" * unfilled_bars

    # Fetch user's balance
    user_balance = await get_user_balance(user_id)

    # Create the status message
    status_message = (
        "━━\🕊<b> User's Stats</b> 🕊/━━\n\n"
        f"━|👤|<b> User</b> → {user_name_with_title}\n"
        f"━|🐙|<b> User ID</b> → {user_id}\n"
        f"━|🎖️|<b> Level</b> → {level}\n"
        f"━|{rank_emoji}|<b> Rank</b> → {user_title}\n"
        f"━|✨|<b> Total Collected</b> → {total_waifus} ({unique_waifus})\n"
        f"━|🍁|<b> Collection</b> → {unique_waifus}/{total_uploaded_characters} ({harem_percentage:.2f}%)\n"
        f"━|💰|<b> Balance</b> → {user_balance} Grab-Tokens\n"
        f"━|📈|<b> Progress Bar </b>→\n{bar_meter}\n\n"
        f"{ban_status}"
        f"━|👑|<i><b> Supreme</b></i> → {rarities['Supreme']}\n"
        f"━|🔱|<i><b> Ultimate</b></i> → {rarities['Ultimate']}\n"
        f"━|🔮|<i><b> Limited Edition</b></i> → {rarities['Limited Edition']}\n"
        f"━|💠|<i><b> Cosmic</b></i> → {rarities['Cosmic']}\n"
        f"━|💮|<i><b> Exclusive</b></i> → {rarities['Exclusive']}\n"
        f"━|🟡|<i><b> Legendary</b></i> → {rarities['Legendary']}\n"
        f"━|🟠|<i><b> Rare</b></i> → {rarities['Rare']}\n"
        f"━|🟢|<i><b> Medium</b></i> → {rarities['Medium']}\n"
        f"━|⚪️|<i><b> Common</b></i> → {rarities['Common']}\n"
        f"━|🟤|<i><b> Uncommon</b></i> → {rarities['Uncommon']}\n"
        f"━|⚜️|<i><b> Epic</b></i> → {rarities['Epic']}\n"
        f"━|🔴|<i><b> Mythic</b></i> → {rarities['Mythic']}\n"
        f"━|💫|<i><b> Divine</b></i> → {rarities['Divine']}\n"
        f"━|❄️|<i><b> Ethereal</b></i> → {rarities['Ethereal']}\n\n"
        f"━━━━━━━━━━━━━━━\n"
        f"━|🌍|<b> Position Globally</b> → {global_position}\n"
        f"━|💬|<b> Chat Position</b> → {chat_position:02d}\n"
    )

    await x.delete()

    # Send the status message with the pfp or character image as caption
    if pfp_url:
        await message.reply_photo(
            photo=pfp_url,
            caption=status_message,
            parse_mode=ParseMode.HTML
        )
    else:
        await message.reply(status_message)

