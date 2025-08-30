from Bot.database import db 

async def get_icaption_preference(user_id):
    preference = await db.Preference.find_one(
        {"user_id": user_id}, 
        {"icaption": 1, "_id": 0}
    )
    return preference.get("icaption", "Caption 1") if preference else "Caption 1"

async def get_user_preferences(user_id: int):
    return await db.Preference.find_one({"user_id": user_id}) or {}

async def get_smode_preference(user_id):
    preference = await db.Preference.find_one(
        {"user_id": user_id},
        {"default": 1, "rarity": 1, "anime": 1, "_id": 0}
    )
    return preference if preference else {"default": "enable", "rarity": None, "anime": None}

async def get_fav_character(user_id):
    fav_entry = await db.Preference.find_one(
        {"user_id": user_id}, 
        {"fav_character_id": 1, "_id": 0}
    )
    return fav_entry.get("fav_character_id") if fav_entry else None
    
# Helper function to get custom title by user_id
async def get_custom_title_by_user_id(user_id):
    user_data = await db.GrabToken.find_one(
        {"user_id": user_id}, 
        {"custom_title": 1, "_id": 0}
    )
    return user_data.get("custom_title") if user_data else None

# Helper function to get custom profile picture URL by user_id
async def get_custom_pfp_url_by_user_id(user_id):
    user_data = await db.GrabToken.find_one(
        {"user_id": user_id}, 
        {"custom_pfp_url": 1, "_id": 0}
    )
    return user_data.get("custom_pfp_url") if user_data else None

async def unfav_player(user_id):
    await db.Preference.delete_one({"user_id": user_id})

async def fav_player(user_id, player_id):
    await db.Preference.update_one(
        {"user_id": user_id},
        {"$set": {"fav_character_id": player_id}},
        upsert=True
    )
    
async def smode_detaile(user_id):
    await db.Preference.update_one(
        {"user_id": user_id},
        {"$set": {"default": "disable", "detailed": "enable"}},
        upsert=True
    )

async def smode_alpha(user_id):
    await db.Preference.update_one(
        {"user_id": user_id},
        {"$set": {"default": "disable","anime": "AnimeAlpha"}},
        upsert=True
    )

async def smode_anime_coun(user_id):
    await db.Preference.update_one(
        {"user_id": user_id},
        {"$set": {"default": "disable","anime": "AnimeCount"}},
        upsert=True
    )

async def smode_defaul(user_id):
    await db.Preference.update_one(
        {"user_id": user_id},
        {"$set": {"default": "enable", "rarity": None, "anime": None, "detailed": None}},
        upsert=True
    )

async def smode_rarit(user_id, rarity):
    await db.Preference.update_one(
        {"user_id": user_id},
        {"$set": {"default": "disable", "rarity": rarity}},
        upsert=True
    )

async def cmode_caption(user_id, selected_mode):
    await db.Preference.update_one(
        {"user_id": user_id},
        {"$set": {"icaption": selected_mode}},
        upsert=True
    )