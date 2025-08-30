from pyrogram import Client, filters
from pyrogram.types import Message
from Bot.config import AYUSH as BOT_OWNER, OWNERS
from Bot import app, Command
from Bot.utils import sudo_filter, og_filter
from Bot.database.privacydb import (
    is_user_sudo, is_user_banned, ban_user, unban_user, 
    add_sudo_user, add_og_user, remove_og_user, is_user_og, 
    remove_sudo_user, get_sudo_users, get_og_users
)
from Bot.errors import capture_and_handle_error


@app.on_message(Command("bang") & sudo_filter & og_filter)
@app.on_message(filters.regex("Nikal Lawde"))
@capture_and_handle_error
async def ban(client: Client, message: Message):
    if message.from_user.id != BOT_OWNER and not await is_user_sudo(message.from_user.id) and not await is_user_og(message.from_user.id):
        await message.reply("🚫 **Yᴏᴜ ᴀʀᴇ ɴᴏᴛ ᴀᴜᴛʜᴏʀɪᴢᴇᴅ ᴛᴏ ᴜsᴇ ᴛʜɪs ᴄᴏᴍᴍᴀɴᴅ.**")
        return

    if len(message.command) < 2 and not message.reply_to_message:
        await message.reply("❗ **Pʟᴇᴀsᴇ ᴘʀᴏᴠɪᴅᴇ ᴀ ᴜsᴇʀ ID ᴏʀ ʀᴇᴘʟʏ ᴛᴏ ᴀ ᴜsᴇʀ's ᴍᴇssᴀɢᴇ.**")
        return

    user_id = int(message.command[1]) if len(message.command) > 1 else message.reply_to_message.from_user.id
    user = await client.get_users(user_id)
    first_name = user.first_name

    if await is_user_banned(user_id):
        await message.reply(f"🔒 **{first_name} ɪs ᴀʟʀᴇᴀᴅʏ ʙᴀɴɴᴇᴅ ғʀᴏᴍ ᴛʜɪs ʙᴏᴛ.**")
        return

    await ban_user(user_id)
    await message.reply(f"🔨 **{first_name} ʜᴀs ʙᴇᴇɴ ᴘᴇʀᴍᴀɴᴇɴᴛʟʏ ʙᴀɴɴᴇᴅ ғʀᴏᴍ ᴛʜɪs ʙᴏᴛ.**")

@app.on_message(Command("unbang") & sudo_filter & og_filter)
@capture_and_handle_error
async def unban(client: Client, message: Message):
    if message.from_user.id != BOT_OWNER and not await is_user_sudo(message.from_user.id) and not await is_user_og(message.from_user.id):
        await message.reply("🚫 **Yᴏᴜ ᴀʀᴇ ɴᴏᴛ ᴀᴜᴛʜᴏʀɪᴢᴇᴅ ᴛᴏ ᴜsᴇ ᴛʜɪs ᴄᴏᴍᴍᴀɴᴅ.**")
        return

    if len(message.command) < 2 and not message.reply_to_message:
        await message.reply("❗ **Pʟᴇᴀsᴇ ᴘʀᴏᴠɪᴅᴇ ᴀ ᴜsᴇʀ ID ᴏʀ ʀᴇᴘʟʏ ᴛᴏ ᴀ ᴜsᴇʀ's ᴍᴇssᴀɢᴇ.**")
        return

    user_id = int(message.command[1]) if len(message.command) > 1 else message.reply_to_message.from_user.id
    user = await client.get_users(user_id)
    first_name = user.first_name

    if not await is_user_banned(user_id):
        await message.reply(f"✅ **{first_name} ɪs ᴀʟʀᴇᴀᴅʏ ғʀᴇᴇ ᴛᴏ ᴜsᴇ ᴛʜɪs ʙᴏᴛ.**")
        return

    await unban_user(user_id)
    await message.reply(f"🔓 **{first_name} ʜᴀs ʙᴇᴇɴ ᴜɴʙᴀɴɴᴇᴅ ғʀᴏᴍ ᴛʜɪs ʙᴏᴛ.**")

@app.on_message(Command("sudo") & filters.user(OWNERS))
@capture_and_handle_error
async def add_sudo(client: Client, message: Message):

    if len(message.command) < 2:
        await message.reply("❗ **Pʟᴇᴀsᴇ ᴘʀᴏᴠɪᴅᴇ ᴀ ᴜsᴇʀ ID.**")
        return

    user_id = int(message.command[1])
    user = await client.get_users(user_id)
    first_name = user.first_name

    if await is_user_sudo(user_id):
        await message.reply(f"✅ **{first_name} ᴀʟʀᴇᴀᴅʏ ʜᴀs sᴜᴅᴏ ᴘᴏᴡᴇʀs.**")
        return

    await add_sudo_user(user_id)
    await message.reply(f"👑 **{first_name} ʜᴀs ʙᴇᴇɴ ᴀᴅᴅᴇᴅ ᴀs ᴀ sᴜᴅᴏ ᴜsᴇʀ.**")


