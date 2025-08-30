import time
from functools import wraps
import asyncio
from collections import defaultdict, deque
from aiocache import cached
from pyrogram import Client, filters
from pyrogram.types import Message, ChatMemberUpdated
from pyrogram.enums import ChatMemberStatus
from pyrogram.handlers import ChatMemberUpdatedHandler
from Bot import app, Command, glog
from Bot.utils import command_filter, warned_user_filter, warned_users, og_filter
from Bot.handlers.shared import (
    update_message_count, get_message_count, update_drop, 
   modify_image_for_unique_id
)
from Bot.database.characterdb import get_random_character, get_character_details
from Bot.database.privacydb import is_user_sudo
from Bot.database.groupdb import is_group_in_database, insert_new_group
from Bot.database.grabtokendb import add_grab_token
from Bot.config import OWNER_ID, SUPPORT_CHAT_ID, LOG_CHANNEL , DEFAULT_DROP_COUNT , MINIMUM_MEMBERS
from Bot.errors import capture_and_handle_error
from texts import WAIFU , ANIME

droplock = {"enabled": False}
message_timestamps = defaultdict(dict)
ignore_duration = 10 * 60 
group_locks = {}
group_last_messages = defaultdict(lambda: deque(maxlen=8)) 
drop_debounce_time = 1.0  


def droplock_decorator(func):
    @wraps(func)
    async def wrapper(client, message: Message, *args, **kwargs):
        if droplock.get("enabled", False):
            return  
        return await func(client, message, *args, **kwargs)
    return wrapper

@app.on_message(Command("droplock") & filters.user(OWNER_ID))
async def toggle_droplock(client: Client, message: Message):

    if len(message.command) < 2:
        await message.reply("Please specify 'on' or 'off'.")
        return


    action = message.command[1].lower()
    if action == "on":
        droplock["enabled"] = True
        await message.reply("**Droplock has been enabled. Message counting is paused.**")
    elif action == "off":
        droplock["enabled"] = False
        await message.reply("**Droplock has been disabled. Message counting is resumed.**")
    else:
        await message.reply("Invalid argument. Use 'on' or 'off'.")

@capture_and_handle_error
async def handle_new_member(client: Client, member_update: ChatMemberUpdated):

    if (member_update.new_chat_member and 
        member_update.new_chat_member.user.is_self and
        (not member_update.old_chat_member or 
         member_update.old_chat_member.status == ChatMemberStatus.LEFT)):
        
        group_id = member_update.chat.id
        group_title = member_update.chat.title
        group_username = f"@{member_update.chat.username}" if member_update.chat.username else "N/A"
        added_by_user_id = member_update.from_user.id
        added_by_username = member_update.from_user.username if member_update.from_user.username else "N/A"
        added_by_first_name = member_update.from_user.first_name
        
        try:
            members_count = await client.get_chat_members_count(group_id)
            

            if members_count < MINIMUM_MEMBERS:
                await client.send_message(
                    chat_id=group_id,
                    text="🚫 This group can't afford me! I'm leaving now."
                )
                await client.leave_chat(group_id)
                return

            if not await is_group_in_database(group_id):
                await insert_new_group(group_id, group_title, group_username, members_count)


            await update_message_count(group_id, 100, 0)
            await client.send_message(
                group_id, 
                f"💬 ʀᴀɴᴅᴏᴍ {WAIFU} ᴡɪʟʟ ʙᴇ ᴅʀᴏᴘᴘᴇᴅ ʜᴇʀᴇ ᴇᴠᴇʀʏ 60 ᴍᴇssᴀɢᴇs.\n\nʏᴏᴜ ᴄᴀɴ ᴄʜᴀɴɢᴇ ᴅʀᴏᴘᴛɪᴍᴇ ᴜsɪɴɢ /droptime !!"
            )


            await client.send_message(
                SUPPORT_CHAT_ID,
                f"🏠 **Added To New Group**\n\n"
                f"🆔 **Group ID:** `{group_id}`\n"
                f"📛 **Group Name:** {group_title}\n"
                f"✳ **Group Username:** {group_username}\n"
                f"👤 **Added By:** `{added_by_first_name}`\n"
                f"🔗 **Username:** @{added_by_username}\n"
                f"📊 **Members Count:** `{members_count}`"
            )
        except Exception as e:
            print(f"Error in handle_new_member: {e}")


app.add_handler(ChatMemberUpdatedHandler(handle_new_member))

