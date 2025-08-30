from Bot.database import db 
from datetime import datetime, timedelta
from Bot.config import OWNERS
from functools import lru_cache

async def ban_user(user_id, duration_minutes=None):
    ban_until = datetime.utcnow() + timedelta(minutes=duration_minutes) if duration_minutes else None
    
    await db.Banned.update_one(
        {"user_id": user_id},
        {"$set": {"user_id": user_id, "ban_until": ban_until}},
        upsert=True
    )

async def unban_user(user_id):
    await db.Banned.delete_one({"user_id": user_id})

async def is_user_banned(user_id):
    ban_record = await db.Banned.find_one(
        {"user_id": user_id},
        {"ban_until": 1, "_id": 0}
    )
    
    if not ban_record:
        return False
        
    if ban_record["ban_until"] is None:
        return True
    elif ban_record["ban_until"] > datetime.utcnow():
        return True
    else:
        await unban_user(user_id)
        return False

@lru_cache(maxsize=1)
def is_owner(user_id):
    return user_id in OWNERS

async def add_sudo_user(user_id):
    await db.Sudo.update_one(
        {"user_id": user_id},
        {"$set": {"user_id": user_id}},
        upsert=True
    )

async def remove_sudo_user(user_id):
    await db.Sudo.delete_one({"user_id": user_id})

async def is_user_sudo(user_id):
    if is_owner(user_id):
        return True
        
    return await db.Sudo.count_documents({"user_id": user_id}, limit=1) > 0

async def add_og_user(user_id):
    await db.Og.update_one(
        {"user_id": user_id},
        {"$set": {"user_id": user_id}},
        upsert=True
    )

async def remove_og_user(user_id):
    await db.Og.delete_one({"user_id": user_id})

async def is_user_og(user_id):
    if is_owner(user_id):
        return True
        
    return await db.Og.count_documents({"user_id": user_id}, limit=1) > 0

async def get_sudo_users():
    return await db.Sudo.find().to_list(length=None)

async def get_og_users():
    return await db.Og.find().to_list(length=None)