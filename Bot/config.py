import configparser
import os


# Find the settings.ini file
config_file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'settings.ini')
config = configparser.ConfigParser()
config.read(config_file)

# Telegram settings
api_id = int(config.get('telegram', 'api_id'))
api_hash = config.get('telegram', 'api_hash')
bot_token = config.get('telegram', 'bot_token')

# Shortener API
API_TOKEN = config.get('shortener', 'api_token')

# User IDs
OWNER_ID = int(config.get('users', 'owner_id'))
BOT_ID = int(config.get('users', 'bot_id'))
ADI = int(config.get('users', 'adi'))
AYUSH = int(config.get('users', 'ayush'))
SUNG = int(config.get('users', 'sung'))
ZERO = int(config.get('users', 'zero'))
OWNERS = [int(id.strip()) for id in config.get('users', 'owners').split(',')]

# Channel IDs
SUPPORT_CHAT_ID = int(config.get('channels', 'support_chat_id'))
LOG_CHANNEL = int(config.get('channels', 'log_channel'))
ERRORS = int(config.get('channels', 'errors'))
GLOG = int(config.get('channels', 'glog'))
SUPPORT_GROUP_URL = config.get('channels', 'support_group_url')


# General settings
DEFAULT_LANG = config.get('settings', 'default_lang')
REDEEM_AMOUNT = int(config.get('settings', 'redeem_amount'))
DEFAULT_DROP_COUNT = int(config.get('settings', 'default_drop_count'))
MINIMUM_MEMBERS = int(config.get('settings', 'minimum_members'))
CLAIM_STICKER_ID = str(config.get('settings', 'claim_sticker_id'))
BET_STICKER_ID = str(config.get('settings', 'bet_sticker_id'))

# Database settings
MONGO_URL = config.get('database', 'mongo_url')
DATABASE_NAME = config.get('database', 'database_name')

# Image settings
IMG_BB_URL = config.get('images', 'img_bb_url')
IMGBB_API_KEY = config.get('images', 'imgbb_api_key')
IMG_BB_KEYS = [key.strip() for key in config.get('images', 'img_bb_keys').split(',')]
START_IMAGE_URLS = [url.strip() for url in config.get('images', 'start_image_urls').split(',')]
HELP_IMAGE_URLS = [url.strip() for url in config.get('images', 'help_image_urls').split(',')]

# Links
REFER_LINK = config.get('links', 'refer_link')