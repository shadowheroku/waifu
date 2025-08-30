import random
import string
from pyrogram import Client, filters
from pyrogram.types import Message
from Bot.database.redeemdb import find_redeem_code, create_redeem_code, update_redeem_code, delete_redeem_code
from Bot.database.smashdb import update_smashed_image 
from Bot.database.characterdb import get_character_details
from Bot import app , Command
from Bot.config import OWNERS
from Bot.utils import warned_user_filter , command_filter
from texts import WAIFU , ANIME

async def generate_unique_code():
    """Generate a unique 8-character alphanumeric redeem code."""
    while True:
        code = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
        # Ensure the code is unique
        if not await find_redeem_code(code):
            return code

@app.on_message(Command("credeem") & filters.user(OWNERS))
async def create_redeem_code_handler(client: Client, message: Message):
    if len(message.command) < 3:
        await message.reply(f"Usᴀɢᴇ: /ᴄʀᴇᴅᴇᴇᴍ {WAIFU}_ɪᴅ ʀᴇᴅᴇᴍᴘᴛɪᴏɴ_ᴄᴏᴜɴᴛ")
        return

    character_id = message.command[1]
    redemption_count = int(message.command[2])

    # Check if the character exists in the database
    character = await get_character_details(character_id)
    if not character:
        await message.reply(f"Tʜɪs {WAIFU} ᴅᴏᴇs ɴᴏᴛ ᴇxɪsᴛ.")
        return
        
    # Check if the character has the IPL 2025 event
    if character.get("event") == "IPL 2025":
        await message.reply(f"🚫 Error: Redeem codes cannot be created for IPL 2025 {WAIFU}.")
        return
    
    if character.get("is_video", False):
        await message.reply(f"🚫 Error: Redeem codes cannot be created for video {WAIFU}.")
        return

    # Generate a unique redeem code
    redeem_code = await generate_unique_code()

    # Save the redeem code in the database
    await create_redeem_code(redeem_code, character_id, redemption_count)

    # Get character details for the response
    character_name = character.get("name", "Unknown")
    character_rarity = character.get("rarity", "Unknown")
    character_rarity_sign = character.get("rarity_sign", "")
    
    await message.reply(
        f"Rᴇᴅᴇᴇᴍ ᴄᴏᴅᴇ ᴄʀᴇᴀᴛᴇᴅ...\n"
        f"`{redeem_code}`\n"
        f"[x{redemption_count} ᴜsᴇs]\n\n"
        f"{WAIFU}: {character_name}\n"
        f"Rarity: {character_rarity_sign} {character_rarity}"
    )

@app.on_message(Command("redeem") & command_filter)
@warned_user_filter
async def redeem_code_handler(client: Client, message: Message):
    if len(message.command) < 2:
        await message.reply("Usᴀɢᴇ: /ʀᴇᴅᴇᴇᴍ ᴄᴏᴅᴇ")
        return

    user_id = message.from_user.id
    redeem_code = message.command[1]

    # Fetch the redeem code details from the database
    code_details = await find_redeem_code(redeem_code)
    if not code_details:
        await message.reply("Iɴᴠᴀʟɪᴅ ʀᴇᴅᴇᴇᴍ ᴄᴏᴅᴇ.")
        return

    # Check if the user has already redeemed this code
    if user_id in code_details["redeemed_by"]:
        await message.reply("Yᴏᴜ ʜᴀᴠᴇ ᴀʟʀᴇᴀᴅʏ ʀᴇᴅᴇᴇᴍᴇᴅ ᴛʜɪs ᴄᴏᴅᴇ.")
        return

    # Check if the redemption count is still valid
    if len(code_details["redeemed_by"]) >= code_details["redemption_count"]:
        await message.reply("Tʜɪs ʀᴇᴅᴇᴇᴍ ᴄᴏᴅᴇ ʜᴀs ʀᴇᴀᴄʜᴇᴅ ɪᴛs ʟɪᴍɪᴛ.")
        return

    # Fetch the character details
    character = await get_character_details(code_details["character_id"])
    if not character:
        await message.reply(f"Tʜᴇ {WAIFU} ᴀssᴏᴄɪᴀᴛᴇᴅ ᴡɪᴛʜ ᴛʜɪs ᴄᴏᴅᴇ ᴅᴏᴇs ɴᴏᴛ ᴇxɪsᴛ.")
        return
        
    # Double-check that the character is not an IPL 2025 player
    if character.get("event") == "IPL 2025":
        await message.reply(f"🚫 Error: This code is for an IPL 2025 {WAIFU} and cannot be redeemed.")
        # Invalidate the code
        await delete_redeem_code(redeem_code)
        return

    # Add the character to the user's collection
    await update_smashed_image(user_id, code_details["character_id"], message.from_user.mention)

    # Update the redeem code details in the database
    await update_redeem_code(redeem_code, user_id)

    # Send success message with character details
    rarity_sign = character.get("rarity_sign", "")
    rarity = character.get("rarity", "")
    anime = character.get("anime", "")
    name = character.get("name", "")
    
    await message.reply(
        f"**🎯 Look! You Redeemed A {rarity} {WAIFU}!!**\n\n"
        f"**✨ Name: {name}**\n"
        f"**{rarity_sign} Rarity: {rarity}**\n"
        f"**🍁 {ANIME}: {anime}**\n\n"
        f"**You can take a look at your collection using /mycollection.**"
    )
    