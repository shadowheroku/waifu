import time
from pyrogram import filters
from Bot import app , Command
from Bot.database.grabtokendb import add_grab_token
from Bot.utils import command_filter, warned_user_filter

# In-memory storage to track cooldowns
user_cooldowns = {}

@app.on_message(Command("bowl") & command_filter)
@warned_user_filter
async def bowl_command(client, message):
    user_id = message.from_user.id
    user_name = message.from_user.first_name  # Extract user's first name

    current_time = time.time()

    # Check if user is already on cooldown
    if user_id in user_cooldowns:
        cooldown_end = user_cooldowns[user_id]
        if current_time < cooldown_end:
            cooldown_time_left = round(cooldown_end - current_time)
            await message.reply_text(
                f"✖ ᴘʟᴇᴀsᴇ ᴡᴀɪᴛ {cooldown_time_left} sᴇᴄᴏɴᴅs ᴛᴏ ʙᴇ ᴀʙʟᴇ ᴛᴏ ᴜsᴇ /bowl ᴀɢᴀɪɴ !!"
            )
            return

    # Set a new cooldown before processing the command
    user_cooldowns[user_id] = current_time + 60

    bowl_message = await app.send_dice(chat_id=message.chat.id, emoji="🎳")
    
    time.sleep(2)

    if bowl_message.dice.value in [5, 6]:
        await add_grab_token(user_id, 150, user_name=user_name)  # Pass user_name to add_grab_token
        result_message = f"🎳 sᴛʀɪᴋᴇ! ʏᴏᴜ ᴡᴏɴ 150 ɢʀᴀʙ-ᴛᴏᴋᴇɴ!"
    else:
        result_message = f"🎳 ɴᴏ sᴛʀɪᴋᴇ ᴛʜɪs ᴛɪᴍᴇ! ᴛʀʏ ᴀɢᴀɪɴ ʟᴀᴛᴇʀ."

    await message.reply_text(result_message)
