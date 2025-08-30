from pyrogram import Client, filters
from pyrogram.types import Message
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from Bot.config import OWNERS
from pyrogram.types import CallbackQuery
from Bot import app, Command
from Bot.database.collectiondb import transfer_collection
from Bot.errors import capture_and_handle_error


@app.on_message(Command("transfer") & filters.user(OWNERS))
@capture_and_handle_error
async def transfer_collection_cmd(client: Client, message: Message):
    if message.from_user.id not in OWNERS: 
        await message.reply("Yᴏᴜ ᴀʀᴇ ɴᴏᴛ ᴀᴜᴛʜᴏʀɪᴢᴇᴅ ᴛᴏ ᴜsᴇ ᴛʜɪs ᴄᴏᴍᴍᴀɴᴅ.")
        return

    try:
        from_user_id, to_user_id = map(int, message.command[1:])
    except (ValueError, IndexError):
        await message.reply("**Usᴀɢᴇ: /ᴛʀᴀɴsғᴇʀ ғʀᴏᴍ_ᴜsᴇʀ_ɪᴅ ᴛᴏ_ᴜsᴇʀ_ɪᴅ**")
        return

    try:
        # Fetch users' information
        from_user = await client.get_users(from_user_id)
        to_user = await client.get_users(to_user_id)
    
        # Send confirmation message with inline buttons
        confirm_markup = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("✅ Cᴏɴғɪʀᴍ", callback_data=f"confirm_transfer:{from_user_id}:{to_user_id}"),
                InlineKeyboardButton("❌ Cᴀɴᴄᴇʟ", callback_data="cancel_transfer")
            ]
        ])
        
        await message.reply(
            f"ᴀʀᴇ ʏᴏᴜ sᴜʀᴇ ʏᴏᴜ ᴡᴀnᴛ ᴛᴏ ᴛʀᴀnsғᴇʀ ᴛʜᴇ ᴄᴏʟʟᴇᴄᴛɪᴏn ғʀᴏᴍ {from_user.first_name} ᴛᴏ {to_user.first_name}?",
            reply_markup=confirm_markup
        )
    except Exception:
        from_user = from_user_id
        to_user = to_user_id
    
        # Send confirmation message with inline buttons
        confirm_markup = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("✅ Cᴏɴғɪʀᴍ", callback_data=f"confirm_transfer:{from_user_id}:{to_user_id}"),
                InlineKeyboardButton("❌ Cᴀɴᴄᴇʟ", callback_data="cancel_transfer")
            ]
        ])
        
        await message.reply(
            f"ᴀʀᴇ ʏᴏᴜ sᴜʀᴇ ʏᴏᴜ ᴡᴀnᴛ ᴛᴏ ᴛʀᴀnsғᴇʀ ᴛʜᴇ ᴄᴏʟʟᴇᴄᴛɪᴏn ғʀᴏᴍ {from_user} ᴛᴏ {to_user}?",
            reply_markup=confirm_markup
        )

@app.on_callback_query(filters.regex(r"^confirm_transfer:(\d+):(\d+)$") & filters.user(OWNERS))
@capture_and_handle_error
async def on_confirm_transfer(client: Client, callback_query: CallbackQuery):
    from_user_id, to_user_id = map(int, callback_query.data.split(":")[1:])

    success, message = await transfer_collection(from_user_id, to_user_id)
    
    if success:
        await callback_query.message.edit_text("**Cᴏʟʟᴇᴄᴛɪᴏɴ sᴜᴄᴄᴇssғᴜʟʟʏ ᴛʀᴀɴsғᴇʀʀᴇᴅ.**")
    else:
        await callback_query.message.edit_text(message)

@app.on_callback_query(filters.regex(r"^cancel_transfer$") & filters.user(OWNERS))
@capture_and_handle_error
async def on_cancel_transfer(client: Client, callback_query: CallbackQuery):
    await callback_query.message.edit_text("Tʀᴀɴsғᴇʀ ᴄᴀɴᴄᴇʟʟᴇᴅ.")