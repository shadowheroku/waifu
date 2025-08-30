from Bot import app , Command
from Bot.database.grabtokendb import get_user_balance
from Bot.database.bankdb import get_bank_balance
from Bot.utils import command_filter, warned_user_filter
from Bot.errors import capture_and_handle_error

@app.on_message(Command(["bal", "balance"]) & command_filter)
@capture_and_handle_error
@warned_user_filter
async def balance_command(client, message): 
    user_id = message.from_user.id

    # Fetch Grabtoken balance
    grabtoken_balance = await get_user_balance(user_id)
    
    # Fetch bank balance
    bank_balance = await get_bank_balance(user_id)

    # Send balance message to the user
    await message.reply_text(
        f"💸 ʏᴏᴜʀ ᴄᴜʀʀᴇɴᴛ ʙᴀʟᴀɴᴄᴇ (ɢʀᴀʙ-ᴛᴏᴋᴇɴꜱ):\n\n"
        f"• ᴡᴀʟʟᴇᴛ: {grabtoken_balance}\n"
        f"• 🏦 ʙᴀɴᴋ ʙᴀʟᴀɴᴄᴇ: {bank_balance}"
    )
