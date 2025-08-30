from Bot.database import db
import pytz , time
from datetime import datetime
from functools import lru_cache

@lru_cache(maxsize=1)
def get_ist_timezone():
    return pytz.timezone('Asia/Kolkata')

def get_current_ist_date():
    tz = get_ist_timezone()
    now = datetime.now(tz)
    return now.strftime('%Y-%m-%d')

async def create_user_if_not_exists(user_id, user_name=None):
    update_data = {
        "$setOnInsert": {
            "grabtoken": 0,
            "daily_tokens": 0,
            "last_updated_date": None,
        }
    }
    
    if user_name:
        update_data["$set"] = {"user_name": user_name}
    
    await db.GrabToken.update_one(
        {"user_id": user_id},
        update_data,
        upsert=True
    )

async def add_grab_token(user_id, amount, user_name=None):
    current_date = get_current_ist_date()
    
    # First ensure user exists with initial values
    await create_user_if_not_exists(user_id, user_name)
    
    # Then update their balance
    update_data = {
        "$inc": {"grabtoken": amount},
        "$set": {
            "daily_tokens": amount,
            "last_updated_date": current_date
        }
    }
    
    if user_name:
        update_data["$set"]["user_name"] = user_name
    
    await db.GrabToken.update_one(
        {"user_id": user_id},
        update_data
    )

async def decrease_grab_token(user_id, amount, user_name=None):
    update_data = {"$inc": {"grabtoken": -amount}}
    if user_name:
        update_data["$set"] = {"user_name": user_name}

    result = await db.GrabToken.find_one_and_update(
        {"user_id": user_id, "grabtoken": {"$gte": amount}},
        update_data,
        upsert=False,
        return_document=False
    )
    
    return result is not None

async def get_user_balance(user_id):
    # First ensure user exists
    await create_user_if_not_exists(user_id)
    
    # Then get their balance
    user = await db.GrabToken.find_one(
        {"user_id": user_id}, 
        {"grabtoken": 1, "_id": 0}
    )
    return user.get("grabtoken", 0) if user else 0

async def transfer_grabtoken(from_user_id, to_user_id, amount, from_user_name=None, to_user_name=None):
    if await decrease_grab_token(from_user_id, amount, from_user_name):
        await add_grab_token(to_user_id, amount, to_user_name)
        return True
    return False

async def reset_user_balance(user_id, user_name=None):
    update_data = {"$set": {"grabtoken": 0}}
    if user_name:
        update_data["$set"]["user_name"] = user_name
    
    await db.GrabToken.update_one(
        {"user_id": user_id},
        update_data,
        upsert=True
    )

async def fetch_grabtoken_leaderboard(user_ids=None):
    pipeline = [
        {"$match": {"user_id": {"$in": user_ids}} if user_ids else {}},
        {
            "$project": {
                "user_id": 1,
                "user_name": 1,
                "total_grabtokens": "$grabtoken"
            }
        },
        {"$sort": {"total_grabtokens": -1}},
        {"$limit": 10}
    ]
    
    return await db.GrabToken.aggregate(pipeline).to_list(length=10)

async def fetch_bank_leaderboard(limit=25):
    pipeline = [
        {
            "$lookup": {
                "from": "GrabToken",
                "localField": "user_id",
                "foreignField": "user_id",
                "as": "user_info"
            }
        },
        {"$unwind": {"path": "$user_info", "preserveNullAndEmptyArrays": True}},
        {
            "$project": {
                "user_id": 1,
                "bank_balance": 1,
                "user_name": "$user_info.user_name"
            }
        },
        {"$match": {"user_name": {"$ne": None}}},
        {"$sort": {"bank_balance": -1}},
        {"$limit": limit}
    ]
    
    return await db.Bank.aggregate(pipeline).to_list(length=limit)

async def cann_claim_gt(user_id, claim_type):
    return await db.Claims.find_one({"user_id": user_id, "claim_type": claim_type})

async def update_claim_time_gt(user_id, claim_type):
    await db.Claims.update_one(
        {"user_id": user_id, "claim_type": claim_type},
        {"$set": {"last_claim_time": time.time()}},
        upsert=True
    )
