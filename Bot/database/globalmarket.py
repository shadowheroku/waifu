from Bot.database import db 
from Bot.database.smashdb import update_smashed_image, remove_smash_image
from bson.objectid import ObjectId
from Bot.database.grabtokendb import decrease_grab_token , add_grab_token


class GlobalMarket:
    async def list_player(self, user_id, player_id, price, user_name=None):
        user_collection = await db.Collection.find_one({"user_id": user_id})
        if not user_collection or not any(img["image_id"] == player_id for img in user_collection.get("images", [])):
            return None

        await remove_smash_image(user_id, player_id, user_name)

        listing = {
            "listed_by": user_id,
            "player_id": player_id,
            "price": price
        }
        result = await db.Market.insert_one(listing)
        return result.inserted_id

    async def unlist_player(self, listing_id, user_id):
        listing = await db.Market.find_one({"_id": ObjectId(listing_id), "listed_by": user_id})
        if not listing:
            return False

        await update_smashed_image(user_id, listing["player_id"])
        
        await db.Market.delete_one({"_id": ObjectId(listing_id)})
        return True

    async def buy_player(self, listing_id, buyer_id, user_name=None):
        listing = await db.Market.find_one({"_id": ObjectId(listing_id)})
        if not listing:
            return False

        seller_id = listing["listed_by"]
        price = listing["price"]
        player_id = listing["player_id"]

        if not await decrease_grab_token(buyer_id, price, user_name):
            return False

        try:
            await add_grab_token(seller_id, price)
            await update_smashed_image(buyer_id, player_id, user_name)
            await db.Market.delete_one({"_id": ObjectId(listing_id)})
            return True
        except Exception as e:
            await add_grab_token(buyer_id, price)
            raise e

    async def get_market_listings(self, page=1, per_page=10):
        skip = (page - 1) * per_page
        cursor = db.Market.find().skip(skip).limit(per_page)
        listings = await cursor.to_list(length=per_page)
        total = await db.Market.count_documents({})
        return listings, total

    async def search_listings(self, player_id=None, max_price=None, seller_id=None):
        query = {}
        if player_id:
            query["player_id"] = player_id
        if max_price:
            query["price"] = {"$lte": max_price}
        if seller_id:
            query["listed_by"] = seller_id
            
        cursor = db.Market.find(query)
        return await cursor.to_list(None)