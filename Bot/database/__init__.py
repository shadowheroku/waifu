from motor.motor_asyncio import AsyncIOMotorClient
from Bot.config import MONGO_URL , DATABASE_NAME

MAX_POOL_SIZE = 100
MIN_POOL_SIZE = 10
MAX_IDLE_TIME_MS = 30000  

try:
    client = AsyncIOMotorClient(
        MONGO_URL,
        maxPoolSize=MAX_POOL_SIZE,
        minPoolSize=MIN_POOL_SIZE,
        maxIdleTimeMS=MAX_IDLE_TIME_MS,
        connectTimeoutMS=5000,
        socketTimeoutMS=10000,
        serverSelectionTimeoutMS=5000,
        waitQueueTimeoutMS=5000,
        retryWrites=True,
        w="majority"  
    )
    db = client[DATABASE_NAME]
except Exception as e:
    raise

tgroups_collection = db['TGroups']
db.Characters = db["Characters"]
db.Anime = db["Anime"]
db.Collection = db["Collection"]
db.Banned = db["Banned"]
db.Sudo = db["Sudo"]
db.Preference = db["Preference"]
db.Gtreq = db["Gtreq"]
db.Gtusers = db["Gtusers"]
db.Users = db["Users"]
db.RedeemCodes = db["RedeemCodes"]
db.RedeemCodes = db["RedeemCodes"]
db.GrabToken = db["GrabToken"]
db.Bets = db["Bets"]