@cached(ttl=300)  # Cache for 5 minutes
async def is_special(client: Client, chat_id: int, user_id: int) -> bool:
    if user_id == OWNER_ID or await is_user_sudo(user_id):
        return True
    return False

@app.on_message(Command("droptime") & filters.group & command_filter)
@warned_user_filter
async def droptime(client: Client, message: Message):

    group_id = message.chat.id
    user_id = message.from_user.id
    user_first_name = message.from_user.first_name

    if len(message.command) < 2:
        count_doc = await get_message_count(group_id)
        
        if count_doc:
            current_droptime = count_doc["msg_count"]
            await message.reply(f"**Tʜᴇ ᴄᴜʀʀᴇɴᴛ ᴅʀᴏᴘᴛɪᴍᴇ ɪs sᴇᴛ ᴛᴏ {current_droptime} ᴍᴇssᴀɢᴇs.**")
        else:
            await message.reply("**Dʀᴏᴘᴛɪᴍᴇ ɪs ɴᴏᴛ sᴇᴛ ғᴏʀ ᴛʜɪs ɢʀᴏᴜᴘ ʏᴇᴛ.**")
        return


    try:
        msg_count = int(message.command[1])
    except ValueError:
        await message.reply("❌ **Pʟᴇᴀsᴇ ᴘʀᴏᴠɪᴅᴇ ᴀ ᴠᴀʟɪᴅ ɴᴜᴍʙᴇʀ ғᴏʀ ᴍᴇssᴀɢᴇ ᴄᴏᴜɴᴛ.")
        return


    special_user = await is_special(client, group_id, user_id)
    
    if not special_user:
        chat_member = await client.get_chat_member(group_id, user_id)
        user_status = chat_member.status
        
        if user_status not in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]:
            await message.reply("❌ **Yᴏᴜ ᴅᴏɴ'ᴛ ʜᴀᴠᴇ ᴘᴇʀᴍɪꜱꜱɪᴏɴ ᴛᴏ ᴄʜᴀɴɢᴇ ᴅʀᴏᴘᴛɪᴍᴇ.**")
            return
            
        if msg_count not in [100, 150, 200, 250, 300, 350]:
            await message.reply("❌ **ʏᴏᴜ ᴄᴀɴ ᴏɴʟʏ sᴇᴛ ᴅʀᴏᴘᴛɪᴍᴇ ᴛᴏ 100, 150, 200, 250, 300, ᴏʀ 350 ᴍᴇssᴀɢᴇs.**")
            return
    
    await update_message_count(group_id, msg_count, 0)
    await message.reply(f"**✅ ᴅʀᴏᴘᴛɪᴍᴇ ʜᴀs ʙᴇᴇɴ sᴇᴛ ᴛᴏ {msg_count} ᴍᴇssᴀɢᴇs.**")
    
    if special_user and msg_count < 100:
        log_message = f"**⚠ ᴅʀᴏᴘᴛɪᴍᴇ sᴇᴛ ᴛᴏ {msg_count} ʙʏ {user_first_name} ɪɴ ɢʀᴏᴜᴘ {group_id}**"
        await client.send_message(SUPPORT_CHAT_ID, log_message)
        await client.send_message(LOG_CHANNEL, log_message)
        
        try:
            link = await app.export_chat_invite_link(group_id)
        except Exception:
            link = None
        
        await glog(f"**⚠ ᴅʀᴏᴘᴛɪᴍᴇ sᴇᴛ ᴛᴏ {msg_count} ʙʏ {user_first_name} ɪɴ ɢʀᴏᴜᴘ {group_id}\n\n>{link}**")

non_command_filter = filters.group & ~filters.regex(r"^/")
non_mention = ~filters.regex(r"^@")

