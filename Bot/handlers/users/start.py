import random
import time
from pyrogram import filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup
from Bot import app, StartTime, get_readable_time , Command
from pyrogram.enums import ParseMode
from Bot.config import OWNER_ID, START_IMAGE_URLS as IMAGE_URLS
from Bot.database.privacydb import is_user_sudo
from Bot.utils import warned_user_filter , save_user_id_decorator
from Bot.database.grabtokendb import create_user_if_not_exists
from Bot.config import SUPPORT_GROUP_URL

@app.on_message(Command("start") & filters.private)
@warned_user_filter
@save_user_id_decorator
async def handle_start(client, message):
    user_id = message.from_user.id

    # Create the user if not already in the GrabToken database
    await create_user_if_not_exists(user_id, message.from_user.first_name)

    if user_id == OWNER_ID or await is_user_sudo(user_id):
        # Special message for owner or sudo users
        keyboard = ReplyKeyboardMarkup(
            [["⚙ Admin Panel ⚙"]],
            resize_keyboard=True
        )
        mention_user = f"Hɪ, [{message.from_user.first_name}](tg://user?id={user_id})!"
        await client.send_message(
            chat_id=message.chat.id,
            text=mention_user,
            reply_markup=keyboard,
            parse_mode=ParseMode.MARKDOWN
        )
    else:
        # Normal start message
        await send_start_message(client, message.chat.id)

@app.on_callback_query(filters.regex("back_to_start"))
async def handle_callback(client, callback_query):
    await callback_query.answer()  # Acknowledge the callback query to avoid timeout issues
    await send_start_message(client, callback_query.message.chat.id, callback_query.message)

@app.on_callback_query(filters.regex("refresh"))
async def refresh_ping_uptime(client, callback_query):
    await callback_query.answer()  # Acknowledge the callback query to avoid timeout issues
    await send_start_message(client, callback_query.message.chat.id, callback_query.message)

async def calculate_ping(client, chat_id):
    start_time = time.time()
    sent_message = await client.send_message(chat_id, "Wait...")
    end_time = time.time()
    await sent_message.delete()
    ping = round((end_time - start_time) * 1000, 3)
    return ping

async def send_start_message(client, chat_id, message_to_edit=None):
    """
    Function to send or edit the start message.
    If message_to_edit is provided, it edits that message with updated ping and uptime.
    """
    ping = await calculate_ping(client, chat_id)
    uptime = await get_readable_time(time.time() - StartTime)

    # Get bot's mention using Markdown
    bot_user = await client.get_me()
    mention_bot = f"[{bot_user.first_name}](tg://user?id={bot_user.id})"

    # Randomly select an image URL
    img_url = random.choice(IMAGE_URLS)

    # Prepare the caption
    caption = f"Gʀᴇᴇᴛɪɴɢs! I'ᴍ {mention_bot}, ʏᴏᴜʀ ᴄʜᴀᴛ ᴄᴏᴍᴘᴀɴɪᴏɴ.\n┏━━━━━━━✦✗✦━━━━━━━┓\n⤷ Wʜᴀᴛ I ᴅᴏ: Bʀɪɴɢ ᴏɢ ᴘʟᴀʏᴇʀꜱ ᴛᴏ ʏᴏᴜʀ ᴄʜᴀᴛ ғᴏʀ ᴜsᴇʀs ᴛᴏ ᴄʟᴀɪᴍ.\n⤷ Hᴏᴡ ᴛᴏ ᴜsᴇ ᴍᴇ: Jᴜsᴛ ᴀᴅᴅ ᴍᴇ ᴛᴏ ʏᴏᴜʀ ɢʀᴏᴜᴘ ᴀɴᴅ ᴛᴀᴘ ᴛʜᴇ Hᴇʟᴘ ʙᴜᴛᴛᴏɴ ғᴏʀ ɪɴsᴛʀᴜᴄᴛɪᴏɴs.\n┗━━━━━━━✦✗✦━━━━━━━┛\n⧗ Pɪɴɢ: {ping} ms\n⧗ Uᴘᴛɪᴍᴇ: {uptime}"

    keyboard = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "𝐴𝐷𝐷 𝑀𝐸",
                    url=f"https://t.me/{bot_user.username}?startgroup=true",
                )
            ],
            [
                InlineKeyboardButton("𝐻𝐸𝐿𝑃", callback_data="help_back"),
                InlineKeyboardButton(
                    "𝑆𝑈𝑃𝑃𝑂𝑅𝑇 𝐺𝑅𝑂𝑈𝑃", url=SUPPORT_GROUP_URL
                ),
            ],
        ]
    )
    

    if message_to_edit:
        # Edit the existing message with updated ping and uptime
        await message_to_edit.edit_caption(
            caption=caption,
            reply_markup=keyboard,
            parse_mode=ParseMode.MARKDOWN
        )
    else:
        # # Send a new message
        # x = await client.send_message(chat_id, "Starting")
        # for i in range(1, 3):
        #     await asyncio.sleep(0.15)
        #     await x.edit_text(f"Starting{'.' * i}")
        # await x.delete()  # Deleting the "Starting..." message
        await client.send_photo(
            chat_id=chat_id,
            photo=img_url,
            caption=caption,
            reply_markup=keyboard,
            parse_mode=ParseMode.MARKDOWN
        )

@app.on_message(Command("start") & filters.group)
@warned_user_filter
async def start_command(client, message):
    # Creating inline keyboard with multiple buttons
    keyboard = InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("sᴛᴀʀᴛ ❄", url=f"https://t.me/{app.me.username}?start=0")],
            [
                InlineKeyboardButton("sᴜᴘᴘᴏʀᴛ", url=SUPPORT_GROUP_URL),
                InlineKeyboardButton("ᴜᴘᴅᴀᴛᴇs", url="https://t.me/Hunt_WH_Updates")
            ]
        ]
    )

    # Sending message with inline buttons
    await message.reply_text(
        "**ʀᴀɴᴅᴏᴍ ᴘʟᴀʏᴇʀ ᴡɪʟʟ ʙᴇ ᴅʀᴏᴘᴘᴇᴅ ʜᴇʀᴇ !!\nᴘʟᴇᴀsᴇ ɢʀᴀɴᴛ ᴍᴇ ᴀᴅᴍɪɴ ᴘʀɪᴠɪʟᴇɢᴇs sᴏ ᴛʜᴀᴛ ɪ ᴄᴀɴ ᴅʀᴏᴘ ᴘʟᴀʏᴇʀ\n\nᴄᴏɴᴛᴀᴄᴛ ᴍᴇ ɪɴ ᴘᴍ ғᴏʀ ᴍᴏʀᴇ ɪɴғᴏ.**",
        reply_markup=keyboard
    )

@app.on_message(Command("refer"))
@warned_user_filter
async def handle_refer(client, message):
    user_id = message.from_user.id

    # Generate referral link
    bot_user = await client.get_me()
    referral_link = f"https://t.me/{bot_user.username}?start=ref_{user_id}"

    # Send referral link to the user
    await client.send_message(
        chat_id=message.chat.id,
        text=f"Your referral link: {referral_link}",
        disable_web_page_preview=True
    )