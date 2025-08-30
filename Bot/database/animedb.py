from Bot.database import db
from Bot.database.iddb import get_next_anime_id
from Bot.database.privacydb import is_user_sudo, is_user_og
from Bot.config import OWNERS

async def create_anime(anime_id , anime_name):
    await db.Anime.insert_one({"name": anime_name, "anime_id": anime_id})
    
async def has_permission(user_id):
    return user_id in OWNERS or await is_user_sudo(user_id) or await is_user_og(user_id)

async def get_anime_details_by_anime_id(anime_id):
    return await db.Anime.find_one({"anime_id": anime_id})

async def get_anime_by_first_letter(first_letter):
    first_letter = first_letter.upper()
    
    anime_list = await db.Anime.find(
        {"name": {"$regex": f"^{first_letter}", "$options": "i"}},
        {"name": 1, "anime_id": 1, "_id": 0}
    ).to_list(length=None)
    
    return anime_list

async def get_anime_id(anime_name):
    anime = await db.Anime.find_one(
        {"name": anime_name}, 
        {"anime_id": 1, "_id": 0}
    )
    
    if anime:
        return anime["anime_id"]
    else:
        anime_id = await get_next_anime_id()
        await db.Anime.insert_one({"name": anime_name, "anime_id": anime_id})
        return anime_id
    
async def rename_anime_logic(anime_id, new_anime_name):
 
    anime = await db.Anime.find_one({"anime_id": anime_id})
    if not anime:
        return f"No anime found with ID {anime_id}."


    await db.Anime.update_one(
        {"anime_id": anime_id}, 
        {"$set": {"name": new_anime_name}}
    )
    

    await db.Characters.update_many(
        {"anime_id": anime_id}, 
        {"$set": {"anime": new_anime_name}}
    )

    return f"Anime with ID {anime_id} has been renamed to {new_anime_name}."

async def list_animes(page, page_size):
    offset = (page - 1) * page_size
    animes = await db.Anime.find().skip(offset).limit(page_size).to_list(length=page_size)
    total_animes = await db.Anime.count_documents({})
    
    return animes, total_animes

async def get_anime(anime_name):
    return await db.Anime.find({"name": {"$regex": anime_name, "$options": "i"}}).to_list(length=100)

async def temp_anime_creation(anime_creation_id , anime_name):
    await db.TempAnimeCreation.insert_one({"creation_id": anime_creation_id, "anime_name": anime_name})
    
async def find_temp_anime_creation(anime_creation_id):
    return await db.TempAnimeCreation.find_one({"creation_id": anime_creation_id})


async def delete_temp_anime_creation(anime_creation_id):
    await db.TempAnimeCreation.delete_one({"creation_id": anime_creation_id}) 


async def search_character(query):
    return await db.Characters.find({
                "$or": [
                    {"name": {"$regex": query, "$options": "i"}},  # Search by character name
                    {"anime": {"$regex": query, "$options": "i"}},# Search by anime name
                    {"rarity": {"$regex": query, "$options": "i"}} 
                ]
            }).to_list(length=None)