import random
from pyrogram import filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from Bot import app , Command
from pyrogram.enums import ParseMode
from Bot.config import OWNER_ID, HELP_IMAGE_URLS as IMAGE_URLS
from Bot.database.privacydb import is_user_sudo
from Bot.utils import warned_user_filter , save_user_id_decorator , command_filter

@app.on_message(Command("help") & filters.private & command_filter)
@warned_user_filter
@save_user_id_decorator
async def help_command(client, message):
    await send_help_message(client, message.chat.id)

@app.on_callback_query(filters.regex("help_back"))
async def on_help_callback(client, callback_query):
    await callback_query.answer()  # Acknowledge the callback query to avoid timeout issues
    await send_help_message(client, callback_query.message.chat.id, callback_query.message)

async def send_help_message(client, chat_id, message_to_edit=None):
    """
    Function to send or edit the help message.
    If message_to_edit is provided, it edits that message instead of sending a new one.
    """
    img_url = random.choice(IMAGE_URLS)  # Randomly select an image URL

    caption = "━━━━━━━━━━━━━━\n          𝐇𝐄𝐋𝐏 𝐌𝐄𝐍𝐔\n━━━━━━━━━━━━━━\nPlease select one of the categories below to view the available commands.\n\nUsable Handlers:\n➤ `/`  ➤ `!`  ➤ `.`\n━━━━━━━━━━━━━━"

    keyboard = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("𝑈𝑆𝐸𝑅𝑆", callback_data="help_users"),
                InlineKeyboardButton("𝑆𝑈𝐷𝑂", callback_data="help_invisibles")
            ],
            [
                InlineKeyboardButton("𝐵𝐴𝐶𝐾", callback_data="back_to_start")
            ],
        ]
    )

    if message_to_edit:
        # Edit the existing message
        await message_to_edit.edit_caption(
            caption=caption,
            reply_markup=keyboard,
            parse_mode=ParseMode.MARKDOWN
        )
    else:
        # Send a new message
        await client.send_photo(
            chat_id=chat_id,
            photo=img_url,
            caption=caption,
            reply_markup=keyboard,
            parse_mode=ParseMode.MARKDOWN
        )

@app.on_callback_query(filters.regex("help_users"))
async def on_help_users_callback(client, callback_query):
    await callback_query.answer()  # Acknowledge the callback query to avoid timeout issues

    users_caption = "⥼ Cᴏᴍᴍᴀɴᴅ Oᴠᴇʀᴠɪᴇᴡ ⥽**\n\n🔹 **/collect** - Cᴀᴘᴛᴜʀᴇ ᴀɴᴅ ᴀᴅᴅ ᴀ ᴘʟᴀʏᴇʀ ᴛᴏ ʏᴏᴜʀ ᴄᴏʟʟᴇᴄᴛɪᴏɴ.\n🔹 **/mycollection** - Sʜᴏᴡᴄᴀsᴇ ʏᴏᴜʀ ᴄᴏʟʟᴇᴄᴛɪᴏɴ ᴏғ ᴘʟᴀʏᴇʀꜱ.\n🔹 **/ɢᴛᴏᴘ** - Aᴄᴄᴇss ᴛʜᴇ ɢʟᴏʙᴀʟ ʟᴇᴀᴅᴇʀʙᴏᴀʀᴅ ғᴏʀ ᴛᴏᴘ ᴄᴏʟʟᴇᴄᴛᴏʀs.\n🔹 **/tdtop** - Vɪᴇᴡ ᴛᴏᴅᴀʏ's ᴛᴏᴘ ᴄᴏʟʟᴇᴄᴛᴏʀꜱ.\n🔹 **/ctop** - Sᴇᴇ ᴡʜɪᴄʜ ᴄʜᴀᴛ ʜᴀs ᴛʜᴇ ᴍᴏsᴛ ᴄᴏʟʟᴇᴄᴛꜱ.\n🔹 **/top** - Dɪsᴘʟᴀʏ ᴛʜᴇ ᴛᴏᴘ ᴄᴏʟʟᴇᴄᴛᴏʀꜱ ᴡɪᴛʜɪɴ ʏᴏᴜʀ ɢʀᴏᴜᴘ.\n🔹 **/droptime** - Aᴅᴊᴜsᴛ ᴛʜᴇ ᴛɪᴍɪɴɢ ғᴏʀ ᴘʟᴀʏᴇʀ ᴅʀᴏᴘs ɪɴ ʏᴏᴜʀ ɢʀᴏᴜᴘs.\n🔹 **/smode** - Cᴜsᴛᴏᴍɪᴢᴇ ʜᴏᴡ ʏᴏᴜʀ ᴄᴏʟʟᴇᴄᴛɪᴏɴ ɪs ᴅɪsᴘʟᴀʏᴇᴅ.\n🔹 **/cmode** - Sᴇᴛ ʏᴏᴜʀ ᴘʀᴇғᴇʀʀᴇᴅ ᴄᴀᴘᴛɪᴏɴ sᴛʏʟᴇ.\n🔹 **/fav** - Mᴀʀᴋ ᴀ ᴘʟᴀʏᴇʀ ᴀs ʏᴏᴜʀ ғᴀᴠᴏʀɪᴛᴇ.\n🔹 **/sstatus** - Rᴇᴠɪᴇᴡ ʏᴏᴜʀ ᴄᴜʀʀᴇɴᴛ sᴛᴀᴛᴜs ᴀɴᴅ ᴀᴄʜɪᴇᴠᴇᴍᴇɴᴛs.\n🔹 **/claim** - Cʟᴀɪᴍ ᴀ ғʀᴇᴇ ᴘʟᴀʏᴇʀ ᴅᴀɪʟʏ.\n🔹 **/sanime** - Sᴇᴀʀᴄʜ ᴛʜʀᴏᴜɢʜ ᴀʟʟ ᴀᴠᴀɪʟᴀʙʟᴇ ᴀɴɪᴍᴇ ɪɴ ᴛʜᴇ ʙᴏᴛ."

    keyboard = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("𝐵𝐴𝐶𝐾", callback_data="help_back")
            ],
        ]
    )

    await callback_query.message.edit_caption(
        caption=users_caption,
        reply_markup=keyboard,
        parse_mode=ParseMode.MARKDOWN
    )

@app.on_callback_query(filters.regex("help_invisibles"))
async def on_help_invisibles_callback(client, callback_query):
    user_id = callback_query.from_user.id

    # Check if the user is the owner or a sudo user
    if user_id == OWNER_ID or await is_user_sudo(user_id):
        await callback_query.answer()  # Acknowledge the callback query

        invisibles_caption = "➲ Bᴇʟᴏᴡ ᴀʀᴇ ᴛʜᴇ ᴄᴏᴍᴍᴀɴᴅs ғᴏʀ ɪɴᴠɪɴᴄɪʙʟᴇs.\n\n -> Use /start To Get The Admin Panel"

        keyboard = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton("𝐵𝐴𝐶𝐾", callback_data="help_back")
                ],
            ]
        )

        await callback_query.message.edit_caption(
            caption=invisibles_caption,
            reply_markup=keyboard,
            parse_mode=ParseMode.MARKDOWN
        )
    else:
        # Deny access if the user is not authorized
        await callback_query.answer(
            "Yᴏᴜ ᴀʀᴇ ɴᴏᴛ ᴀɴ ɪɴᴠɪɴᴄɪʙʟᴇ ᴜsᴇʀ!",
            show_alert=True
        )
