from Bot.database import tgroups_collection, db
from datetime import datetime

async def is_group_in_database(group_id: int) -> bool:
    group = await tgroups_collection.find_one({"group_id": group_id})
    return group is not None

async def insert_new_group(group_id: int, group_title: str, group_username: str, members_count: int):
    await tgroups_collection.insert_one({
        "group_id": group_id,
        "group_title": group_title,
        "group_username": group_username,
        "members_count": members_count,
        "added_at": datetime.utcnow()
    })

async def update_group_smash(group_id: int, chat_name: str, chat_username: str | None):
    return await db.Groups.update_one(
        {"group_id": group_id},
        {
            "$inc": {"smash_count": 1},
            "$set": {"chat_name": chat_name, "username": chat_username}
        },
        upsert=True
    )

async def update_daily_smash(user_id: int, date: str, first_name: str):
    return await db.Tdsmashes.update_one(
        {"user_id": user_id, "date": date},
        {
            "$inc": {"smash_count": 1},
            "$set": {"first_name": first_name}
        },
        upsert=True
    )

async def update_total_smash_count(user_id: int, first_name: str):
    return await db.SmashCount.update_one(
        {"user_id": user_id},
        {
            "$inc": {"smash_count": 1},
            "$set": {"first_name": first_name}
        },
        upsert=True
    )