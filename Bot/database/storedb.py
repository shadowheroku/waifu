from datetime import datetime
from Bot.database import db


async def add_today_players(user_id, player_ids):
    if len(player_ids) != 10:
        raise ValueError("Exactly 10 player IDs must be provided.")

    await db.Store.update_one(
        {"user_id": user_id},
        {
            "$set": {
                "player_ids": player_ids,
                "stored_at": datetime.utcnow()
            }
        },
        upsert=True
    )


async def update_player_ids(user_id, player_ids):
    if len(player_ids) != 10:
        raise ValueError("Exactly 10 player IDs must be provided.")

    await db.Store.update_one(
        {"user_id": user_id},
        {
            "$set": {"player_ids": player_ids}
        }
    )


async def get_player_ids(user_id):
    user_data = await db.Store.find_one(
        {"user_id": user_id}, 
        {"player_ids": 1, "_id": 0}
    )
    return user_data.get("player_ids", []) if user_data else []


async def get_stored_datetime(user_id):
    user_data = await db.Store.find_one(
        {"user_id": user_id}, 
        {"stored_at": 1, "_id": 0}
    )
    return user_data.get("stored_at") if user_data else None


async def has_stored_today(user_id):
    current_date = datetime.utcnow().date()
    start_of_day = datetime(current_date.year, current_date.month, current_date.day)
    
    count = await db.Store.count_documents({
        "user_id": user_id,
        "stored_at": {"$gte": start_of_day}
    })
    
    return count > 0


async def delete_stored_data(user_id):
    await db.Store.delete_one({"user_id": user_id})


async def get_all_stored_users():
    users = await db.Store.find(
        {}, 
        {"user_id": 1, "_id": 0}
    ).to_list(length=None)
    
    return [user["user_id"] for user in users]

async def get_user_store(user_id: int):
    return await db.Store.find_one({"user_id": user_id})

async def update_user_store(user_id: int, player_ids: list):
    return await db.Store.update_one(
        {"user_id": user_id},
        {
            "$set": {
                "player_ids": player_ids,
                "stored_at": datetime.utcnow(),
            }
        },
        upsert=True
    )

async def get_purchase_record(user_id: int, date: str):
    return await db.SUCCESFULLYPURCHASED.find_one({
        "user_id": user_id,
        "date": date
    })

async def add_purchase_record(user_id: int, date: str, player_id: int):
    existing_record = await get_purchase_record(user_id, date)
    if existing_record:
        await db.SUCCESFULLYPURCHASED.update_one(
            {"user_id": user_id, "date": date},
            {"$push": {"player_ids": player_id}}
        )
    else:
        await db.SUCCESFULLYPURCHASED.insert_one({
            "user_id": user_id,
            "date": date,
            "player_ids": [player_id]
        })
