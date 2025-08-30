import random
import asyncio
from pyrogram import filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from Bot import app , Command
from Bot.database.grabtokendb import decrease_grab_token, add_grab_token
from Bot.utils import command_filter , warned_user_filter
import time

# In-memory storage for button clicks and cooldowns
user_bet_choices = {}
user_cooldowns = {}
COOLDOWN_DURATION = 60  # 60 seconds

# Button options
def generate_difficulty_buttons():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🟢 Easy", callback_data="bet_easy")],
        [InlineKeyboardButton("🟡 Medium", callback_data="bet_medium")],
        [InlineKeyboardButton("🔴 Hard", callback_data="bet_hard")]
    ])

@app.on_message(Command("bet") & command_filter)
@warned_user_filter
async def bet_command(client, message):
    user_id = message.from_user.id
    current_time = time.time()

    # Check if the user is in cooldown
    if user_id in user_cooldowns:
        time_since_last_bet = current_time - user_cooldowns[user_id]
        if time_since_last_bet < COOLDOWN_DURATION:
            remaining_time = int(COOLDOWN_DURATION - time_since_last_bet)
            await message.reply_text(f"✖ ʏᴏᴜ ᴄᴀɴ ᴘʟᴀᴄᴇ ᴀɴᴏᴛʜᴇʀ ʙᴇᴛ ɪɴ {remaining_time} sᴇᴄᴏɴᴅs!")
            return

    try:
        # Extract bet amount and choice (heads/tails)
        amount = int(message.command[1])
        choice = message.command[2].lower()

        if amount <= 0:
            await message.reply_text("Please Choose A Positive Amount !!")
            return

        if choice not in ["heads", "tails", "h", "t"]:
            await message.reply_text("✖ ᴘʟᴇᴀsᴇ ᴄʜᴏᴏsᴇ ʜᴇᴀᴅs ᴏʀ ᴛᴀɪʟs! (ʜ/ᴛ)")
            return
    except (IndexError, ValueError):
        await message.reply_text("✖ ᴘʟᴇᴀsᴇ ᴘʀᴏᴠɪᴅᴇ ᴀ ᴠᴀʟɪᴅ ʙᴇᴛ ᴀᴍᴏᴜɴᴛ ᴀɴᴅ ᴄʜᴏɪᴄᴇ! Example: `/bet 100 heads`")
        return

    # Check if user has enough tokens to bet
    if not await decrease_grab_token(user_id, amount):
        await message.reply_text("✖ ɴᴏᴛ ᴇɴᴏᴜɢʜ ɢʀᴀʙ-ᴛᴏᴋᴇɴ ᴛᴏ ᴘʟᴀᴄᴇ ᴛʜɪs ʙᴇᴛ.")
        return

    # Store the user's bet and update their last bet time
    user_bet_choices[user_id] = {"amount": amount, "choice": choice}
    user_cooldowns[user_id] = current_time  # Update cooldown

# Check restrictions for difficulties based on amount
    if amount > 100000:
        await message.reply_text(
            "🪙 **ᴄʜᴏᴏsᴇ ʏᴏᴜʀ ᴅɪғғɪᴄᴜʟᴛʏ**:\n"
            "⚠ ʏᴏᴜ ᴄᴀɴ'ᴛ sᴇʟᴇᴄᴛ ᴇᴀsʏ ᴏʀ ᴍᴇᴅɪᴜᴍ ғᴏʀ ʙᴇᴛs ᴏᴠᴇʀ 100000 ɢʀᴀʙ-ᴛᴏᴋᴇɴs!\n\n"
            "💡 **ᴅɪғғɪᴄᴜʟᴛʏ ᴅᴇᴛᴀɪʟs**:\n"
            "🟢 **ᴇᴀsʏ**: ᴡɪɴ ᴍᴜʟᴛɪᴘʟɪᴇʀ ×1.5\n"
            "🟡 **ᴍᴇᴅɪᴜᴍ**: ᴡɪɴ ᴍᴜʟᴛɪᴘʟɪᴇʀ ×3\n"
            "🔴 **ʜᴀʀᴅ**: ᴡɪɴ ᴍᴜʟᴛɪᴘʟɪᴇʀ ×5 (ʜɪɢʜ ʀɪsᴋ, ʟᴏᴡ ᴄʜᴀɴᴄᴇ ᴏғ ᴡɪɴɴɪɴɢ!)",
            reply_markup=generate_difficulty_buttons()
        )
    elif amount > 30000:
        await message.reply_text(
            "🪙 **ᴄʜᴏᴏsᴇ ʏᴏᴜʀ ᴅɪғғɪᴄᴜʟᴛʏ**:\n"
            "⚠ ʏᴏᴜ ᴄᴀɴ'ᴛ sᴇʟᴇᴄᴛ ᴇᴀsʏ ғᴏʀ ʙᴇᴛs ᴏᴠᴇʀ 30000 ɢʀᴀʙ-ᴛᴏᴋᴇɴs!\n\n"
            "💡 **ᴅɪғғɪᴄᴜʟᴛʏ ᴅᴇᴛᴀɪʟs**:\n"
            "🟢 **ᴇᴀsʏ**: ᴡɪɴ ᴍᴜʟᴛɪᴘʟɪᴇʀ ×1.5\n"
            "🟡 **ᴍᴇᴅɪᴜᴍ**: ᴡɪɴ ᴍᴜʟᴛɪᴘʟɪᴇʀ ×3\n"
            "🔴 **ʜᴀʀᴅ**: ᴡɪɴ ᴍᴜʟᴛɪᴘʟɪᴇʀ ×5 (ʜɪɢʜ ʀɪsᴋ, ʟᴏᴡ ᴄʜᴀɴᴄᴇ ᴏғ ᴡɪɴɴɪɴɢ!)",
            reply_markup=generate_difficulty_buttons()
        )
    else:
        await message.reply_text(
            "🪙 **ᴄʜᴏᴏsᴇ ʏᴏᴜʀ ᴅɪғғɪᴄᴜʟᴛʏ**:\n\n"
            "💡 **ᴅɪғғɪᴄᴜʟᴛʏ ᴅᴇᴛᴀɪʟs**:\n"
            "🟢 **ᴇᴀsʏ**: ᴡɪɴ ᴍᴜʟᴛɪᴘʟɪᴇʀ ×1.5\n"
            "🟡 **ᴍᴇᴅɪᴜᴍ**: ᴡɪɴ ᴍᴜʟᴛɪᴘʟɪᴇʀ ×3\n"
            "🔴 **ʜᴀʀᴅ**: ᴡɪɴ ᴍᴜʟᴛɪᴘʟɪᴇʀ ×5 (ʜɪɢʜ ʀɪsᴋ, ʟᴏᴡ ᴄʜᴀɴᴄᴇ ᴏғ ᴡɪɴɴɪɴɢ!)",
            reply_markup=generate_difficulty_buttons()
        )
    

