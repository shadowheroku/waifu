from Bot.database import db

async def create_bank_account_if_not_exists(user_id):
    await db.Bank.update_one(
        {"user_id": user_id},
        {"$setOnInsert": {"bank_balance": 0}},
        upsert=True
    )

async def deposit_to_bank(user_id, amount):
    await db.Bank.update_one(
        {"user_id": user_id},
        {"$inc": {"bank_balance": amount}},
        upsert=True
    )

async def withdraw_from_bank(user_id, amount):
    result = await db.Bank.find_one_and_update(
        {"user_id": user_id, "bank_balance": {"$gte": amount}},
        {"$inc": {"bank_balance": -amount}},
        return_document=False
    )
    
    return result is not None

async def get_bank_balance(user_id):
    user = await db.Bank.find_one(
        {"user_id": user_id}, 
        {"bank_balance": 1, "_id": 0}
    )
    return user["bank_balance"] if user else 0
