from pyrogram import Client , filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message
from datetime import datetime
import asyncio
from Bot import app , Command
from Bot.utils import command_filter, warned_user_filter
from Bot.handlers.shared import *
from Bot.database.smashdb import update_smashed_image
from Bot.database.characterdb import get_character_details
from Bot.database.groupdb import update_group_smash, update_daily_smash, update_total_smash_count
from texts import WAIFU , ANIME

smash_locks = {}


# Define the helper function
async def split_sentence(name):
    # You can customize this function to handle more specific splits based on your needs
    return name.split()

async def is_guess_true(name, waifu_names):
    """
    Check if the guessed name contains valid words from waifu_names and no unrelated words.
    """
    guessed_args = set(await split_sentence(name.lower()))
    unwanted_words = {"&", "and", "x"}  # Words to discard
    guessed_args -= unwanted_words  # Remove unwanted words from the guess

    for waifu_name in waifu_names:
        waifu_args = set(await split_sentence(waifu_name.lower()))
        waifu_args -= unwanted_words  # Remove unwanted words from waifu names
        
        # Ensure all guessed words are part of the waifu name and at least one match exists
        if guessed_args.issubset(waifu_args) and guessed_args & waifu_args:
            return True

    return False

# Update the hunt command
@app.on_message(Command("collect") & filters.group & command_filter)
@warned_user_filter
async def smash_image(client: Client, message: Message):
    group_id = message.chat.id
    user_id = message.from_user.id
    chat_name = message.chat.title  # Retrieve the chat name
    user_first_name = message.from_user.first_name  # Retrieve the user's first name
    chat_username = message.chat.username  # Retrieve the chat's username if available

    if group_id not in smash_locks:
        smash_locks[group_id] = asyncio.Lock()
    
    async with smash_locks[group_id]:
        drop = drop_details.get(group_id)

        if not drop:
            return

        if drop["smashed_by"]:
            smashed_user = await client.get_users(drop["smashed_by"])
            smashed_user_mention = smashed_user.mention if smashed_user else f"User ID: {drop['smashed_by']}"

            await message.reply(f"**ℹ Lᴀsᴛ {WAIFU} ᴡᴀs ᴀʟʀᴇᴀᴅʏ Collected ʙʏ {smashed_user_mention} !!**")
            return

        if len(message.command) < 2:
            dropped_image_link = drop.get("dropped_image_link", "")
        
            keyboard = InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            f"{WAIFU} 🔼", url=dropped_image_link
                        )
                    ]
                ]
            )
            
            await message.reply(
                f"Pʟᴇᴀsᴇ ɢᴜᴇss ᴛʜᴇ {WAIFU} ɴᴀᴍᴇ.",
                reply_markup=keyboard
            )
            return

        guessed_name = " ".join(message.command[1:]).strip().lower()
        today_date = datetime.utcnow().date().isoformat()

        character_name = drop["image_name"].strip().lower()
        character_name_parts = character_name.split()

        # Use the is_guess_true function to match the guessed name
        is_correct = await is_guess_true(guessed_name, [drop["image_name"]])

        if is_correct:
            await update_smashed_image(user_id, drop["image_id"], user_first_name)
            await update_drop(group_id, drop["image_id"], drop["image_name"], drop["image_url"], smashed_by=user_id)
           
            # Update all database records
            await update_group_smash(group_id, chat_name, chat_username)
            await update_daily_smash(user_id, today_date, user_first_name)
            await update_total_smash_count(user_id, user_first_name)

            character = await get_character_details(drop["image_id"])
            rarity_sign = character.get("rarity_sign", "")
            rarity = character.get("rarity", "")
            anime = character.get("anime", "")
            
            await message.react("⚡️" , big=True)
            await message.reply(
                f"**✅ Look You Collected A {rarity} {WAIFU} !!**\n\n"
                f"**👤 Name : {drop['image_name']}**\n"
                f"**{rarity_sign} Rarity : {rarity}**\n"
                f"**🤝 {ANIME} : {anime}**\n\n"
                f"**Yᴏᴜ Cᴀɴ Tᴀᴋᴇ A Lᴏᴏᴋ Aᴛ Yᴏᴜʀ Cᴏʟʟᴇᴄᴛɪᴏɴ Usɪɴɢ /mycollection**",
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            f"{user_first_name}'s Collection",
                            switch_inline_query_current_chat=f"collected.{user_id}"
                        )
                    ]
                ]
            )
        )
        else:
            dropped_image_link = drop.get("dropped_image_link", "")
            
            keyboard = InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            f"{WAIFU} 🔼", url=dropped_image_link
                        )
                    ]
                ]
            )
            
            await message.reply(
                f"**❌ Iɴᴄᴏʀʀᴇᴄᴛ ɢᴜᴇss -: {guessed_name} !**\n\n**Pʟᴇᴀsᴇ ᴛʀʏ ᴀɢᴀɪɴ...**",
                reply_markup=keyboard
            )