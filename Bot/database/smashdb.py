from Bot.database import db 

async def get_user_smash_count(user_id: int):
    user_smash_data = await db.SmashCount.find_one({"user_id": user_id})
    return user_smash_data["smash_count"] if user_smash_data else 0 

async def update_smashed_image(user_id, image_id, user_name=None, given=False):
    update_data = {
        "$inc": {"images.$[elem].count": 1},
    }
    
    if user_name:
        update_data["$set"] = {"user_name": user_name}
    
    if given:
        update_data["$set"] = update_data.get("$set", {})
        update_data["$set"]["images.$[elem].given"] = True
    
    result = await db.Collection.update_one(
        {"user_id": user_id, "images.image_id": image_id},
        update_data,
        array_filters=[{"elem.image_id": image_id}]
    )
    
    if result.matched_count == 0:
        image_data = {"image_id": image_id, "count": 1}
        
        if given:
            image_data["given"] = True
            
        push_data = {"$push": {"images": image_data}}
        
        if user_name:
            push_data["$set"] = {"user_name": user_name}
        
        await db.Collection.update_one(
            {"user_id": user_id},
            push_data,
            upsert=True
        )


async def remove_smashed_image(user_id, image_id):
    await db.Collection.update_one(
        {"user_id": user_id, "images.image_id": image_id},
        {"$inc": {"images.$[elem].count": -1}},
        array_filters=[{"elem.image_id": image_id}]
    )
    
    await db.Collection.update_one(
        {"user_id": user_id},
        {"$pull": {"images": {"image_id": image_id, "count": {"$lte": 0}}}}
    )
    
    user_doc = await db.Collection.find_one(
        {"user_id": user_id},
        {"images": 1, "_id": 0}
    )
    
    if not user_doc or not user_doc.get("images"):
        await db.Collection.delete_one({"user_id": user_id})

async def add_specific_image(user_id, image_id, user_name=None, given=False):
    update_data = {
        "$inc": {"images.$[elem].count": 1},
    }
    
    if user_name:
        update_data["$set"] = {"user_name": user_name}
    
    if given:
        update_data["$set"] = update_data.get("$set", {})
        update_data["$set"]["images.$[elem].given"] = True
    
    result = await db.Collection.update_one(
        {"user_id": user_id, "images.image_id": image_id},
        update_data,
        array_filters=[{"elem.image_id": image_id}]
    )
    
    if result.matched_count == 0:
        image_data = {"image_id": image_id, "count": 1}
        
        if given:
            image_data["given"] = True
            
        push_data = {"$push": {"images": image_data}}
        
        if user_name:
            push_data["$set"] = {"user_name": user_name}
        
        await db.Collection.update_one(
            {"user_id": user_id},
            push_data,
            upsert=True
        )

async def get_global_smash_count(image_id):
    pipeline = [
        {"$unwind": "$images"},
        {"$match": {
            "images.image_id": image_id,
            "$or": [
                {"images.given": {"$exists": False}},
                {"images.given": False}
            ]
        }},
        {"$group": {
            "_id": None,
            "total_count": {"$sum": "$images.count"},
            "unique_users": {"$addToSet": "$user_id"}
        }}
    ]
    
    result = await db.Collection.aggregate(pipeline).to_list(length=1)
    
    if result:
        total_smash_count = result[0]["total_count"]
        unique_user_count = len(result[0]["unique_users"])
    else:
        total_smash_count, unique_user_count = 0, 0
        
    return total_smash_count, unique_user_count

async def remove_smash_image(user_id, img_id, user_name=None):
    update_data = {
        "$inc": {"images.$[elem].count": -1}
    }
    
    if user_name:
        update_data["$set"] = {"user_name": user_name}
    
    await db.Collection.update_one(
        {"user_id": user_id, "images.image_id": img_id},
        update_data,
        array_filters=[{"elem.image_id": img_id}]
    )
    
    await db.Collection.update_one(
        {"user_id": user_id},
        {"$pull": {"images": {"image_id": img_id, "count": {"$lte": 0}}}}
    )

async def get_smash_count_data(user_id):
    return await db.SmashCount.find_one({"user_id": user_id})


    
async def get_chat_smashers(client, chat_id, character_id):
    member_ids = [member.user.id async for member in client.get_chat_members(chat_id)]
    smashers = []
    for user_id in member_ids:
        user_collection = await db.Collection.find_one({"user_id": user_id})
        if user_collection:
            for image in user_collection.get("images", []):
                if image["image_id"] == character_id and not image.get("given", False):
                    smashers.append({"user_id": user_id, "count": image["count"]})
    return smashers