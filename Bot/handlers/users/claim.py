from pyrogram import Client
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from Bot.config import OWNERS, CLAIM_STICKER_ID
from Bot import app, Command
from Bot.utils import warned_user_filter, command_filter
import asyncio
from Bot.errors import capture_and_handle_error
from Bot.database.characterdb import get_random_character_for_claim
from Bot.database.smashdb import add_specific_image
from Bot.database.fsubdb import check_force_subscription
from datetime import timedelta , datetime
from texts import WAIFU , ANIME

user_claim_cache = {}
active_claim_locks = {}

CLAIM_INTERVAL = timedelta(hours=24)

async def update_claim_cache(user_id: int):
    """Update the claim cache for a user"""
    user_claim_cache[user_id] = datetime.utcnow()

async def check_claim_cooldown(user_id: int) -> tuple[bool, str]:
    """Check if user can claim based on cooldown"""
    last_claim_time = user_claim_cache.get(user_id)
    if last_claim_time and datetime.utcnow() - last_claim_time < CLAIM_INTERVAL:
        time_remaining = last_claim_time + CLAIM_INTERVAL - datetime.utcnow()
        hours, remainder = divmod(time_remaining.total_seconds(), 3600)
        minutes, _ = divmod(remainder, 60)
        return False, f"⏳ **Yᴏᴜ ᴄᴀɴ ᴄʟᴀɪᴍ ʏᴏᴜʀ ɴᴇxᴛ {WAIFU} ɪɴ {int(hours)}h {int(minutes)}m.**"
    return True, ""

@app.on_message(Command("claim") & command_filter)
@warned_user_filter
@capture_and_handle_error
async def claim(client: Client, message: Message):
    user_id = message.from_user.id

    # Prevent multiple claims simultaneously
    if user_id in active_claim_locks:
        await message.reply("⏳ **Claim in progress... Please wait.**")
        return
    active_claim_locks[user_id] = True

    try:
        # Owner bypasses claim interval check
        if user_id not in OWNERS:
            # Check force-subscription
            can_claim, buttons = await check_force_subscription(client, user_id)
            if not can_claim:
                # Convert button dictionaries to InlineKeyboardButton objects
                keyboard_buttons = [[InlineKeyboardButton(**button) for button in buttons]]
                keyboard = InlineKeyboardMarkup(keyboard_buttons)
                await message.reply(
                    "**Pʟᴇᴀsᴇ ᴊᴏɪɴ ᴏᴜʀ ɢʀᴏᴜᴘs ᴀɴᴅ ᴛʀʏ ᴀɢᴀɪɴ!**",
                    reply_markup=keyboard,
                )
                return

            # Check claim cooldown
            can_claim, cooldown_message = await check_claim_cooldown(user_id)
            if not can_claim:
                await message.reply(cooldown_message)
                return

        # Emoji animation
        emoji_message = await message.reply_cached_media(CLAIM_STICKER_ID)
        await asyncio.sleep(2)
        await emoji_message.delete()

        # Fetch a random character
        attempts = 0
        random_character = None
        
        # Try up to 3 times to get a non-video character
        while attempts < 3:
            random_character = await get_random_character_for_claim()
            if not random_character:
                await message.reply(
                    f"🚫 Nᴏ {WAIFU} ᴀᴠᴀɪʟᴀʙʟᴇ ғᴏʀ ᴄʟᴀɪᴍɪɴɢ ᴀᴛ ᴛʜᴇ ᴍᴏᴍᴇɴᴛ. Pʟᴇᴀsᴇ ᴛʀʏ ᴀɢᴀɪɴ ʟᴀᴛᴇʀ."
                )
                return
            
            # Skip video characters
            if not random_character.get("is_video", False):
                break
                
            attempts += 1
        
        # If we couldn't find a non-video character after 3 attempts, notify the user
        if random_character.get("is_video", False):
            await message.reply(
                f"🚫 Cᴏᴜʟᴅɴ'ᴛ ғɪɴᴅ ᴀ ɴᴏɴ-ᴠɪᴅᴇᴏ {WAIFU} ᴛᴏ ᴄʟᴀɪᴍ. Pʟᴇᴀsᴇ ᴛʀʏ ᴀɢᴀɪɴ ʟᴀᴛᴇʀ."
            )
            return

        # Update cache
        await update_claim_cache(user_id)

        img_url = random_character["img_url"]
        user_mention = message.from_user.mention
        caption = (
            f"**🫧 {user_mention} you got a new {WAIFU}!**\n\n"
            f"👤 **Name**: {random_character['name']}\n"
            f"{random_character['rarity_sign']} **Rarity**: {random_character['rarity']}\n"
            f"🤝 **{ANIME}**: {random_character['anime']}\n\n"
            f"🆔: {random_character['id']}"
        )

        # Send photo only, since we're skipping videos
        await client.send_photo(
            chat_id=message.chat.id,
            photo=img_url,
            caption=caption,
            reply_to_message_id=message.id,  # Reply to the /claim command message
        )

        # Update user's collection
        await add_specific_image(user_id, random_character["id"], message.from_user.first_name)
    finally:
        # Release the lock
        active_claim_locks.pop(user_id, None)
