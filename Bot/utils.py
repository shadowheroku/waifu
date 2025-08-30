from pyrogram import Client, filters
from pyrogram.types import Message
from Bot.database.privacydb import is_user_banned , is_user_sudo , is_user_og
from Bot.database import db 
from Bot.config import OWNERS
import time 
from Bot.config import SUPPORT_CHAT_ID
from functools import wraps
from Bot.database.grabtokendb import add_grab_token
from lexica import Client as LexicaClient
import aiohttp
import random
from pyrogram import Client, filters
from Bot.config import IMG_BB_KEYS , IMG_BB_URL
from functools import partial

ignore_duration = 10 * 60 

Command = partial(filters.command, prefixes=list("/#!.?"))

warned_users = {}

async def command_filter(_, __, message: Message):
    if message.from_user is None:
        return False
    return not await is_user_banned(message.from_user.id)

def warned_user_filter(func):
    @wraps(func)
    async def wrapper(client, message, *args, **kwargs):
        user_id = message.from_user.id
        current_time = time.time()
        
        if user_id in warned_users:
            warning_time = warned_users[user_id]
            if current_time - warning_time < ignore_duration:
                return None 
            else:
                del warned_users[user_id] 

        return await func(client, message, *args, **kwargs) 
    return wrapper

async def sudo_filter(_, __, message: Message):
    if message.from_user is None:
        return False
    if message.from_user.id in OWNERS or await is_user_sudo(message.from_user.id) or await is_user_og(message.from_user.id):
        return True
    return False


async def og_filter(_, __, message: Message):
    if message.from_user is None:
        return False
    if message.from_user.id in OWNERS or await is_user_og(message.from_user.id):
        return True
    return False

async def admin_filter(_, __, message: Message):
    if message.from_user is None:
        return False
    user_id = message.from_user.id
    if message.from_user.id in OWNERS or await is_user_sudo(user_id) or await is_user_og(user_id):
        return True
    return False

command_filter = filters.create(command_filter)
sudo_filter = filters.create(sudo_filter)
og_filter = filters.create(og_filter)
admin_filter = filters.create(admin_filter)


async def save_user_id(client: Client, message: Message):
    user_id = message.from_user.id
    first_name = message.from_user.first_name
    username = message.from_user.username
    
    if not await db.TotalUsers.find_one({"user_id": user_id}):
        await db.TotalUsers.insert_one({"user_id": user_id})

        log_message = (
            f"👤 **New User Started The Bot**\n\n"
            f"🆔 **User ID:** `{user_id}`\n"
            f"📛 **First Name:** `{first_name}`\n"
            f"🔗 **Username:** @{username if username else 'N/A'}"
        )
        await client.send_message(SUPPORT_CHAT_ID, log_message)

        if len(message.command) > 1:
            referral_code = message.command[1]
            if referral_code.startswith("ref_"):
                referrer_id = int(referral_code.split("_")[1])
                if referrer_id != user_id:
                    await add_grab_token(referrer_id, 10000)
                    await client.send_message(
                        chat_id=referrer_id,
                        text=f"🎉 Congrats! You've earned 10,000 Grab-Tokens for referring {first_name} to the bot!"
                    )


def save_user_id_decorator(handler):
    async def wrapper(client: Client, message: Message):
        await save_user_id(client, message)
        await handler(client, message)
    return wrapper


async def getFile(message: Message):

    if not message.reply_to_message:
        return None

    # Check if the reply contains a photo or a document of valid image types
    if message.reply_to_message.photo:
        image = await message.reply_to_message.download()
        return image
    elif message.reply_to_message.document and message.reply_to_message.document.mime_type in ['image/png', 'image/jpg', 'image/jpeg']:
        image = await message.reply_to_message.download()
        return image
    else:
        return None

async def UpscaleImages(image: bytes) -> str:
    try:
        # Initialize the Lexica client and upscale the image
        client = LexicaClient()
        content = client.upscale(image)
        
        # Save the upscaled image to a file
        upscaled_file_path = "upscaled.png"
        with open(upscaled_file_path, "wb") as output_file:
            output_file.write(content)
        
        return upscaled_file_path
    except Exception as e:
        raise Exception(f"Failed to upscale the image: {e}")
    
async def upload_image_to_imgbb(session: aiohttp.ClientSession, file_id: str, client: Client) -> str:
    try:
        api_key = random.choice(IMG_BB_KEYS)
        photo_path = await client.download_media(file_id)

        form = aiohttp.FormData()
        form.add_field('key', api_key)
        form.add_field('image', open(photo_path, 'rb'))

        async with session.post(IMG_BB_URL, data=form) as response:
            result = await response.json()
            if result['success']:
                return result['data']['url']
            else:
                raise Exception("ImgBB upload failed.")

    except Exception as e:
        raise Exception(f"Image upload error: {str(e)}")