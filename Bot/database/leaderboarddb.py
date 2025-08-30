from datetime import datetime
from Bot.database import db

async def fetch_leaderboard_data(user_ids=None):
    pipeline = [
        {"$match": {"user_id": {"$in": user_ids}} if user_ids else {}},
        {"$unwind": "$images"},
        {
            "$group": {
                "_id": "$user_id",
                "user_name": {"$first": "$user_name"},
                "total_characters": {"$sum": "$images.count"},
                "total_unique_characters": {"$sum": 1},
            }
        },
        {"$sort": {"total_characters": -1}},
        {"$limit": 10},
    ]
    return await db.Collection.aggregate(pipeline).to_list(length=10)

async def fetch_top_chats():
    return await db.Groups.find().sort("smash_count", -1).limit(10).to_list(length=10)

async def fetch_today_top_collectors():
    today_date = datetime.utcnow().date().isoformat()
    return await db.Tdsmashes.find({"date": today_date}).sort("smash_count", -1).limit(10).to_list(length=10)

async def fetch_grabtoken_leaderboard(member_ids=None):
    pipeline = [
        {"$match": {"user_id": {"$in": member_ids}} if member_ids else {}},
        {
            "$project": {
                "_id": "$user_id",
                "user_name": 1,
                "total_grabtokens": "$grabtoken"
            }
        },
        {"$match": {"total_grabtokens": {"$gt": 0}}},
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

async def add_daily_rewards( user_id, amount, first_name):
    await db.GrabToken.update_one(
        {"user_id": user_id},
        {
            "$inc": {"grabtokens": amount},
            "$set": {"user_name": first_name}
        },
        upsert=True
    )

async def get_daily_collectors(date):
    return await db.GrabToken.find({"last_updated_date": date})\
        .sort("daily_tokens", -1)\
        .to_list(length=None) 
        
async def fetch_top_grabtoken_users_today(today_ist):
    return await db.GrabToken.find({"last_updated_date": today_ist})\
        .sort("daily_tokens", -1)\
        .to_list(length=None)
        
async def get_global_top_smashers(character_id):
    collections = await db.Collection.find({"images.image_id": character_id}).to_list(length=None)
    
    smashers = {}
    for collection in collections:
        for image in collection["images"]:
            if image["image_id"] == character_id and not image.get("given", False):
                user_id = collection["user_id"]
                if user_id not in smashers:
                    smashers[user_id] = 0
                smashers[user_id] += image["count"]
    
    return sorted(smashers.items(), key=lambda x: x[1], reverse=True)[:5] 

async def get_leaderboard_data():
    collections = await db.Collection.find({}).to_list(length=None)
    leaderboard = []
    for user_collection in collections:
        total_characters = sum(image["count"] for image in user_collection["images"])
        total_unique_characters = len(user_collection["images"])
        leaderboard.append({
            "user_id": user_collection["user_id"],
            "total_characters": total_characters,
            "total_unique_characters": total_unique_characters
        })
    leaderboard.sort(key=lambda x: x["total_characters"], reverse=True)
    return leaderboard

async def get_chat_leaderboard_data(member_ids: list):
    chat_leaderboard = []
    for uid in member_ids:
        collection = await db.Collection.find_one({"user_id": uid})
        if collection and collection.get("images"):
            total_chars = sum(img["count"] for img in collection["images"])
            unique_chars = len(collection["images"])
            chat_leaderboard.append({
                "user_id": uid,
                "total_characters": total_chars,
                "total_unique_characters": unique_chars
            })
    chat_leaderboard.sort(key=lambda x: x["total_characters"], reverse=True)
    return chat_leaderboard
