from Bot.database import db
from pyrogram.types import User
from Bot.database.collectiondb import get_user_collection
from Bot.database.characterdb import get_character_details
from Bot.database.leaderboarddb import get_leaderboard_data
from Bot.database.grabtokendb import get_user_balance
from Bot.database.bankdb import get_bank_balance


async def get_user_name(user_id):
    user_doc = await db.Collection.find_one(
        {"user_id": user_id}, 
        {"user_name": 1, "_id": 0}
    )
    return user_doc.get("user_name") if user_doc else None

async def get_claimed_achievements(user_id):
    return await db.ClaimedAchievements.find_one({"user_id": user_id})

async def update_claimed_achievements(user_id, claimed_rewards):
    await db.ClaimedAchievements.update_one({"user_id": user_id}, {"$set": {"claimed": claimed_rewards}}, upsert=True)
    
async def get_user_info(user: User):

    id = user.id
    first_name = user.first_name 
    mention = user.mention 
    username = user.username 
    dc = user.dc_id 
    
    # Get financial data
    wallet_balance = await get_user_balance(id) 
    bank_balance = await get_bank_balance(id) 
    
    # Get collection data
    user_collection = await get_user_collection(id)
    total_uploaded_characters = await db.Characters.count_documents({})
    total_characters = sum(image["count"] for image in user_collection["images"]) if user_collection else 0
    unique_characters = len(user_collection["images"]) if user_collection else 0
    harem_percentage = (unique_characters / total_uploaded_characters) * 100 if total_uploaded_characters > 0 else 0
    
    # Initialize rarity counts
    rarities = {
        "Legendary": 0, "Rare": 0, "Medium": 0, 
        "Common": 0, "Exclusive": 0, "Cosmic": 0, "Limited Edition": 0, "Ultimate": 0,
        "Supreme": 0, "Uncommon": 0, "Epic": 0, "Mythic": 0,
        "Divine": 0, "Ethereal": 0, "Premium": 0
    }
    
    # Count rarities in collection
    if user_collection:
        for image in user_collection.get("images", []):
            character = await get_character_details(image["image_id"])
            if character and character["rarity"] in rarities:
                rarities[character["rarity"]] += 1
    
    # Get global position
    global_leaderboard = await get_leaderboard_data()
    global_position = next((index + 1 for index, entry in enumerate(global_leaderboard) if entry["user_id"] == id), len(global_leaderboard))
    
    return {
        "user_id": id,
        "first_name": first_name,
        "username": username,
        "mention": mention,
        "dc_id": dc,
        "wallet_balance": wallet_balance,
        "bank_balance": bank_balance,
        "total_characters": total_characters,
        "unique_characters": unique_characters,
        "total_uploaded_characters": total_uploaded_characters,
        "harem_percentage": harem_percentage,
        "rarities": rarities,
        "global_position": global_position
    }


