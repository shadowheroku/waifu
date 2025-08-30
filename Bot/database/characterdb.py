from Bot.database import db
import random 
from functools import lru_cache
import datetime
from pytz import timezone
from Bot.database.smashdb import get_global_smash_count

async def get_total_uploaded_characters():
    return await db.Characters.count_documents({})

async def get_all_images():
    return await db.Characters.find({}).to_list(length=None)    

async def get_anime_total_characters(anime_id: str):
    return await db.Characters.count_documents({"anime_id": anime_id})

async def get_character_details(image_id):
    return await db.Characters.find_one({"id": image_id})

async def get_all_characters_by_rarity(rarity):
    return await db.Characters.find({"rarity": rarity}).to_list(length=None)

async def get_character_by_anime(anime_name):
    return await db.Characters.find({"anime": {"$regex": f"^{anime_name}$", "$options": "i"}}).to_list(length=100)

async def total_character_in_anime(anime_id):
    return await db.Characters.count_documents({"anime_id": anime_id})

async def get_character(character_id):
    return await get_character_details(character_id)

async def get_character_check_details(character_id):
    character = await get_character_details(character_id)
    if not character:
        return None
    
    global_smash_count, unique_user_count = await get_global_smash_count(character_id)
    
    return {
        "character": character,
        "unique_user_count": unique_user_count
    }

async def get_top_five_less_smashed_character_by_rarity(rarity):
    pipeline = [
        {"$match": {"rarity": rarity}},
        {"$lookup": {
            "from": "Collection",
            "let": {"char_id": "$id"},
            "pipeline": [
                {"$unwind": "$images"},
                {"$match": {"$expr": {"$eq": ["$images.image_id", "$$char_id"]}}},
                {"$group": {"_id": "$user_id"}}
            ],
            "as": "collectors"
        }},
        {"$addFields": {"unique_user_count": {"$size": "$collectors"}}},
        {"$sort": {"unique_user_count": 1}},
        {"$limit": 5}
    ]
    
    return await db.Characters.aggregate(pipeline).to_list(length=5)

@lru_cache(maxsize=1)
def get_rarity_weights(mode="random"):

    if mode == "random":
        return {
            "Common": 50,
            "Rare": 25,
            "Medium": 40,
            "Legendary": 20,
            "Exclusive": 8,
            "Cosmic": 5,
            "Limited Edition": 3,
            "Ultimate": 1,
            "Supreme": 0,
            "Uncommon": 0,
            "Epic": 0,
            "Mythic": 0,
            "Divine": 0,
            "Ethereal": 0,
            "Premium": 0
        }
    elif mode == "claim":
        return {
            "Common": 60,
            "Rare": 25,
            "Medium": 45,
            "Legendary": 15,
            "Exclusive": 3,
            "Cosmic": 1,
            "Limited Edition": 0,
            "Ultimate": 0,
            "Uncommon": 0,
            "Epic": 0,
            "Mythic": 0,
            "Divine": 0,
            "Ethereal": 0,
            "Premium": 0
        }
    elif mode == "propose":
        return {
            "Common": 50,
            "Rare": 25,
            "Medium": 40,
            "Legendary": 20,
            "Exclusive": 2,
            "Cosmic": 1,
            "Limited Edition": 0,
            "Ultimate": 0,
            "Uncommon": 45,
            "Epic": 15,
            "Mythic": 2,
            "Divine": 25,
            "Ethereal": 3,
            "Premium": 0
        }

async def get_random_character():
    # Check for video character (0.1% chance)
    if random.random() < 0.001:  # 0.1%
        video_chars = await db.Characters.find({"is_video": True}).to_list(length=None)
        if video_chars:
            return random.choice(video_chars)

    ist = timezone('Asia/Kolkata')
    current_date = datetime.datetime.now(ist).date()
    
    if random.random() < 0.2:  
        date_restricted_chars = await get_characters_by_date_range(current_date)
        if date_restricted_chars:
            return random.choice(date_restricted_chars)
    
    base_rarity_weights = get_rarity_weights("random")

    counter = await db.Ultimate.find_one({"_id": "Ultimate"})
    current_count = counter["count"] if counter else 0

    adjusted_weights = base_rarity_weights.copy()
    
    # Now allows up to 80 Ultimate drops
    if current_count >= 80:
        adjusted_weights["Ultimate"] = 0

    rarities = list(adjusted_weights.keys())
    weights = list(adjusted_weights.values())

    selected_rarity = random.choices(rarities, weights=weights, k=1)[0]

    if selected_rarity == "Ultimate":
        update_result = await db.Ultimate.update_one(
            {"_id": "Ultimate", "count": {"$lt": 80}},  # Updated limit
            {"$inc": {"count": 1}},
            upsert=True
        )

        if not update_result.modified_count:
            adjusted_weights["Ultimate"] = 0
            rarities = list(adjusted_weights.keys())
            weights = list(adjusted_weights.values())
            selected_rarity = random.choices(rarities, weights=weights, k=1)[0]

    characters = await db.Characters.find({"rarity": selected_rarity}).to_list(length=None)
    
    if not characters:
        raise ValueError(f"No characters found for rarity: {selected_rarity}")

    return random.choice(characters)


async def get_all_characters_by_event(event_name):
    return await db.Characters.find({"event": event_name}).to_list(length=None)

async def get_characters_by_date_range(current_date=None):
    if current_date is None:
        ist = timezone('Asia/Kolkata')
        current_date = datetime.datetime.now(ist).date()
    
    current_date_str = current_date.isoformat()
    
    query = {
        "date_range.start": {"$lte": current_date_str},
        "date_range.end": {"$gte": current_date_str}
    }
    
    return await db.Characters.find(query).to_list(length=None)

async def get_random_character_by_date_range(current_date=None):

    if current_date is None:
        ist = timezone('Asia/Kolkata')
        current_date = datetime.datetime.now(ist).date()
    

    current_date_str = current_date.isoformat()
    

    query = {
        "date_range.start": {"$lte": current_date_str},
        "date_range.end": {"$gte": current_date_str}
    }
    
    characters = await db.Characters.find(query).to_list(length=None)
    
    if not characters:

        return await get_random_character()
    
    return random.choice(characters)

async def get_random_character_for_claim():
    # Check for video character (0.05% chance)
    if random.random() < 0.0005:  # 0.05%
        video_chars = await db.Characters.find({"is_video": True}).to_list(length=None)
        if video_chars:
            return random.choice(video_chars)

    rarity_weights = get_rarity_weights("claim")

    rarities = list(rarity_weights.keys())
    weights = list(rarity_weights.values())

    selected_rarity = random.choices(rarities, weights=weights, k=1)[0]

    characters = await db.Characters.find({"rarity": selected_rarity}).to_list(length=None)

    if not characters:
        raise ValueError(f"No characters found for rarity: {selected_rarity}")

    return random.choice(characters)

async def get_random_character_for_propose():
    # Check for video character (0.01% chance)
    if random.random() < 0.0001:  # 0.01%
        video_chars = await db.Characters.find({"is_video": True}).to_list(length=None)
        if video_chars:
            return random.choice(video_chars)
   
    rarity_weights = get_rarity_weights("propose")

    rarities = list(rarity_weights.keys())
    weights = list(rarity_weights.values())

    selected_rarity = random.choices(rarities, weights=weights, k=1)[0]

    characters = await db.Characters.find({"rarity": selected_rarity}).to_list(length=None)

    if not characters:
        raise ValueError(f"No characters found for rarity: {selected_rarity}")

    return random.choice(characters)