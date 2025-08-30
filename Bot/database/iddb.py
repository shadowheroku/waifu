from Bot.database import db

async def get_next_id():
    counter = await db.Counters.find_one_and_update(
        {"_id": "character_id"},
        {"$inc": {"sequence_value": 1}},
        upsert=True,
        return_document=True
    )
    return counter["sequence_value"]

async def get_next_anime_id():
    counter = await db.Counters.find_one_and_update(
        {"_id": "anime_id"},
        {"$inc": {"sequence_value": 1}},
        upsert=True,
        return_document=True
    )
    return counter["sequence_value"]