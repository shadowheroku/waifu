import time
from pyrogram import Client
import Bot.config
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import logging
from rich.console import Console
from rich.logging import RichHandler
from Bot.utils import Command
from Bot.config import GLOG , SUPPORT_CHAT_ID , DATABASE_NAME

LOG_FILE = f"{DATABASE_NAME}.log"

open(LOG_FILE, 'w').close()
    
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s - %(levelname)s] - Cricket - %(message)s",
    datefmt="%d-%b-%y %H:%M:%S",
    handlers=[
        RichHandler(console=Console(), rich_tracebacks=True), 
        logging.FileHandler(LOG_FILE), 
    ]
)

logging.getLogger("httpx").setLevel(logging.ERROR)
logging.getLogger("pyrogram").setLevel(logging.ERROR)

logger = logging.getLogger()


BACKUP_FILE_JSON = "last_backup.json"  


class App(Client):
    def __init__(self):
        super().__init__(
            name="Cricket",
            api_id=Bot.config.api_id,
            api_hash=Bot.config.api_hash,
            bot_token=Bot.config.bot_token,
            workers=40,
            max_concurrent_transmissions=10,
)

app = App()


scheduler = AsyncIOScheduler()

DOWNLOAD_DIR = "downloads"

RARITY_MAPPING = {
    "1": {"name": "Common", "sign": "⚪️"},
    "2": {"name": "Medium", "sign": "🟢"},
    "3": {"name": "Rare", "sign": "🟠"},
    "4": {"name": "Legendary", "sign": "🟡"},
    "5": {"name": "Exclusive", "sign": "💮"},
    "6": {"name": "Cosmic", "sign": "💠"},
    "7": {"name": "Limited Edition", "sign": "🔮"},
    "8": {"name": "Ultimate", "sign": "🔱"},
    "9": {"name": "Supreme", "sign": "👑"},
    "10": {"name": "Uncommon", "sign": "🟤"},
    "11": {"name": "Epic", "sign": "⚜️"},
    "12": {"name": "Mythic", "sign": "🔴"},
    "13": {"name": "Divine", "sign": "💫"},
    "14": {"name": "Ethereal", "sign": "❄️"},
    "15": {"name": "Premium" , "sign" : "🧿"}
}

PRICE_MAPPING = {
    "1": {"name": "Common", "price": "63000"},
    "2": {"name": "Medium", "price": "84000"},
    "3": {"name": "Rare", "price": "119000"},
    "4": {"name": "Legendary", "price": "210000"},
    "5": {"name": "Exclusive", "price": "700000"},
    "6": {"name": "Cosmic", "price": "980000"},
    "7": {"name": "Limited Edition", "price": "1330000"},
    "8": {"name": "Ultimate", "price": "2520000"},
    "9": {"name": "Supreme", "price": "1260000000"},
    "10": {"name": "Uncommon", "price": "112000"},
    "11": {"name": "Epic", "price": "700000"},
    "12": {"name": "Mythic", "price": "1120000"},
    "13": {"name": "Divine", "price": "2100000"},
    "14": {"name": "Ethereal", "price": "3500000"},
    "15": {"name": "Premium", "price": "56000000"}
}


PRICE_MAPPING_FOR_SELL = {
    "1": {"name": "Common", "price": "2000"},
    "2": {"name": "Medium", "price": "3500"},
    "3": {"name": "Rare", "price": "4000"},
    "4": {"name": "Legendary", "price": "8000"},
    "5": {"name": "Exclusive", "price": "100000"},
    "6": {"name": "Cosmic", "price": "150000"},
    "7": {"name": "Limited Edition", "price": "350000"},
    "8": {"name": "Ultimate", "price": "750000"},
    "9": {"name": "Supreme", "price": "5000000"},
    "10": {"name": "Uncommon", "price": "10000"},
    "11": {"name": "Epic", "price": "25000"},
    "12": {"name": "Mythic", "price": "150000"},
    "13": {"name": "Divine", "price": "200000"},
    "14": {"name": "Ethereal", "price": "400000"},
    "15": {"name": "Premium", "price" : "5000000"}
}

