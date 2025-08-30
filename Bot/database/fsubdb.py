from Bot.database import db
from pyrogram.enums import ChatMemberStatus
from pyrogram.errors import UserNotParticipant

# Enable or disable force subscription
async def set_force_subscription(enabled):
    await db.Settings.update_one(
        {"setting": "force_sub"},
        {"$set": {"enabled": enabled}},
        upsert=True
    )
    return enabled

# Get current force subscription status
async def get_force_subscription():
    force_sub = await db.Settings.find_one({"setting": "force_sub"})
    if not force_sub:
        return {
            "enabled": False,
            "group_ids": []
        }
    
    # Normalize entries to handle old integer format
    group_entries = force_sub.get("group_ids", [])
    normalized_entries = []
    for entry in group_entries:
        if isinstance(entry, int):
            normalized_entries.append({"id": entry, "invite_link": None})
        else:
            normalized_entries.append(entry)
            
    return {
        "enabled": force_sub.get("enabled", False),
        "group_ids": normalized_entries
    }

# Add or update group entries
async def add_group_entries(group_entries):
    force_sub = await db.Settings.find_one({"setting": "force_sub"})
    current_entries = force_sub.get("group_ids", []) if force_sub else []
    
    # Normalize existing entries
    normalized_entries = []
    for entry in current_entries:
        if isinstance(entry, int):
            normalized_entries.append({"id": entry, "invite_link": None})
        else:
            normalized_entries.append(entry)
    
    # Update or add new entries
    for new_group in group_entries:
        exists = False
        for entry in normalized_entries:
            if entry["id"] == new_group["id"]:
                if new_group["invite_link"]:
                    entry["invite_link"] = new_group["invite_link"]
                exists = True
                break
        if not exists:
            normalized_entries.append(new_group)
            
    # Update database
    await db.Settings.update_one(
        {"setting": "force_sub"},
        {"$set": {"group_ids": normalized_entries}},
        upsert=True
    )
    
    return len(group_entries)

# Remove group entries
async def remove_group_entries(group_entries):
    force_sub = await db.Settings.find_one({"setting": "force_sub"})
    current_entries = force_sub.get("group_ids", []) if force_sub else []
    
    # Normalize existing entries
    normalized_entries = []
    for entry in current_entries:
        if isinstance(entry, int):
            normalized_entries.append({"id": entry, "invite_link": None})
        else:
            normalized_entries.append(entry)
    
    # Remove specified entries
    remove_ids = [g["id"] for g in group_entries]
    filtered_entries = [e for e in normalized_entries if e["id"] not in remove_ids]
    
    # Update database
    await db.Settings.update_one(
        {"setting": "force_sub"},
        {"$set": {"group_ids": filtered_entries}},
        upsert=True
    )
    
    return len(group_entries) 


async def is_subscribed(client, user_id: int, group_id: int) -> bool:
    try:
        member = await client.get_chat_member(group_id, user_id)
        return member.status in [ChatMemberStatus.MEMBER, ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]
    except UserNotParticipant:
        return False
    except:
        return False

async def get_chat_username(client, chat_id: int) -> str:
    try:
        chat = await client.get_chat(chat_id)
        return chat.username
    except Exception as e:
        print(f"Error fetching chat username: {e}")
        return None

async def check_force_subscription(client, user_id: int) -> tuple[bool, list]:
    """Check if user is subscribed to required groups"""
    force_sub = await db.Settings.find_one({"setting": "force_sub"})
    if not force_sub or not force_sub.get("enabled"):
        return True, []

    group_entries = force_sub.get("group_ids", [])
    buttons = []
    for group in group_entries:
        group_id = group.get("id")
        invite_link = group.get("invite_link")
        if not group_id or not invite_link:
            continue
        if not await is_subscribed(client, user_id, group_id):
            buttons.append({
                "text": "Jᴏɪɴ Gʀᴏᴜᴘ",
                "url": invite_link
            })

    return len(buttons) == 0, buttons