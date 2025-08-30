from pyrogram import Client, filters
from pyrogram.types import Message
from Bot.database.fsubdb import set_force_subscription, get_force_subscription, add_group_entries, remove_group_entries
from Bot.config import OWNERS
from Bot import app, Command

@app.on_message(Command("setfsub") & filters.private & filters.user(OWNERS))
async def set_force_sub(client: Client, message: Message):
    user_id = message.from_user.id
    
    if len(message.command) < 2:
        await message.reply("⚠️ Pʟᴇᴀsᴇ sᴘᴇᴄɪғʏ 'ᴇɴᴀʙʟᴇ' ᴏʀ 'ᴅɪsᴀʙʟᴇ'.")
        return
    
    action = message.command[1].lower()
    if action not in ["enable", "disable"]:
        await message.reply("⚠️ Iɴᴠᴀʟɪᴅ ᴀᴄᴛɪᴏɴ. Pʟᴇᴀsᴇ sᴘᴇᴄɪғʏ 'ᴇɴᴀʙʟᴇ' ᴏʀ 'ᴅɪsᴀʙʟᴇ'.")
        return
    
    enabled = action == "enable"
    await set_force_subscription(enabled)
    await message.reply(f"✅ ғᴏʀᴄᴇ-sᴜʙsᴄʀɪᴘᴛɪᴏɴ ʜᴀs ʙᴇᴇɴ {'enabled' if enabled else 'disabled'}.")


@app.on_message(Command("managegrpids") & filters.private & filters.user(OWNERS))
async def manage_group_ids(client: Client, message: Message):
    user_id = message.from_user.id

    if len(message.command) < 3:
        await message.reply("⚠️ Please specify 'add' or 'remove' followed by group IDs/links.")
        return

    action = message.command[1].lower()
    if action not in ["add", "remove"]:
        await message.reply("⚠️ Invalid action. Use 'add' or 'remove'.")
        return

    processed_groups = []
    args = message.command[2:]
    
    if action == "add":
        i = 0
        while i < len(args):
            try:
                custom_link = None
                chat_id = args[i]
                
                # Check if next argument is -link flag
                if i + 2 < len(args) and args[i + 1] == "-link":
                    custom_link = args[i + 2]
                    i += 3
                else:
                    i += 1
                
                chat = await client.get_chat(chat_id)
                group_id = chat.id
                
                # Determine invite link
                invite_link = None
                if custom_link:
                    invite_link = custom_link
                elif chat.username:
                    invite_link = f"https://t.me/{chat.username}"
                elif chat_id.startswith("http"):
                    invite_link = chat_id
                else:
                    invite_link = await client.export_chat_invite_link(group_id)
                    
                processed_groups.append({
                    "id": group_id,
                    "invite_link": invite_link
                })
            except Exception as e:
                await message.reply(f"⚠️ Failed to process {chat_id}: {str(e)}")
                if custom_link:
                    i += 3
                else:
                    i += 1
                continue
    else:
        # For removal, just process the IDs directly without validation
        for arg in message.command[2:]:
            try:
                # Convert string to integer if it's a numeric ID
                group_id = int(arg) if arg.lstrip('-').isdigit() else arg
                processed_groups.append({
                    "id": group_id,
                    "invite_link": None
                })
            except ValueError:
                await message.reply(f"⚠️ Invalid group ID format: {arg}")
                continue

    # Update entries based on action
    if action == "add":
        count = await add_group_entries(processed_groups)
    elif action == "remove":
        count = await remove_group_entries(processed_groups)

    await message.reply(f"✅ Successfully {action}ed {count} groups.")

@app.on_message(Command("getfsub") & filters.private & filters.user(OWNERS))
async def get_fsub_chats(client: Client, message: Message):
    fsub_config = await get_force_subscription()
    
    if not fsub_config["enabled"]:
        await message.reply("⚠️ Force-subscription is disabled.")
        return

    group_entries = fsub_config["group_ids"]
    if not group_entries:
        await message.reply("⚠️ No groups configured.")
        return

    response = "📋 **Force-sub Groups:**\n\n"
    for idx, entry in enumerate(group_entries, 1):
        link = entry.get("invite_link", "No link")
        response += f"{idx}. `{entry['id']}` - {link}\n"
    
    await message.reply(response)