def price(rarity):
    rarity_str = str(rarity)
    # First, try to fetch by key
    if rarity_str in PRICE_MAPPING_FOR_SELL:
        try:
            return int(PRICE_MAPPING_FOR_SELL[rarity_str]["price"])
        except ValueError:
            return None

    # If not found by key, search for a matching rarity name (case-insensitive)
    for data in PRICE_MAPPING_FOR_SELL.values():
        if data["name"].lower() == rarity_str.lower():
            try:
                return int(data["price"])
            except ValueError:
                return None
    return None


COUNTRY_MAPPING = {
    
    "1": {"name" : "India" , "sign" : "🇮🇳"},
    "2": {"name": "England", "sign": "🏴‍☠️"},
    "3": {"name": "Australia", "sign": "🇦🇺"},
    "4": {"name": "South Africa", "sign": "🇿🇦"},
    "5": {"name": "New Zealand", "sign": "🇳🇿"},
    "6": {"name": "Sri Lanka", "sign": "🇱🇰"},
    "7": {"name": "Afghanistan", "sign": "🇦🇫"},
    "8": {"name": "Ireland", "sign": "🇮🇪"},
    "9": {"name": "Zimbabwe", "sign": "🇿🇼"}
    
}

EVENT_MAPPING = {
    "𝘽𝙖𝙩𝙩𝙚𝙧": {"name": "𝘽𝙖𝙩𝙩𝙚𝙧", "sign": "🌟"},
    "𝘽𝙤𝙬𝙡𝙚𝙧𝙨": {"name": "𝘽𝙤𝙬𝙡𝙚𝙧𝙨", "sign": "👽"},
    "𝘼𝙡𝙡 𝙍𝙤𝙪𝙣𝙙𝙚𝙧": {"name": "𝘼𝙡𝙡 𝙍𝙤𝙪𝙣𝙙𝙚𝙧", "sign": "🥱"},
    "𝑨𝑽𝑬𝑹𝑨𝑮𝑬": {"name": "𝑨𝑽𝑬𝑹𝑨𝑮𝑬", "sign": "👌"},
    "𝑮𝑶𝑶𝑫": {"name": "𝑮𝑶𝑶𝑫", "sign": "🌟"},
    "𝙃𝙖𝙡𝙡 𝙤𝙛 𝙛𝙖𝙢𝙚": {"name": "𝙃𝙖𝙡𝙡 𝙤𝙛 𝙛𝙖𝙢𝙚", "sign": "🔥"},
    "𝑫𝒖𝒐": {"name": "𝑶𝑮", "sign": "⚡"},
    "𝑱𝑶𝑫": {"name": "𝑱𝑶𝑫", "sign": "🔱"},
    "𝑫𝒖𝒐": {"name": "𝑫𝒖𝒐", "sign": "👥"},
    "𝑮𝒐𝒂𝒕": {"name": "𝑮𝒐𝒂𝒕", "sign": "🗿"},
    "𝑻𝒆𝒂𝒎": {"name": "𝑻𝒆𝒂𝒎", "sign": "⚔️"},
    "𝘾𝙐𝙏𝙄𝙀": {"name": "𝘾𝙐𝙏𝙄𝙀", "sign": "💝"}
}


StartTime = time.time()
BOT_ID: int = 0
BOT_USERNAME: str = ""
MENTION_BOT: str = ""

async def get_readable_time(seconds: int) -> str:
    time_string = ""
    if seconds < 0:
        raise ValueError("Input value must be non-negative")

    if seconds < 60:
        time_string = f"{round(seconds)}s"
    else:
        minutes, seconds = divmod(seconds, 60)
        hours, minutes = divmod(minutes, 60)
        days, hours = divmod(hours, 24)
        if days > 0:
            time_string += f"{round(days)}days, "
        if hours > 0:
            time_string += f"{round(hours)}h:"
        time_string += f"{round(minutes)}m:{round(seconds):02d}s"

    return time_string


async def glog(text):
    
    await app.send_message(chat_id=GLOG , text = text , disable_web_page_preview=True)

async def llog(text):
    
    await app.send_message(chat_id=SUPPORT_CHAT_ID , text = text , disable_web_page_preview=True)