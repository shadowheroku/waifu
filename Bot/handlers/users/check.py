from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from Bot.database.smashdb import get_chat_smashers
from Bot.database.leaderboarddb import get_global_top_smashers
from Bot.database.characterdb import get_character_check_details
from pyrogram.enums import ParseMode
from Bot import app, Command
from Bot.utils import command_filter, warned_user_filter
from pyrogram.handlers import CallbackQueryHandler
from Bot.errors import capture_and_handle_error
from texts import WAIFU , ANIME

# Fetch user names function
async def fetch_user_names(client, user_ids):
    user_mentions = {}
    for user_id in user_ids:
        try:
            user = await client.get_users(user_id)
            user_mentions[user.id] = user.mention
        except Exception as e:
            continue  # Skip this user if an exception occurs
    return user_mentions

@app.on_message(Command("check") & filters.group & command_filter)
@warned_user_filter
@capture_and_handle_error
async def check_character(client: Client, message: Message):
    if len(message.command) < 2:
        await message.reply(f"🔍 ᴘʟᴇᴀsᴇ ᴘʀᴏᴠɪᴅᴇ ᴛʜᴇ {WAIFU} ɪᴅ ᴛᴏ ᴄʜᴇᴄᴋ.")
        return

    character_id = message.command[1]

    x = await message.reply_text("🔍")
    
    result = await get_character_check_details(character_id)
    if not result:
        await message.reply(f"{WAIFU} ᴅᴇᴛᴀɪʟs nᴏᴛ ғᴏᴜɴᴅ.")
        return

    character = result["character"]
    unique_user_count = result["unique_user_count"]

    # Create the caption
    caption = (
        f"👤**Name**: **{character['name']}**\n"
        f"{character['rarity_sign']} **Rarity**: **{character['rarity']}**\n"
        f"🤝**{ANIME}**: **{character['anime']}**\n\n"
        f"🆔 **ID**: **{character['id']}**\n\n"
        f"☘️ ɢʟᴏʙᴀʟʟʏ ᴄᴏʟʟᴇᴄᴛᴇᴅ: {unique_user_count} ᴛɪᴍᴇs"
    )

    # Create inline keyboard with the "Smashers" button
    keyboard = InlineKeyboardMarkup(
        [[InlineKeyboardButton("👥 sʜᴏᴡ ᴄᴏʟʟᴇᴄᴛᴇʀꜱ ʜᴇʀᴇ", callback_data=f"show_smashers_{character_id}")],
        [InlineKeyboardButton("🏆 ᴛᴏᴘ ᴄᴏʟʟᴇᴄᴛᴇʀꜱ", callback_data=f"top_smashers_{character_id}")]]
    )

    # Send the media with the caption and the button
    if character.get("is_video", False):
        await x.delete()
        await client.send_video(
            chat_id=message.chat.id,
            video=character["video_url"],
            caption=caption,
            reply_markup=keyboard
        )
    else:
        await x.delete()
        await client.send_photo(
            chat_id=message.chat.id,
            photo=character["img_url"],
            caption=caption,
            reply_markup=keyboard
        )

@capture_and_handle_error
async def show_smashers(client: Client, callback_query: CallbackQuery):
    character_id = callback_query.data.split('_')[2]
    chat_id = callback_query.message.chat.id

    # Get smashers using the new database function
    smashers = await get_chat_smashers(client, chat_id, character_id)

    # Fetch user names
    user_mentions = await fetch_user_names(client, [smasher["user_id"] for smasher in smashers])
    smasher_text = "\n".join([f"{user_mentions[smasher['user_id']]} --> {smasher['count']}" for smasher in smashers])

    # Edit the message with smashers details
    await callback_query.edit_message_text(
        callback_query.message.caption + "\n\n" + "ᴄᴏʟʟᴇᴄᴛᴇʀꜱ ʜᴇʀᴇ━━━" + "\n" + smasher_text,
        parse_mode=ParseMode.HTML
    )

@capture_and_handle_error
async def show_top_smashers(client: Client, callback_query: CallbackQuery):
    await callback_query.answer()
    try:
        character_id = callback_query.data.split('_')[2]

        # Get top smashers using the new database function
        top_smashers = await get_global_top_smashers(character_id)

        # Fetch user names for top smashers
        user_ids = [user_id for user_id, _ in top_smashers]
        user_mentions = await fetch_user_names(client, user_ids)

        # Filter out users that could not be fetched (Unknown Users)
        top_smasher_text = "\n".join(
            [f"- {user_mentions[user_id]} [x{count}]" for user_id, count in top_smashers if user_id in user_mentions]
        )

        # Edit the message with the top smashers details
        await callback_query.edit_message_text(
            f"ᴛᴏᴘ ᴄᴏʟʟᴇᴄᴛᴇʀꜱ ғᴏʀ ᴛʜɪs {WAIFU}:.\n\n{top_smasher_text}",
            parse_mode=ParseMode.HTML
        )
    except Exception as e:
        print("ᴀn ᴜnᴋnᴏᴡn ᴇʀʀᴏʀ ᴏᴄᴄᴜʀʀᴇᴅ.")

# Corrected regex pattern
app.add_handler(CallbackQueryHandler(show_top_smashers, filters.regex(r"^top_smashers_")))
app.add_handler(CallbackQueryHandler(show_smashers, filters.regex(r"^show_smashers_")))
