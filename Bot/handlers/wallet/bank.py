from pyrogram import filters
from Bot import app , Command
from Bot.database.grabtokendb import decrease_grab_token, add_grab_token
from Bot.database.bankdb import deposit_to_bank, withdraw_from_bank
from Bot.database.grabtokendb import transfer_grabtoken
from Bot.utils import command_filter, warned_user_filter
from Bot.errors import capture_and_handle_error

@app.on_message(Command("deposit") & command_filter)
@capture_and_handle_error
@warned_user_filter
async def deposit_command(client, message):
    user_id = message.from_user.id
    try:
        amount = int(message.command[1])
    except (IndexError, ValueError):
        await message.reply_text("✖ ᴘʟᴇᴀsᴇ ᴘʀᴏᴠɪᴅᴇ ᴀ ᴠᴀʟɪᴅ ᴀᴍᴏᴜɴᴛ.")
        return

    if await decrease_grab_token(user_id, amount):
        await deposit_to_bank(user_id, amount)
        await message.reply_text(f"✅ sᴜᴄᴄᴇssғᴜʟʟʏ ᴅᴇᴘᴏsɪᴛᴇᴅ {amount} ɢʀᴀʙ-ᴛᴏᴋᴇɴ ᴛᴏ ʏᴏᴜʀ ʙᴀɴᴋ.")
    else:
        await message.reply_text("✖ ɴᴏᴛ ᴇɴᴏᴜɢʜ ɢʀᴀʙ-ᴛᴏᴋᴇɴ ᴛᴏ ᴅᴇᴘᴏsɪᴛ.")

@app.on_message(Command("withdraw") & command_filter)
@capture_and_handle_error
@warned_user_filter
async def withdraw_command(client, message):
    user_id = message.from_user.id
    try:
        amount = int(message.command[1])
    except (IndexError, ValueError):
        await message.reply_text("✖ ᴘʟᴇᴀsᴇ ᴘʀᴏᴠɪᴅᴇ ᴀ ᴠᴀʟɪᴅ ᴀᴍᴏᴜɴᴛ.")
        return

    if await withdraw_from_bank(user_id, amount):
        await add_grab_token(user_id, amount)
        await message.reply_text(f"✅ sᴜᴄᴄᴇssғᴜʟʟʏ ᴡɪᴛʜᴅʀᴇᴡ {amount} ɢʀᴀʙ-ᴛᴏᴋᴇɴ ғʀᴏᴍ ʏᴏᴜʀ ʙᴀɴᴋ.")
    else:
        await message.reply_text("✖ ɴᴏᴛ ᴇɴᴏᴜɢʜ ʙᴀɴᴋ ʙᴀʟᴀɴᴄᴇ ᴛᴏ ᴡɪᴛʜᴅʀᴀᴡ.")

@app.on_message(Command("pay") & filters.reply & command_filter)
@capture_and_handle_error
@warned_user_filter
async def pay_command(client, message):
    from_user_id = message.from_user.id

    # Ensure the command is a reply
    if not message.reply_to_message:
        await message.reply_text("✖ ᴘʟᴇᴀsᴇ ʀᴇᴘʟʏ ᴛᴏ ᴀ ᴜsᴇʀ's ᴍᴇssᴀɢᴇ ᴛᴏ ᴘᴀʏ ᴛʜᴇᴍ.")
        return

    to_user_id = message.reply_to_message.from_user.id

    # Check if user is trying to pay themselves
    if from_user_id == to_user_id:
        await message.reply_text("✖ ʏᴏᴜ ᴄᴀɴ'ᴛ ᴘᴀʏ ʏᴏᴜʀsᴇʟғ.")
        return

    try:
        amount = int(message.command[1])  # Grab the amount from the command
    except (IndexError, ValueError):
        await message.reply_text("✖ ᴘʟᴇᴀsᴇ ᴘʀᴏᴠɪᴅᴇ ᴀ ᴠᴀʟɪᴅ ᴀᴍᴏᴜɴᴛ ᴛᴏ ᴘᴀʏ.")
        return

    if amount <= 0:
        await message.reply_text("✖ ᴘʟᴇᴀsᴇ ᴘᴀʏ ᴀᴛ ʟᴇᴀsᴛ 1 ɢʀᴀʙ-ᴛᴏᴋᴇɴ.")
        return

    # Try to transfer the tokens
    if await transfer_grabtoken(from_user_id, to_user_id, amount):
        await message.reply_text(f"✅ sᴜᴄᴄᴇssғᴜʟʟʏ ᴘᴀɪᴅ {amount} ɢʀᴀʙ-ᴛᴏᴋᴇɴ ᴛᴏ {message.reply_to_message.from_user.first_name}!")
    else:
        await message.reply_text("✖ ɴᴏᴛ ᴇɴᴏᴜɢʜ ʙᴀʟᴀɴᴄᴇ ᴛᴏ ᴄᴏᴍᴘʟᴇᴛᴇ ᴛʜᴇ ᴘᴀʏᴍᴇɴᴛ.")