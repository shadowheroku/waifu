import configparser
import os


# Find the settings.ini file
config_file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'settings.ini')
config = configparser.ConfigParser()
config.read(config_file)

# Telegram settings
api_id = 23212132
api_hash = "1c17efa86bdef8f806ed70e81b473c20"
bot_token = "8013665655:AAFbn4ZUUXAUqXV1HBvGdrcDFiYaDY9Y4do"

# Shortener API
API_TOKEN = config.get('shortener', 'api_token')

# User IDs
OWNER_ID = 8429156335
BOT_ID = 8013665655
ADI = int(config.get('users', 'adi'))
AYUSH = int(config.get('users', 'ayush'))
SUNG = int(config.get('users', 'sung'))
ZERO = int(config.get('users', 'zero'))
OWNERS = [int(id.strip()) for id in config.get('users', 'owners').split(',')]

# Channel IDs
SUPPORT_CHAT_ID = -1002800777153
LOG_CHANNEL = -1002800777153
ERRORS = -1002800777153
GLOG = -1002800777153
SUPPORT_GROUP_URL = "https://t.me/MonicLogs"


# General settings
# General settings
DEFAULT_LANG = config.get('settings', 'default_lang', fallback='en')  # default language: English
REDEEM_AMOUNT = int(config.get('settings', 'redeem_amount', fallback='100'))  # default redeem amount: 100 coins
DEFAULT_DROP_COUNT = int(config.get('settings', 'default_drop_count', fallback='5'))  # default drop count: 5
MINIMUM_MEMBERS = int(config.get('settings', 'minimum_members', fallback='10'))  # minimum group members: 10
CLAIM_STICKER_ID = config.get('settings', 'claim_sticker_id', fallback='CAACAgQAAyEFAASm8HfBAAI7tGiyw8SNwJ0sVaUhW69sMXuALMIIAAIwEQACFvpYUPu-gNcdMet4HgQ')  # sample sticker ID
BET_STICKER_ID = config.get('settings', 'bet_sticker_id', fallback='CAACAgQAAyEFAASm8HfBAAI7tGiyw8SNwJ0sVaUhW69sMXuALMIIAAIwEQACFvpYUPu-gNcdMet4HgQ')  # sample sticker ID


# Database settings
MONGO_URL = "mongodb+srv://ryumasgod:ryumasgod@cluster0.ojfkovp.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
DATABASE_NAME = "Shadow"

# Image settings
IMG_BB_URL = config.get('images', 'img_bb_url')
IMGBB_API_KEY = config.get('images', 'imgbb_api_key')
IMG_BB_KEYS = [key.strip() for key in config.get('images', 'img_bb_keys').split(',')]
START_IMAGE_URLS = [url.strip() for url in config.get('images', 'start_image_urls').split(',')]
HELP_IMAGE_URLS = [url.strip() for url in config.get('images', 'help_image_urls').split(',')]

# Links
REFER_LINK = config.get('links', 'refer_link')
