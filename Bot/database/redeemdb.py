from Bot.database import db
import time
from datetime import datetime
from Bot.database.grabtokendb import get_current_ist_date
from datetime import datetime
import pytz

IST = pytz.timezone("Asia/Kolkata")


async def find_redeem_code(code: str):
    return await db.RedeemCodes.find_one({"code": code})

async def create_redeem_code(code: str, character_id: str, redemption_count: int):
    return await db.RedeemCodes.insert_one({
        "code": code,
        "character_id": character_id,
        "redemption_count": redemption_count,
        "redeemed_by": []
    })

async def update_redeem_code(code: str, user_id: int):
    return await db.RedeemCodes.update_one(
        {"code": code},
        {"$push": {"redeemed_by": user_id}}
    )

async def delete_redeem_code(code: str):
    return await db.RedeemCodes.delete_one({"code": code}) 


async def create_redeem_code_shortner(code, user_id, amount, user_name=None):
    await db.RedeemCodes.insert_one({
        "code": code,
        "user_id": user_id,
        "amount": amount,
        "claimed": False,
        "created_at": time.time(),
        "created_by_name": user_name,
        "claimed_by": None,
        "claimed_by_name": None,
        "claimed_at": None
    })

async def get_redeem_code_shortner(code):
    return await db.RedeemCodes.find_one({"code": code})



async def claim_redeem_code_shortner(code, user_id, user_name=None):
    result = await db.RedeemCodes.find_one_and_update(
        {"code": code, "claimed": False},
        {
            "$set": {
                "claimed": True,
                "claimed_by": user_id,
                "claimed_by_name": user_name or "Unknown",
                "claimed_at": time.time()
            }
        },
        return_document=True
    )
    
    return result

async def get_user_daily_usage_shortner(user_id, date=None):
    if date is None:
        date = get_current_ist_date()
    
    date_obj = datetime.strptime(date, "%Y-%m-%d")
    start_of_day = IST.localize(datetime.combine(date_obj, datetime.min.time())).timestamp()
    end_of_day = IST.localize(datetime.combine(date_obj, datetime.max.time())).timestamp()

    count = await db.RedeemCodes.count_documents({
        "user_id": user_id,
        "created_at": {"$gte": start_of_day, "$lte": end_of_day}
    })
    
    return count

async def cleanup_expired_codes_shortner(expiry_time=86400):
    current_time = time.time()
    expiry_threshold = current_time - expiry_time
    
    result = await db.RedeemCodes.delete_many({
        "created_at": {"$lt": expiry_threshold},
        "claimed": False
    })
    
    return result.deleted_count 