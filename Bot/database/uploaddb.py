from Bot.database import db
from Bot.database.iddb import get_next_id
from Bot.database.animedb import get_anime_details_by_anime_id
from Bot import RARITY_MAPPING


async def get_total_waifus():
    return await db.Characters.count_documents({})

async def get_total_animes():
    return await db.Anime.count_documents({})

async def get_total_harems():
    return await db.Collection.count_documents({})

async def upload_waifu(waifu_data):
    await db.Characters.insert_one(waifu_data)

async def force_delete(waifu_id):

    await db.Characters.delete_one({"id": waifu_id})
    
    await db.Collection.update_many(
        {"images.image_id": waifu_id},
        {"$pull": {"images": {"image_id": waifu_id}}}
    )
    
async def update_name(waifu_id, new_name):
    await db.Characters.update_one({"id": waifu_id}, {"$set": {"name": new_name}})
    
async def find_anime(anime_id):
    return await db.Anime.find_one({"anime_id": anime_id})

async def find_waifu(waifu_id):
    return await db.Characters.find_one({"id": waifu_id})

async def update_anime(waifu_id , anime_id, anime_name):
    await db.Characters.update_one({"id": waifu_id}, {"$set": {"anime_id": anime_id, "anime": anime_name}})
    
async def update_rarity(waifu_id , rarity , rarity_sign):
    await db.Characters.update_one({"id": waifu_id}, {
            "$set": {"rarity": rarity, "rarity_sign": rarity_sign}
        })
async def remove_event(waifu_id):
    await db.Characters.update_one(
            {"id": waifu_id},
            {"$unset": {"event": "", "event_sign": ""}}
        )
async def update_event(waifu_id , event , event_sign):
    await db.Characters.update_one({"id": waifu_id}, {
            "$set": {"event": event, "event_sign": event_sign}
        })

async def update_image(waifu_id , image_url):
    await db.Characters.update_one({"id": waifu_id}, {"$set": {"img_url": image_url}})    

async def reset_waifu(waifu_id):
    await db.Collection.update_many(
        {"images.image_id": waifu_id},
        {"$pull": {"images": {"image_id": waifu_id}}}
    )

async def get_ipl_players():
    return await db.Characters.find({"event": "IPL 2025"}).to_list(length=None)

RARITY_MAPPING_FOR_STORE = {
    "1": {"name": "Uncommon", "sign": "🟤"},
    "2": {"name": "Epic", "sign": "⚜️"},
    "3": {"name": "Mythic", "sign": "🔴"},
    "4": {"name": "Divine", "sign": "💫"},
    "5": {"name": "Ethereal", "sign": "❄️"}
}

async def get_rarity_info_for_store(rarity_key):

    return RARITY_MAPPING_FOR_STORE.get(rarity_key)

async def get_rarity_info(rarity_key):

    return RARITY_MAPPING.get(rarity_key)

async def get_anime_for_upload(anime_id):

    return await get_anime_details_by_anime_id(anime_id)

async def save_character_to_store(upload_data):

    character_id = await get_next_id()
    character_doc = {
        "id": str(character_id),
        "img_url": upload_data['img_url'],
        "name": upload_data['name'],
        "anime": upload_data.get('anime', "Unknown"),
        "anime_id": upload_data['anime_id'],
        "rarity": upload_data['rarity'],
        "rarity_sign": upload_data['rarity_sign']
    }

    if upload_data.get("event"):
        character_doc["event"] = upload_data["event"]
        character_doc["event_sign"] = upload_data["event_sign"]

    await db.Characters.insert_one(character_doc)
    return character_id 