@app.on_message(Command("rmsudo") & filters.user(OWNERS))
@capture_and_handle_error
async def remove_sudo(client: Client, message: Message):
    if len(message.command) < 2:
        await message.reply("❗ **Pʟᴇᴀsᴇ ᴘʀᴏᴠɪᴅᴇ ᴀ ᴜsᴇʀ ID.**")
        return

    user_id = int(message.command[1])
    user = await client.get_users(user_id)
    first_name = user.first_name

    if not await is_user_sudo(user_id):
        await message.reply(f"**✅ {first_name} ɪs ᴀʟʀᴇᴀᴅʏ ᴀ nᴏʀᴍᴀʟ ᴜsᴇʀ.**")
        return

    await remove_sudo_user(user_id)
    await message.reply(f"❌ **{first_name} ʜᴀs ʙᴇᴇɴ ʀᴇᴍᴏᴠᴇᴅ ᴀs ᴀ sᴜᴅᴏ ᴜsᴇʀ.**")



@app.on_message(Command("og") & filters.user(OWNERS))
@capture_and_handle_error
async def add_og(client: Client, message: Message):

    if len(message.command) < 2:
        await message.reply("❗ **Pʟᴇᴀsᴇ ᴘʀᴏᴠɪᴅᴇ ᴀ ᴜsᴇʀ ID.**")
        return

    user_id = int(message.command[1])
    user = await client.get_users(user_id)
    first_name = user.first_name

    if await is_user_og(user_id):
        await message.reply(f"✅ **{first_name} ɪs ᴀʟʀᴇᴀᴅʏ ᴀɴ OG ᴜsᴇʀ.**")
        return

    await add_og_user(user_id)
    await message.reply(f"👑 **{first_name} ʜᴀs ʙᴇᴇɴ ᴀᴅᴅᴇᴅ ᴀs ᴀɴ OG ᴜsᴇʀ.**")

@app.on_message(Command("rmog") & filters.user(OWNERS))
@capture_and_handle_error
async def remove_og(client: Client, message: Message):
    if len(message.command) < 2:
        await message.reply("❗ **Pʟᴇᴀsᴇ ᴘʀᴏᴠɪᴅᴇ ᴀ ᴜsᴇʀ ID.**")
        return

    user_id = int(message.command[1])
    user = await client.get_users(user_id)
    first_name = user.first_name

    if not await is_user_og(user_id):
        await message.reply(f"✅ **{first_name} ɪs ᴀʟʀᴇᴀᴅʏ ᴀ ʀᴇɢᴜʟᴀʀ ᴜsᴇʀ, ɴᴏᴛ ᴀɴ OG.**")
        return

    await remove_og_user(user_id)
    await message.reply(f"❌ **{first_name} ʜᴀs ʙᴇᴇɴ ʀᴇᴍᴏᴠᴇᴅ ғʀᴏᴍ ᴛʜᴇ OG ᴜsᴇʀs.**")

# OG List
@app.on_message(Command("sudoers") & filters.user(OWNERS))
@capture_and_handle_error
async def sudoers(client: Client, message: Message):
    sudo_users = await get_sudo_users()
    if not sudo_users:
        await message.reply("🛑 **Tʜᴇʀᴇ ᴀʀᴇ ɴᴏ sᴜᴅᴏ ᴜsᴇʀs.**")
        return

    sudo_list = []
    for i, sudo in enumerate(sudo_users, 1):
        user_id = sudo['user_id']
        try:
            user = await client.get_users(user_id)
            user_mention = user.mention
        except Exception:
            user_mention = f"User ID {user_id}"
        sudo_list.append(f"{i}. {user_mention} → {user_id}")

    sudo_message = "\n".join(sudo_list)
    await message.reply(f"👑 **Lɪsᴛ ᴏғ sᴜᴅᴏ ᴜsᴇʀs:**\n\n{sudo_message}")


@app.on_message(Command("ogs") & filters.user(OWNERS))
@capture_and_handle_error
async def og_list(client: Client, message: Message):
    og_users = await get_og_users()
    if not og_users:
        await message.reply("🛑 **Tʜᴇʀᴇ ᴀʀᴇ ɴᴏ OG ᴜsᴇʀs.**")
        return

    og_list = []
    for i, og in enumerate(og_users, 1):
        user_id = og['user_id']
        try:
            user = await client.get_users(user_id)
            user_mention = user.mention
        except Exception:
            user_mention = f"User ID {user_id}"
        og_list.append(f"{i}. {user_mention} → {user_id}")

    og_message = "\n".join(og_list)
    await message.reply(f"👑 **Lɪsᴛ ᴏғ OG ᴜsᴇʀs:**\n\n{og_message}")

