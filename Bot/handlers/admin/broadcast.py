import asyncio
from pyrogram import filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from Bot.database.collectiondb import get_groups_and_users
from Bot import app, Command
from Bot.errors import capture_and_handle_error
from Bot.config import OWNER_ID, ADI


APPROVED_USERS = [OWNER_ID, ADI]  

def is_approved_user(user_id):
    return user_id in APPROVED_USERS


cancel_broadcast = False


async def broadcast_message(client, message, groups, users):
    global cancel_broadcast
    user_count, group_count = 0, 0

    # Forward to all groups
    for group_id in groups:
        if cancel_broadcast:
            break
        try:
            await message.forward(group_id)
            group_count += 1
            await asyncio.sleep(1.5)  
        except Exception as e:
            if "FloodWait" in str(e):
                wait_time = int(str(e).split()[1])
                await asyncio.sleep(wait_time)
            else:
                continue
    
    # Forward to all users
    for user_id in users:
        if cancel_broadcast:
            break
        try:
            await message.forward(user_id)
            user_count += 1
            await asyncio.sleep(1.5)  # Add delay to slow down broadcast speed
        except Exception as e:
            if "FloodWait" in str(e):
                wait_time = int(str(e).split()[1])
                await asyncio.sleep(wait_time)
            else:
                continue

    return user_count, group_count

# Cancel callback
async def cancel_broadcast_callback(client, query):
    global cancel_broadcast
    if not is_approved_user(query.from_user.id):
        await query.answer("🚫 You do not have permission to cancel the broadcast.", show_alert=True)
        return

    cancel_broadcast = True
    await query.message.edit_text("🚫 ᴛʜᴇ ʙʀᴏᴀᴅᴄᴀsᴛ ʜᴀs ʙᴇᴇɴ ᴄᴀɴᴄᴇʟʟᴇᴅ.")
    await query.answer("Broadcast cancelled.", show_alert=True)

@app.on_message(Command("broadcast") & filters.user(APPROVED_USERS) & filters.reply )
@capture_and_handle_error
async def start_broadcast(client, message):
    global cancel_broadcast
    cancel_broadcast = False  # Reset cancellation

    # Get groups and users from the database
    groups, users = await get_groups_and_users()

    # Send broadcast start message with cancel button
    cancel_button = InlineKeyboardMarkup([[InlineKeyboardButton("🚫 ᴄᴀɴᴄᴇʟ ʙʀᴏᴀᴅᴄᴀsᴛ", callback_data="cancel_broadcast")]])
    broadcast_message_status = await message.reply_text(
        "📡 ʙʀᴏᴀᴅᴄᴀsᴛɪɴɢ ɪɴ ᴘʀᴏɢʀᴇss...", reply_markup=cancel_button
    )

    # Start broadcasting (forwarding the message)
    user_count, group_count = await broadcast_message(client, message.reply_to_message, groups, users)

    # Edit the final broadcast message with statistics
    if not cancel_broadcast:
        await broadcast_message_status.edit_text(
            f"✅ ʙʀᴏᴀᴅᴄᴀsᴛ ᴄᴏᴍᴘʟᴇᴛᴇᴅ!\n👥 ᴜsᴇʀs ʀᴇᴀᴄʜᴇᴅ: {user_count}\n👥 ɢʀᴏᴜᴘs ʀᴇᴀᴄʜᴇᴅ: {group_count}"
        )

@app.on_callback_query(filters.regex("cancel_broadcast"))
@capture_and_handle_error
async def on_cancel_callback(client, query):
    await cancel_broadcast_callback(client, query)

