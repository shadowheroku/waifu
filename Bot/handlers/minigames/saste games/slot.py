import time
from pyrogram import filters
from Bot import app , Command
from Bot.database.grabtokendb import add_grab_token
from Bot.utils import command_filter, warned_user_filter

user_cooldowns = {}

@app.on_message(Command("slot") & command_filter)
@warned_user_filter
async def slot_command(client, message):
    user_id = message.from_user.id
    user_name = message.from_user.first_name

    current_time = time.time()

    if user_id in user_cooldowns and current_time < user_cooldowns[user_id]:
        cooldown_time_left = round(user_cooldowns[user_id] - current_time)
        await message.reply_text(f"✖ ᴘʟᴇᴀsᴇ ᴡᴀɪᴛ {cooldown_time_left} sᴇᴄᴏɴᴅs ᴛᴏ ᴜsᴇ /slot ᴀɢᴀɪɴ!")
        return

    user_cooldowns[user_id] = current_time + 60  # Set cooldown
    slot_message = await app.send_dice(chat_id=message.chat.id, emoji="🎰")
    time.sleep(2)

    dice_value = slot_message.dice.value

    if dice_value == 64:
        await add_grab_token(user_id, 1000, user_name=user_name)
        result_message = f"🎰 ᴊᴀᴄᴋᴘᴏᴛ! ʏᴏᴜ ᴡᴏɴ 1000 ɢʀᴀʙ-ᴛᴏᴋᴇɴ!"
    elif 40 <= dice_value < 64:
        await add_grab_token(user_id, 500, user_name=user_name)
        result_message = f"🎰 ᴄᴏɴɢʀᴀᴛs! ʏᴏᴜ ᴡᴏɴ 500 ɢʀᴀʙ-ᴛᴏᴋᴇɴ!"
    elif 20 <= dice_value < 40:
        await add_grab_token(user_id, 250, user_name=user_name)
        result_message = f"🎰 ɴɪᴄᴇ! ʏᴏᴜ ᴡᴏɴ 250 ɢʀᴀʙ-ᴛᴏᴋᴇɴ!"
    else:
        result_message = f"🎰 ɴᴏ ʟᴜᴄᴋ ᴛʜɪs ᴛɪᴍᴇ! ᴛʀʏ ᴀɢᴀɪɴ ʟᴀᴛᴇʀ."

    await message.reply_text(result_message)