# Callback handler for bet difficulty
@app.on_callback_query(filters.regex(r"bet_"))
async def bet_difficulty_callback(client, callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    user_name = callback_query.from_user.first_name  # Extract user's first name

    # Ensure only the command initiator can select the difficulty
    if user_id not in user_bet_choices:
        await callback_query.answer("✖ ᴛʜɪs ʙᴜᴛᴛᴏɴ ɪsɴ'ᴛ ғᴏʀ ʏᴏᴜ!", show_alert=True)
        return

    bet_data = user_bet_choices[user_id]
    amount = bet_data["amount"]
    choice = bet_data["choice"]

    # Check bet amount and disable difficulties based on conditions
    if amount > 100000 and callback_query.data in ["bet_easy", "bet_medium"]:
        await callback_query.answer("✖ ʏᴏᴜ ᴄᴀɴ'ᴛ ᴄʜᴏᴏsᴇ ᴛʜɪs ᴅɪғғɪᴄᴜʟᴛʏ ғᴏʀ ʙᴇᴛs ᴏᴠᴇʀ 100000 ɢʀᴀʙ-ᴛᴏᴋᴇɴꜱ!", show_alert=True)
        return
    if amount > 30000 and callback_query.data == "bet_easy":
        await callback_query.answer("✖ ʏᴏᴜ ᴄᴀɴ'ᴛ ᴄʜᴏᴏsᴇ ᴇᴀsʏ ғᴏʀ ʙᴇᴛs ᴏᴠᴇʀ 30000 ɢʀᴀʙ-ᴛᴏᴋᴇɴꜱ!", show_alert=True)
        return

    # Delete the message with buttons
    await callback_query.message.delete()

    # Simulate coin flip and difficulty-based results
    difficulty = callback_query.data.split("_")[1]
    result_multiplier = {"easy": 1.5, "medium": 2, "hard": 3}[difficulty]
    win_chance = {"easy": 50, "medium": 25, "hard": 8}[difficulty]

    # Edit the message to show "Flipping the coin..."
    bet_message = await callback_query.message.reply_text("🪙 ꜰʟɪᴘᴘɪɴɢ ᴛʜᴇ ᴄᴏɪɴ...")

    # Delay to simulate flipping animation
    await asyncio.sleep(1)

    # Simulate coin toss result
    coin_result = random.choice(["heads", "tails"])

    # Edit the message to show the coin landed on heads/tails after 1 second
    await bet_message.edit_text(f"ᴄʜᴇᴄᴋɪɴɢ ᴛʜᴇ ʀᴇꜱᴜʟᴛꜱ !!")
    
    # Simulate win/loss based on difficulty
    if random.randint(1, 100) <= win_chance and coin_result.startswith(choice[0]):
        winnings = int(amount * result_multiplier)
        await add_grab_token(user_id, winnings , user_name=user_name)
        result_text = f"🎉 ʏᴏᴜ ᴡᴏɴ {winnings} ɢʀᴀʙ-ᴛᴏᴋᴇɴꜱ ᴡɪᴛʜ ᴀ {difficulty.capitalize()} ʙᴇᴛ!"
    else:
        result_text = "❌ ʏᴏᴜ ʟᴏꜱᴛ ᴛʜᴇ ʙᴇᴛ. ʙᴇᴛᴛᴇʀ ʟᴜᴄᴋ ɴᴇxᴛ ᴛɪᴍᴇ."

    # Final result message after 0.8 seconds
    await asyncio.sleep(0.8)
    await bet_message.edit_text(result_text)
    del user_bet_choices[user_id]