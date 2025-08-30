from Bot.database import db
import time

async def get_bot_stats():
    rarities = {
        "Common": "⚪",
        "Medium": "🟢",
        "Rare": "🟠",
        "Legendary": "🟡",
        "Exclusive": "💮",
        "Cosmic": "💠",
        "Limited Edition": "🔮",
        "Ultimate": "🔱",
        "Supreme": "👑",
        "Uncommon": "🟤", 
        "Epic": "⚜️", 
        "Mythic": "🔴",
        "Divine": "💫",
        "Ethereal": "❄️", 
        "Premium": "🧿" 
    }
    
    group_count = await db.TGroups.count_documents({})
    user_count = await db.TotalUsers.count_documents({})
    total_characters = await db.Characters.count_documents({})
    harem_count = await db.Collection.count_documents({})
    
    rarity_counts = {}
    for rarity, sign in rarities.items():
        count = await db.Characters.count_documents({"rarity": rarity})
        rarity_counts[rarity] = (sign, count)
    
    return {
        "group_count": group_count,
        "user_count": user_count,
        "total_characters": total_characters,
        "harem_count": harem_count,
        "rarity_counts": rarity_counts
    } 
    
async def get_redeem_stats():
    current_time = time.time()
    expired_time = current_time - 86400
    
    total_codes = await db.RedeemCodes.count_documents({})
    claimed_codes = await db.RedeemCodes.count_documents({"claimed": True})
    unclaimed_codes = await db.RedeemCodes.count_documents({"claimed": False})
    expired_codes = await db.RedeemCodes.count_documents({
        "claimed": False,
        "created_at": {"$lt": expired_time}
    })
    recent_codes = await db.RedeemCodes.count_documents({
        "created_at": {"$gt": expired_time}
    })
    recent_claims = await db.RedeemCodes.count_documents({
        "claimed": True,
        "claimed_at": {"$gt": expired_time}
    })
    
    pipeline = [
        {"$group": {"_id": "$user_id", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
        {"$limit": 5}
    ]
    top_generators = await db.RedeemCodes.aggregate(pipeline).to_list(length=5)
    
    top_generators_info = []
    for generator in top_generators:
        user_id = generator["_id"]
        count = generator["count"]
        user_info = await db.GrabToken.find_one({"user_id": user_id})
        user_name = user_info.get("user_name", f"User {user_id}") if user_info else f"User {user_id}"
        top_generators_info.append({"user_id": user_id, "user_name": user_name, "count": count})
    
    return {
        "total_codes": total_codes,
        "claimed_codes": claimed_codes,
        "unclaimed_codes": unclaimed_codes,
        "expired_codes": expired_codes,
        "recent_codes": recent_codes,
        "recent_claims": recent_claims,
        "top_generators": top_generators_info
    }

async def clear_expired_redeem_codes():
    current_time = time.time()
    expired_time = current_time - 86400
    
    result = await db.RedeemCodes.delete_many({
        "claimed": False,
        "created_at": {"$lt": expired_time}
    })
    
    return result.deleted_count 