from Bot.database import db
from texts import WAIFU , ANIME

async def capitalize_name(name):
    return " ".join(word.capitalize() for word in name.split())

async def rename_anime_names_db():
    anime_list = await db.Anime.find({}).to_list(length=None)

    updated_count = 0
    for anime in anime_list:
        original_name = anime["name"]
        new_name = await capitalize_name(original_name)

        if original_name != new_name:
            anime_id = anime["anime_id"]
            await db.Anime.update_one(
                {"anime_id": anime_id},
                {"$set": {"name": new_name}}
            )
            await db.Characters.update_many(
                {"anime_id": anime_id},
                {"$set": {"anime": new_name}}
            )
            updated_count += 1

    return f"Renamed {updated_count} {ANIME} names successfully."

async def rename_character_names_db():
    characters = await db.Characters.find({}).to_list(length=None)

    updated_count = 0
    for character in characters:
        original_name = character["name"]
        new_name = await capitalize_name(original_name)

        if original_name != new_name:
            character_id = character["id"]
            await db.Characters.update_one(
                {"id": character_id},
                {"$set": {"name": new_name}}
            )
            updated_count += 1

    return f"Renamed {updated_count} {WAIFU} names successfully." 