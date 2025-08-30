# from pyrogram import Client, filters
# from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
# from datetime import datetime, timedelta
# import asyncio

# from Bot.database.characterdb import get_random_character
# from Bot.database.smashdb import update_smashed_image
# from Bot.config import OWNER_ID
# from Bot import app
# from Bot.utils import warned_user_filter, command_filter
# from Bot.errors import capture_and_handle_error

# # Constants
# CLAIM_LIMIT = 2
# CLAIM_INTERVAL = timedelta(minutes=10)
# DAILY_RESET_INTERVAL = timedelta(hours=24)
# MANDATORY_LINK = "https://t.me/seed_coin_bot/app?startapp=5630057244"

# # In-memory caches
# user_claim_cache = {}  # Stores user claim times, remaining claims, and link status
# active_claim_locks = {}


# @app.on_message(filters.command("claim") & command_filter)
# @warned_user_filter
# @capture_and_handle_error
# async def claim(client: Client, message: Message):
#     user_id = message.from_user.id
#     user_data = user_claim_cache.get(user_id, {
#         "last_claim_time": None,
#         "remaining_claims": CLAIM_LIMIT,
#         "link_clicked": False,
#         "daily_reset": datetime.utcnow() - DAILY_RESET_INTERVAL,
#         "claim_attempt": 0,
#     })

#     # Reset daily claim limits if the reset interval has passed
#     if datetime.utcnow() - user_data["daily_reset"] >= DAILY_RESET_INTERVAL:
#         user_data["remaining_claims"] = CLAIM_LIMIT
#         user_data["daily_reset"] = datetime.utcnow()
#         user_data["claim_attempt"] = 0

#     # Increment claim attempt count
#     user_data["claim_attempt"] += 1

#     # Handle alternate claim/link flow
#     if user_data["claim_attempt"] % 2 == 1:  # Odd attempts
#         keyboard = InlineKeyboardMarkup(
#             [[InlineKeyboardButton("Click Here to Unlock", url=MANDATORY_LINK)]]
#         )
#         await message.reply(
#             "⚠️ **You must click the link below before claiming. Once done, try /claim again.\n\nNote -: URL Has Been Updated , Now If You Don't Click The Url Then Your Reward Will Be Dedecuted!!**",
#             reply_markup=keyboard,
#         )
#         user_claim_cache[user_id] = user_data
#         return

#     # Prevent multiple simultaneous claims
#     if user_id in active_claim_locks:
#         await message.reply("⏳ **Claim in progress... Please wait.**")
#         return

#     active_claim_locks[user_id] = True

#     try:
#         # Owner bypasses claim interval and limits
#         if user_id != OWNER_ID:

#             # Check if user has remaining claims
#             if user_data["remaining_claims"] <= 0:
#                 await message.reply("🚫 **You have reached your daily claim limit. Try again tomorrow.**")
#                 return

#             # Check claim cooldown
#             last_claim_time = user_data["last_claim_time"]
#             if last_claim_time and datetime.utcnow() - last_claim_time < CLAIM_INTERVAL:
#                 time_remaining = last_claim_time + CLAIM_INTERVAL - datetime.utcnow()
#                 minutes, seconds = divmod(time_remaining.total_seconds(), 60)
#                 await message.reply(
#                     f"⏳ **You can claim again in {int(minutes)}m {int(seconds)}s.**"
#                 )
#                 return

#         # Emoji animation
#         emoji_message = await message.reply("⚡️")
#         await asyncio.sleep(2)
#         await emoji_message.delete()

#         # Fetch a random character
#         random_character = await get_random_character()
#         if not random_character:
#             await message.reply(
#                 "🚫 No player available for claiming at the moment. Please try again later."
#             )
#             return

#         # Update user's last claim time and remaining claims
#         user_data["last_claim_time"] = datetime.utcnow()
#         user_data["remaining_claims"] -= 1
#         user_claim_cache[user_id] = user_data

#         # Prepare and send the message with the character's image and caption
#         img_url = random_character["img_url"]
#         user_mention = message.from_user.mention
#         caption = (
#             f"**🫧 {user_mention} you got a new player!**\n\n"
#             f"✨ **Name**: {random_character['name']}\n"
#             f"{random_character['rarity_sign']} **Rarity**: {random_character['rarity']}\n"
#             f"🍁 **Team**: {random_character['anime']}\n\n"
#             f"🆔: {random_character['id']}"
#         )

#         await client.send_photo(
#             chat_id=message.chat.id,
#             photo=img_url,
#             caption=caption,
#             reply_to_message_id=message.id,
#         )

#         # Update user's collection
#         await update_smashed_image(user_id, random_character["id"], message.from_user.first_name)

#     finally:
#         # Release the lock
#         active_claim_locks.pop(user_id, None)