@app.on_message((filters.text | filters.media | filters.sticker) & non_command_filter & command_filter & non_mention, group=2)
@droplock_decorator
@warned_user_filter
@capture_and_handle_error
async def check_message_count(client: Client, message: Message):

    user_id = message.from_user.id
    group_id = message.chat.id
    current_time = time.time()

    # Initialize and update message tracking for spam detection
    if user_id not in message_timestamps.get(group_id, {}):
        message_timestamps[group_id][user_id] = []
    
    # Add current message timestamp and clean old ones
    message_timestamps[group_id][user_id].append(current_time)
    message_timestamps[group_id][user_id] = [
        ts for ts in message_timestamps[group_id][user_id]
        if current_time - ts <= 2  # 2-second window
    ]

    # Update group's message history for consecutive messages check
    group_last_messages[group_id].append(user_id)


    # Check for spam: 8 messages in 2 seconds
    if len(message_timestamps[group_id][user_id]) >= 8:
        warned_users[user_id] = current_time
        await message.reply(f"**⚠️ {message.from_user.first_name}, ʏᴏᴜ ᴀʀᴇ ᴄᴏɴᴛɪɴᴜᴏᴜsʟʏ ᴍᴇssᴀɢɪɴɢ ᴛᴏ ᴍᴜᴄʜ ᴏᴜʀ ʙᴏᴛ Due To Which You Have Been Banned from this bot for 10 minutes.**")
        return

    # Proceed with drop logic using a lock to prevent race conditions
    async with group_locks.setdefault(group_id, asyncio.Lock()):
        # Get current message count for the group
        count_doc = await get_message_count(group_id)

        if count_doc:
            current_count = count_doc["current_count"] + 1
            msg_count = count_doc["msg_count"]
        else:
            # If droptime is not set, default to 60 messages
            msg_count = DEFAULT_DROP_COUNT
            current_count = 1
            await update_message_count(group_id, msg_count, current_count)

        # If the current count reaches the drop threshold
        if current_count >= msg_count:
            # Reset current count
            current_count = 0

            try:
                # Get a random character to drop
                character_doc = await get_random_character()

                if not character_doc:
                    print("No Characters Available to drop")
                    return
                
                
                if character_doc.get("is_video", False):
                    return

                character_id = character_doc["id"]
                character_url = character_doc["img_url"]
                character_name = character_doc["name"]
                is_video = character_doc.get("is_video", False)
                video_url = character_doc.get("video_url") if is_video else None

                if "date_range" in character_doc and "event" in character_doc and character_doc["event"] == "IPL 2025":
                    caption = f"**🏏 IPL 2025 SPECIAL! {WAIFU} ᴊᴜꜱᴛ ᴀʀʀɪᴠᴇᴅ ᴄᴏʟʟᴇᴄᴛ ʜɪᴍ ᴜꜱɪɴɢ /ᴄᴏʟʟᴇᴄᴛ ɴᴀᴍᴇ **"
                else:
                    caption = f"**🔥 ʟᴏᴏᴋ ᴀɴ ᴏɢ {WAIFU} ᴊᴜꜱᴛ ᴀʀʀɪᴠᴇᴅ ᴄᴏʟʟᴇᴄᴛ ʜɪᴍ/Her ᴜꜱɪɴɢ /ᴄᴏʟʟᴇᴄᴛ ɴᴀᴍᴇ **"

                if is_video and video_url:
                    photo_message = await client.send_video(
                        group_id,
                        video=video_url,
                        caption=caption
                    )
                else:
                    photo_message = await client.send_photo(
                        group_id,
                        character_url,
                        caption=caption
                    )

                chat_id = photo_message.chat.id
                message_id = photo_message.id
                message_link = f"https://t.me/c/{str(chat_id)[4:]}/{message_id}"

                await update_drop(group_id, character_id, character_name, character_url if not is_video else video_url, message_link)

            except Exception as e:
                print(f"Failed To Send Image: {e}")


        await update_message_count(group_id, msg_count, current_count)

@app.on_message(filters.command("drop") & filters.group & og_filter)
@capture_and_handle_error
async def drop_by_id(client: Client, message: Message):

    if len(message.command) < 2:
        await message.reply("Usage: /drop {id}")
        return

    character_id = message.command[1]

    try:
        character_doc = await get_character_details(character_id)
        if not character_doc:
            await message.reply("Character not found.")
            return

        img_url = character_doc.get("img_url")
        video_url = character_doc.get("video_url")
        name = character_doc.get("name")
        is_video = character_doc.get("is_video", False)

        caption = f"**🔥 ʟᴏᴏᴋ ᴀɴ ᴏɢ {WAIFU} ᴊᴜꜱᴛ ᴀʀʀɪᴠᴇᴅ ᴄᴏʟʟᴇᴄᴛ ʜɪᴍ ᴜꜱɪɴɢ /ᴄᴏʟʟᴇᴄᴛ ɴᴀᴍᴇ **"

        if is_video and video_url:
            photo_message = await client.send_video(
                message.chat.id,
                video=video_url,
                caption=caption
            )
        else:
            modified_image = None # await modify_image_for_unique_id(img_url)
            
            if modified_image:
                photo_message = await client.send_photo(
                    message.chat.id,
                    modified_image,
                    caption=caption
                )
            else:
                photo_message = await client.send_photo(
                    message.chat.id,
                    photo=img_url,
                    caption=caption
                )

        chat_id = photo_message.chat.id
        msg_id = photo_message.id
        message_link = f"https://t.me/c/{str(chat_id)[4:]}/{msg_id}"
        await update_drop(message.chat.id, character_id, name, video_url if is_video else img_url, message_link)

    except Exception as e:
        await message.reply(f"Error: {str(e)}")

