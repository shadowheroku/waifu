import time
from pyrogram import filters
from Bot import app , Command
from Bot.database.grabtokendb import add_grab_token
from Bot.utils import command_filter, warned_user_filter

# In-memory dictionary to store user cooldowns
user_cooldowns = {}

@app.on_message(Command("roll") & command_filter)
@warned_user_filter
async def roll_command(client, message):
    user_id = message.from_user.id
    user_name = message.from_user.first_name

    current_time = time.time()

    if user_id in user_cooldowns and current_time < user_cooldowns[user_id]:
        cooldown_time_left = round(user_cooldowns[user_id] - current_time)
        await message.reply_text(f"✖ ᴘʟᴇᴀsᴇ ᴡᴀɪᴛ {cooldown_time_left} sᴇᴄᴏɴᴅs ᴛᴏ ᴜsᴇ /roll ᴀɢᴀɪɴ!")
        return

    if len(message.command) != 2 or not message.command[1].isdigit() or int(message.command[1]) not in range(1, 7):
        await message.reply_text("ℹ ᴘʟᴇᴀsᴇ sᴘᴇᴄɪғʏ ᴀ ɴᴜᴍʙᴇʀ ʙᴇᴛᴡᴇᴇɴ 1 ᴀɴᴅ 6, ʟɪᴋᴇ ᴛʜɪs: /roll 4")
        return

    user_cooldowns[user_id] = current_time + 120  # Set cooldown
    chosen_number = int(message.command[1])
    dice_message = await app.send_dice(chat_id=message.chat.id, emoji="🎲")
    time.sleep(2.5)

    if dice_message.dice.value == chosen_number:
        await add_grab_token(user_id, 200, user_name=user_name)
        result_message = f"🎲 ᴛʜᴇ ᴅɪᴄᴇ ʀᴏʟʟᴇᴅ : {dice_message.dice.value}\n🎉 ʏᴏᴜ ᴡᴏɴ 200 ɢʀᴀʙ-ᴛᴏᴋᴇɴ!"
    else:
        result_message = f"🎲 ᴛʜᴇ ᴅɪᴄᴇ ʀᴏʟʟᴇᴅ : {dice_message.dice.value}\nᴏᴏᴘs! ʙᴇᴛᴛᴇʀ ʟᴜᴄᴋ ɴᴇxᴛ ᴛɪᴍᴇ."

    await message.reply_text(result_message)

