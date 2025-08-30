from Bot.database import db
from Bot.database.characterdb import get_character_details
from Bot.database.preferencedb import get_fav_character
from Bot.database.characterdb import get_anime_total_characters

async def get_user_collection(user_id: int):
    return await db.Collection.find_one({"user_id": user_id})

async def update_user_collection(user_id, updated_images):
    await db.Collection.update_one(
        {"user_id": user_id},
        {"$set": {"images": updated_images}},
        upsert=True
    )

async def get_groups_and_users():
    groups_cursor = db.TGroups.find({})
    users_cursor = db.TotalUsers.find({})
    
    groups = [group["group_id"] for group in await groups_cursor.to_list(None)]
    users = [user["user_id"] for user in await users_cursor.to_list(None)]
    
    return groups, users 

async def get_collection_details(user_collection, user_preferences):
    if not user_collection or not user_collection.get("images"):
        return None, None, None, None

    ITEMS_PER_PAGE = 10 if user_preferences.get("detailed") == "enable" else 5

    characters_details = {}
    anime_character_count = {}
    anime_total_characters = {}

    for image in user_collection["images"]:
        character = await get_character_details(image["image_id"])
        if not character:
            continue
            
        characters_details[image["image_id"]] = character

        anime_id = character.get("anime_id")
        if anime_id:
            if anime_id not in anime_character_count:
                anime_character_count[anime_id] = 0
                anime_total_characters[anime_id] = await get_anime_total_characters(anime_id)
            anime_character_count[anime_id] += 1

    sorted_images = user_collection["images"]

    if user_preferences.get("rarity"):
        sorted_images = [
            img for img in sorted_images 
            if img["image_id"] in characters_details and 
               characters_details[img["image_id"]].get("rarity") == user_preferences["rarity"]
        ]

    if user_preferences.get("anime") == "AnimeAlpha":
        sorted_images = sorted(
            sorted_images,
            key=lambda img: characters_details.get(img["image_id"], {}).get("anime", "").lower()
        )
    elif user_preferences.get("anime") == "AnimeCount":
        sorted_images = sorted(
            sorted_images,
            key=lambda img: -anime_character_count.get(
                characters_details.get(img["image_id"], {}).get("anime_id", ""), 0
            )
        )

    return sorted_images, characters_details, anime_character_count, anime_total_characters

async def get_collection_image(user_collection, user_id: int):
    if not user_collection or not user_collection.get("images"):
        return None

    fav_character_id = await get_fav_character(user_id)
    if fav_character_id:
        fav_character = await get_character_details(fav_character_id)
        if (fav_character and 
            fav_character.get("img_url") and 
            any(image["image_id"] == fav_character_id for image in user_collection["images"])):
            return fav_character["img_url"]

    if user_collection["images"]:
        first_character = await get_character_details(user_collection["images"][0]["image_id"])
        if first_character and "img_url" in first_character:
            return first_character["img_url"]

    return None


async def delete_user_collection(user_id):

    collection = await get_user_collection(user_id)
    if not collection:
        return None
        
    collection_data = []
    for img in collection.get("images", []):
        collection_data.extend([str(img["image_id"])] * img["count"])
    
    await db.Collection.delete_one({"user_id": user_id})
    return collection_data 


async def update_user_collection_for_transfer(user_id, collection_data):
    return await db.Collection.update_one(
        {"user_id": user_id},
        {"$set": collection_data},
        upsert=True
    )

async def transfer_collection(from_user_id, to_user_id):

    from_collection = await get_user_collection(from_user_id)
    to_collection = await get_user_collection(to_user_id)

    if not from_collection:
        return False, "The source user does not have any collection."

    await delete_user_collection(to_user_id)

    if not to_collection:
        to_collection = {"user_id": to_user_id, "images": []}

    to_images = {img["image_id"]: img for img in to_collection["images"]}
    for img in from_collection["images"]:
        if img["image_id"] in to_images:
            to_images[img["image_id"]]["count"] += img["count"]
        else:
            to_images[img["image_id"]] = img

    to_collection["images"] = list(to_images.values())

    await update_user_collection_for_transfer(to_user_id, to_collection)

    await delete_user_collection(from_user_id)

    return True, "Collection successfully transferred." 