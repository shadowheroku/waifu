import time
from Bot import app , Command
from Bot.database.grabtokendb import add_grab_token, cann_claim_gt, update_claim_time_gt
from Bot.utils import command_filter, warned_user_filter
from Bot.errors import capture_and_handle_error


DAILY_REWARD = 3000
WEEKLY_REWARD = 15000
MONTHLY_REWARD = 30000


DAILY_COOLDOWN = 24 * 60 * 60  
WEEKLY_COOLDOWN = 7 * 24 * 60 * 60  
MONTHLY_COOLDOWN = 30 * 24 * 60 * 60  

async def can_claim(user_id, claim_type):


    last_claim = await cann_claim_gt(user_id, claim_type)
    
    if not last_claim:
        return True  
    
    now = time.time()
    if claim_type == "daily":
        cooldown_period = DAILY_COOLDOWN
    elif claim_type == "weekly":
        cooldown_period = WEEKLY_COOLDOWN
    elif claim_type == "monthly":
        cooldown_period = MONTHLY_COOLDOWN
    
    return now - last_claim["last_claim_time"] > cooldown_period

async def update_claim_time(user_id, claim_type):
    """Update the last claim time for the user."""
    await update_claim_time_gt(user_id, claim_type)

@app.on_message(Command("daily") & command_filter)
@capture_and_handle_error
@warned_user_filter
async def daily_command(client, message):
    user_id = message.from_user.id
    user_name = message.from_user.first_name
    
    if await can_claim(user_id, "daily"):
        await add_grab_token(user_id, DAILY_REWARD, user_name)
        await update_claim_time(user_id, "daily")
        await message.reply_text(f"✅ ʏᴏᴜ ʜᴀᴠᴇ ꜱᴜᴄᴄᴇꜱꜱꜰᴜʟʟʏ ᴄʟᴀɪᴍᴇᴅ ʏᴏᴜʀ ᴅᴀɪʟʏ ʀᴇᴡᴀʀᴅ ᴏꜰ {DAILY_REWARD} ɢʀᴀʙ-ᴛᴏᴋᴇɴꜱ!")
    else:
        await message.reply_text(f"✖ ʏᴏᴜ ʜᴀᴠᴇ ᴀʟʀᴇᴀᴅʏ ᴄʟᴀɪᴍᴇᴅ ʏᴏᴜʀ ᴅᴀɪʟʏ ʀᴇᴡᴀʀᴅ!")

@app.on_message(Command("weekly") & command_filter)
@capture_and_handle_error
@warned_user_filter
async def weekly_command(client, message):
    user_id = message.from_user.id
    user_name = message.from_user.first_name
    
    if await can_claim(user_id, "weekly"):
        await add_grab_token(user_id, WEEKLY_REWARD, user_name)
        await update_claim_time(user_id, "weekly")
        await message.reply_text(f"✅ ʏᴏᴜ ʜᴀᴠᴇ ꜱᴜᴄᴄᴇꜱꜱꜰᴜʟʟʏ ᴄʟᴀɪᴍᴇᴅ ʏᴏᴜʀ ᴡᴇᴇᴋʟʏ ʀᴇᴡᴀʀᴅ ᴏꜰ {WEEKLY_REWARD} ɢʀᴀʙ-ᴛᴏᴋᴇɴꜱ!")
    else:
        await message.reply_text(f"✖ ʏᴏᴜ ʜᴀᴠᴇ ᴀʟʀᴇᴀᴅʏ ᴄʟᴀɪᴍᴇᴅ ʏᴏᴜʀ ᴡᴇᴇᴋʟʏ ʀᴇᴡᴀʀᴅ!")

@app.on_message(Command("monthly") & command_filter)
@capture_and_handle_error
@warned_user_filter
async def monthly_command(client, message):
    user_id = message.from_user.id
    user_name = message.from_user.first_name
    
    if await can_claim(user_id, "monthly"):
        await add_grab_token(user_id, MONTHLY_REWARD, user_name)
        await update_claim_time(user_id, "monthly")
        await message.reply_text(f"✅ ʏᴏᴜ ʜᴀᴠᴇ ꜱᴜᴄᴄᴇꜱꜱꜰᴜʟʟʏ ᴄʟᴀɪᴍᴇᴅ ʏᴏᴜʀ ᴍᴏɴᴛʜʟʏ ʀᴇᴡᴀʀᴅ ᴏꜰ {MONTHLY_REWARD} ɢʀᴀʙ-ᴛᴏᴋᴇɴꜱ!")
    else:
        await message.reply_text(f"✖ ʏᴏᴜ ʜᴀᴠᴇ ᴀʟʀᴇᴀᴅʏ ᴄʟᴀɪᴍᴇᴅ ʏᴏᴜʀ ᴍᴏɴᴛʜʟʏ ʀᴇᴡᴀʀᴅ!")