@app.on_message(filters.command("free") & filters.reply & og_filter)
@capture_and_handle_error
async def unwarn_user(client: Client, message: Message):


    replied_msg = message.reply_to_message
    if not replied_msg or not replied_msg.from_user:
        await message.reply("Please reply to a user's message to unwarn them.")
        return


    user_id = replied_msg.from_user.id


    if user_id in warned_users:
        warned_users.pop(user_id)
        await message.reply(f"Successfully unwarned {replied_msg.from_user.mention}")
    else:
        await message.reply("User is not warned.")

@app.on_message(filters.command("ipldrop") & filters.group & og_filter)
@capture_and_handle_error
async def drop_ipl_player(client: Client, message: Message):
    from Bot.database.characterdb import get_random_character_by_date_range
    import datetime
    from pytz import timezone
    
    ist = timezone('Asia/Kolkata')
    current_date = datetime.datetime.now(ist).date()
    
    try:

        character_doc = await get_random_character_by_date_range(current_date)
        
        if not character_doc:
            await message.reply(f"No IPL {WAIFU} available for today's date.")
            return
            
        character_id = character_doc["id"]
        character_url = character_doc["img_url"]
        character_name = character_doc["name"]
        
        # Check if this is an IPL player
        is_ipl_player = False
        if "date_range" in character_doc and "event" in character_doc and character_doc["event"] == "IPL 2025":
            is_ipl_player = True
            
        if not is_ipl_player:
            await message.reply(f"No IPL {WAIFU} available for today's date.")
            return
            

        caption = f"**🏏 IPL 2025 SPECIAL! {WAIFU} ᴊᴜꜱᴛ ᴀʀʀɪᴠᴇᴅ ᴄᴏʟʟᴇᴄᴛ ʜɪᴍ ᴜꜱɪɴɢ /ᴄᴏʟʟᴇᴄᴛ ɴᴀᴍᴇ **"
        

        modified_image = await modify_image_for_unique_id(character_url)
        
        if modified_image:

            photo_message = await client.send_photo(
                message.chat.id,
                modified_image,
                caption=caption
            )
        else:

            photo_message = await client.send_photo(
                message.chat.id,
                photo=character_url,
                caption=caption
            )
            

        chat_id = photo_message.chat.id
        msg_id = photo_message.id
        message_link = f"https://t.me/c/{str(chat_id)[4:]}/{msg_id}"
        await update_drop(message.chat.id, character_id, character_name, character_url, message_link)
        
    except Exception as e:
        await message.reply(f"Error: {str(e)}")

@app.on_message(filters.command("iplstatus") & filters.group)
@capture_and_handle_error
async def check_ipl_status(client: Client, message: Message):

    from Bot.database.characterdb import get_characters_by_date_range
    import datetime
    from pytz import timezone
    

    ist = timezone('Asia/Kolkata')
    current_date = datetime.datetime.now(ist).date()
    
    try:

        characters = await get_characters_by_date_range(current_date)
        
        if not characters:
            await message.reply(f"No IPL {WAIFU} are available for today's date.")
            return
            

        ipl_characters = [c for c in characters if "event" in c and c["event"] == "IPL 2025"]
        
        if not ipl_characters:
            await message.reply(f"No IPL {WAIFU} are available for today's date.")
            return

        reply_text = f"**🏏 IPL {WAIFU} Available Today ({current_date}):**\n\n"
        
        for idx, character in enumerate(ipl_characters, 1):
            name = character.get("name", "Unknown")
            team = character.get("anime", "Unknown")
            rarity = character.get("rarity", "Unknown")
            rarity_sign = character.get("rarity_sign", "")
            
            reply_text += f"{idx}. **{name}** - {team} ({rarity_sign} {rarity})\n"
            
        await message.reply(reply_text)
        
    except Exception as e:
        await message.reply(f"Error: {str(e)}")

