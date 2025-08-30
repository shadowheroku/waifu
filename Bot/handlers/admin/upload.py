from pyrogram import filters, Client
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, Message
import re
from pyrogram.enums import ListenerTypes , ParseMode
from Bot import app , EVENT_MAPPING , RARITY_MAPPING
from Bot.database.iddb import get_next_id
from Bot.database.animedb import get_anime_details_by_anime_id
from Bot.errors import capture_and_handle_error
import requests
from Bot.config import SUPPORT_CHAT_ID , LOG_CHANNEL
from pyrogram.enums import ParseMode
from pyrogram import types
from Bot.utils import sudo_filter
from Bot.database.characterdb import get_character_details
from Bot.database.uploaddb import *
from texts import WAIFU , ANIME

CATBOX_API_URL = "https://catbox.moe/user/api.php"

upload_details = {}


@app.on_message(filters.regex("⚙ Admin Panel ⚙") & sudo_filter & filters.private)
async def handle_admin_panel(client , message: types.Message):
    # Fetch total counts
    total_waifus = await get_total_waifus()
    total_animes = await get_total_animes()
    total_harems = await get_total_harems()
    
    # Create the confirmation text
    confirmation_text = (
        f"Admin Panel:\n\n"
        f"Total {WAIFU}: {total_waifus}\n"
        f"Total {ANIME}: {total_animes}\n"
        f"Total Harems: {total_harems}\n"
    )

    # Create the inline keyboard with specific row structures
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text=f"🆕 Aᴅᴅ {WAIFU}", callback_data="add_waifu"),
            InlineKeyboardButton(text=f"Aᴅᴅ {ANIME} 🆕", callback_data="add_anime")
        ],
        [
            InlineKeyboardButton(text=f"✏️ Eᴅɪᴛ {WAIFU}", callback_data="edit_character"),
            InlineKeyboardButton(text=f"🗑 Dᴇʟᴇᴛᴇ {WAIFU}", callback_data="delete_character")
        ],
        [
            InlineKeyboardButton(text=f"✏️ Rᴇɴᴀᴍᴇ {ANIME}", callback_data="rename_anime"),
            InlineKeyboardButton(text=f"🔍 Sᴇᴀʀᴄʜ {ANIME}", switch_inline_query_current_chat="search.anime ")
        ],
        [InlineKeyboardButton(text=f"📤 Uᴘʟᴏᴀᴅ {WAIFU} Tᴏ Sᴛᴏʀᴇ", callback_data="upload_waifu_to_store")],
        [InlineKeyboardButton(text=f"🎥 Uᴘʟᴏᴀᴅ Vɪᴅᴇᴏ {WAIFU}", callback_data="upload_video_waifu")],
        [InlineKeyboardButton(text=f"🏏 Aᴅᴅ IPL {WAIFU}", callback_data="add_ipl_player")],
        [InlineKeyboardButton(text=f"📋 Vɪᴇᴡ IPL {WAIFU}s", callback_data="view_ipl_players")],
        [InlineKeyboardButton(text="❌ Cʟᴏsᴇ", callback_data="xxx")]
    ])

    await message.reply_text(confirmation_text, reply_markup=keyboard)

@app.on_callback_query(filters.regex("add_waifu"))
@capture_and_handle_error
async def start_character_upload(client: Client, callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    await callback_query.message.delete()

    btn = InlineKeyboardMarkup([
        [InlineKeyboardButton("Cancel Upload", callback_data="close_upload")]
    ])

    try:
        img_message: Message = await client.ask(
            user_id,
            text=f"Please send the image of the {WAIFU} you want to upload!",
            filters=filters.photo,
            timeout=60,
            reply_markup=btn
        )
        file_path = await img_message.download()

        # Upload the file to Catbox
        with open(file_path, "rb") as image_file:
            response = requests.post(
                CATBOX_API_URL,
                data={"reqtype": "fileupload"},
                files={"fileToUpload": image_file},
            )

        if response.status_code == 200 and response.text.startswith("https"):
            img_url = response.text.strip()

        upload_details[user_id] = {"img_url": img_url.strip()}

        btn = InlineKeyboardMarkup([
            [InlineKeyboardButton("Cancel Upload", callback_data="close_upload")]
        ])
        name_message: Message = await client.ask(
            user_id,
            text=f"Image uploaded: {img_url}\n\nNow please send the {WAIFU} name.",
            timeout=60,
            reply_markup=btn
        )
        upload_details[user_id]["name"] = name_message.text.strip()

        btn = InlineKeyboardMarkup([
            [
                InlineKeyboardButton(f"Search {ANIME}", switch_inline_query_current_chat=".anime "),
                InlineKeyboardButton("Cancel", callback_data="close_upload")
            ]
        ])
        team_message: Message = await client.ask(
            user_id,
            text=f"Please send the {ANIME} ID. Use the button below to search for the {ANIME}.",
            timeout=60,
            reply_markup=btn
        )
        team_id_text = team_message.text.strip()
        if "🆔 ID:" in team_id_text:
            match = re.search(r'🆔\s*ID:\s*(\d+)', team_id_text)
            if match:
                team_id = int(match.group(1))
                upload_details[user_id]["anime_id"] = team_id
                try : 
                    a = await get_anime_details_by_anime_id(team_id)
                    upload_details[user_id]["anime"] = a["name"]
                except Exception as e :
                    print(e)
            else :
                await team_message.reply_text(f"Failed To Get The {ANIME} Info , Please Create That {ANIME} And Try Again !!")
                return

        rarity_buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton(f"{v['sign']} {v['name']}", callback_data=f"glob_{k}")] 
        for k, v in RARITY_MAPPING.items()
        ])
        rarity_choice : CallbackQuery = await client.ask(
            user_id,
            text="Now choose the rarity:",
            timeout=60,
            filters=filters.regex("glob_.*"),
            reply_markup=rarity_buttons,
            listener_type=ListenerTypes.CALLBACK_QUERY
        )
        rarity_key = rarity_choice.data.split("_")[1]
        rarity = RARITY_MAPPING[rarity_key]
        upload_details[user_id].update({"rarity": rarity["name"], "rarity_sign": rarity["sign"]})
        await rarity_choice.message.delete()

        event_buttons = InlineKeyboardMarkup([
            [InlineKeyboardButton(f"{v['sign']} {v['name']}", callback_data=f"globevent_{k}")]
            for k, v in EVENT_MAPPING.items()
        ] + [[InlineKeyboardButton("Skip Event", callback_data="globevent_skip")]])

        event_choice : CallbackQuery = await client.ask(
            user_id,
            text="Choose an event (or skip):",
            timeout=60,
            filters=filters.regex("globevent_.*"),
            reply_markup=event_buttons,
            listener_type=ListenerTypes.CALLBACK_QUERY
        )
        if event_choice.data != "globevent_skip":
            event_key = event_choice.data.split("_")[1]
            event = EVENT_MAPPING[event_key]
            upload_details[user_id].update({"event": event["name"], "event_sign": event["sign"]})
        await event_choice.message.delete()

        data = upload_details[user_id]

        confirmation_text = (
            f"Please confirm the following details:\n\n"
            f"📸 Image URL: {data['img_url']}\n"
            f"📝 Name: {data['name']}\n"
            f"📺 {ANIME}: {data.get('anime', 'N/A')}\n"
            f"🆔 {ANIME} ID: {data['anime_id']}\n"
            f"🌟 Rarity: {data['rarity']} {data['rarity_sign']}\n"
        )

        confirm_buttons = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("Confirm Upload", callback_data="glob_confirm"),
                InlineKeyboardButton("Cancel", callback_data="close_upload")
            ]
        ])
        await client.send_photo(
            user_id,
            photo=data['img_url'],
            caption=confirmation_text,
            reply_markup=confirm_buttons
        )

    except Exception as e:
        await callback_query.message.reply(f"Error: {str(e)}")

@app.on_callback_query(filters.regex("glob_confirm"))
@capture_and_handle_error
async def confirm_upload_handler(client: Client, callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    data = upload_details.get(user_id)
    if not data:
        await callback_query.message.reply("No upload data found for Global Upload")
        return

    character_id = await get_next_id()
    character_doc = {
        "id": str(character_id),
        "img_url": data['img_url'],
        "name": data['name'],
        "anime": data.get('anime', "Unknown"),
        "anime_id": data['anime_id'],
        "rarity": data['rarity'],
        "rarity_sign": data['rarity_sign']
    }

    if data.get("event"):
        character_doc["event"] = data["event"]
        character_doc["event_sign"] = data["event_sign"]

    await upload_waifu(character_doc)
    await callback_query.message.edit_caption(f"{WAIFU} successfully uploaded." , reply_markup=None)
    del upload_details[user_id]
    text = f"<b>✨ New {WAIFU} Uploaded by {callback_query.from_user.mention}!!</b>\n\n"
    text += f"🎀 <b>Name :</b> {data['name']}\n"
    text += f"⛩️ <b>{ANIME} :</b> {data['anime']}\n"
    text += f"{data['rarity_sign']} <b>Rarity</b> : {data['rarity']}\n\n"
    
    await app.send_photo(chat_id=SUPPORT_CHAT_ID , photo = data['img_url'] , caption=text , parse_mode=ParseMode.HTML)
    await app.send_photo(chat_id=LOG_CHANNEL , photo = data['img_url'] , caption=text , parse_mode=ParseMode.HTML)


@app.on_callback_query(filters.regex("close_upload"))
@capture_and_handle_error
async def lol(client: Client, callback: CallbackQuery):
    user_id = callback.from_user.id
    
    # Remove the user's upload details from the cache
    if user_id in upload_details:
        upload_details.pop(user_id, None)
    
    # Delete the message
    await callback.message.delete()
    
    # Optionally, send a confirmation message
    await client.send_message(
        chat_id=user_id,
        text="Upload process has been canceled successfully."
    )
    
@app.on_callback_query(filters.regex("xxx"))
async def x(c , q : CallbackQuery):
    await q.message.delete()
    
    
@app.on_message(filters.command("forcedelete") & sudo_filter & filters.private)
async def l(c : Client , m : Message):
    
    try:
        command_args = m.text.split(maxsplit=1)
        character_id = command_args[1].strip()
    except IndexError:
        await m.reply_text(f"❗ Pʟᴇᴀsᴇ ᴘʀᴏᴠɪᴅᴇ ᴀ {WAIFU} ID.")
        return
    
    character = await get_character_details(character_id)
    if not character:
        await m.reply_text(f"❗ {WAIFU} ɴᴏᴛ ғᴏᴜɴᴅ. Pʟᴇᴀsᴇ ᴘʀᴏᴠɪᴅᴇ ᴀ ᴠᴀʟɪᴅ {WAIFU} ID.")
        return
    
    # Extract character details
    name = character.get("name", "Unknown")
    anime = character.get("anime", "Unknown")
    rarity_sign = character.get("rarity_sign", "Unknown")
    rarity = character.get("rarity", "Unknown")

    # Prepare the message caption
    caption = (
        f"Name: {name}\n"
        f"{ANIME}: {anime}\n"
        f"{rarity_sign} Rarity: {rarity}\n"
        f"ID: {character_id}\n\n"
        f"Aʀᴇ ʏᴏᴜ sᴜʀᴇ ʏᴏᴜ ᴡᴀɴᴛ ᴛᴏ ғᴏʀᴄᴇ ᴅᴇʟᴇᴛᴇ ᴛʜɪs {WAIFU}?"
    )

    # Send message with inline buttons for confirmation or cancellation
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Cᴏɴғɪʀᴍ", callback_data=f"q_forcedelete_{character_id}")],
        [InlineKeyboardButton(text="❌ Cᴀɴᴄᴇʟ", callback_data="xxx")]
    ])
    await m.reply_text(caption, reply_markup=keyboard)
    
@app.on_callback_query(filters.regex("q_forcedelete_"))
async def x(c : Client , q : CallbackQuery):
    
    character_id = q.data.split("_")[-1]
    
    await force_delete(character_id)

    await q.message.edit_text(f"✅ {WAIFU} ᴡɪᴛʜ ɪᴅ {character_id} ʜᴀs ʙᴇᴇɴ ғᴏʀᴄᴇᴅᴇʟᴇᴛᴇᴅ sᴜᴄᴄᴇssғᴜʟʟʏ.")
    
@app.on_callback_query(filters.regex("delete_character"))
async def h(c : Client , q : CallbackQuery):
    
    await q.message.delete()
    
    l = InlineKeyboardMarkup([[InlineKeyboardButton("Search"  , switch_inline_query_current_chat="")]])
    m : Message = await c.ask(q.from_user.id , f"🔍 Pʟᴇᴀsᴇ sᴇɴᴅ ᴛʜᴇ {WAIFU} ID ʏᴏᴜ ᴡᴀɴᴛ ᴛᴏ ᴅᴇʟᴇᴛᴇ:" , reply_markup= l , filters= filters.text)
    
    try:
        character_id = str(m.text.strip())
    except ValueError:
        await m.reply_text(f"❗ Iɴᴠᴀʟɪᴅ {WAIFU} ID. Pʟᴇᴀsᴇ ᴘʀᴏᴠɪᴅᴇ ᴀ ᴠᴀʟɪᴅ ɪɴᴛᴇɢᴇʀ ID.")
        return

    character = await get_character_details(character_id)
    if not character:
        await m.reply_text(f"❗ {WAIFU} ɴᴏᴛ ғᴏᴜɴᴅ. Pʟᴇᴀsᴇ ᴘʀᴏᴠɪᴅᴇ ᴀ ᴠᴀʟɪᴅ {WAIFU} ID.")
        return
    
    # Extract character details
    name = character.get("name", "Unknown")
    anime = character.get("anime", "Unknown")
    rarity_sign = character.get("rarity_sign", "Unknown")
    rarity = character.get("rarity", "Unknown")
    img_url = character.get("img_url", None)
    
    # Prepare the message caption
    caption = (
        f"Name: {name}\n"
        f"{ANIME}: {anime}\n"
        f"{rarity_sign} Rarity: {rarity}\n"
        f"ID: {character_id}\n\n"
        f"Aʀᴇ ʏᴏᴜ sᴜʀᴇ ʏᴏᴜ ᴡᴀɴᴛ ᴛᴏ ᴅᴇʟᴇᴛᴇ ᴛʜɪs {WAIFU} ᴘᴇʀᴍᴀɴᴇɴᴛʟʏ?"
    )

    # Send the image with the caption and inline buttons
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Cᴏɴғɪʀᴍ", callback_data=f"m_deletion_{character_id}")],
        [InlineKeyboardButton(text="❌ Cᴀɴᴄᴇʟ", callback_data="xxx")]
    ])

    if img_url:
        await m.reply_photo(photo=img_url, caption=caption, reply_markup=keyboard)
    else:
        await m.reply_text(caption, reply_markup=keyboard)
        
@app.on_callback_query(filters.regex("m_deletion_"))
async def x(c : Client , q : CallbackQuery):
    
    character_id = q.data.split("_")[-1]
    
    await force_delete(character_id)

    await q.message.edit_text(f"✅ {WAIFU} ᴡɪᴛʜ ɪᴅ {character_id} ʜᴀs ʙᴇᴇɴ ғᴏʀᴄᴇᴅᴇʟᴇᴛᴇᴅ sᴜᴄᴄᴇssғᴜʟʟʏ.")
    
@app.on_callback_query(filters.regex("add_anime"))
async def a(c : Client , q : CallbackQuery):
    
    btn = InlineKeyboardMarkup([[InlineKeyboardButton("Team" , switch_inline_query_current_chat=".anime ")]])
    
    text = f"Sᴇᴀʀᴄʜ ғᴏʀ / Cʀᴇᴀᴛᴇ {ANIME} Usɪɴɢ ᴛʜᴇ ʙᴜᴛᴛᴏɴ ɢɪᴠᴇɴ ʙᴇʟᴏᴡ ʙʏ ᴊᴜsᴛ ᴛʏᴘɪɴɢ ᴛʜᴇ {ANIME}'s ɴᴀᴍᴇ."
    
    await q.message.edit_text(text , reply_markup=btn)

@app.on_callback_query(filters.regex("renamee_anime"))
async def c(c : Client , q : CallbackQuery):
    
    await q.message.edit_text(f"Usᴇ ᴊᴜsᴛ /{ANIME} ᴄᴏᴍᴍᴀɴᴅ ᴛᴏ ʀᴇɴᴀᴍᴇ {ANIME}." , reply_markup=None)


@app.on_callback_query(filters.regex("edit_character"))
async def handle_character_selection(c : Client , q: types.CallbackQuery):
    
    await q.message.delete()

    btn = InlineKeyboardMarkup([[InlineKeyboardButton(f"Sᴇᴀʀᴄʜ {WAIFU}" , switch_inline_query_current_chat="")]])
    message : Message = await c.ask(q.from_user.id , text= f"🔍 Cʜᴏᴏsᴇ ᴛʜᴇ {WAIFU} ᴛᴏ ᴇᴅɪᴛ:" , reply_markup=btn , timeout=60 , filters=filters.via_bot)
    
    
    if not message.caption:
        await message.reply_text(f"❗ Nᴏ ᴄᴀᴘᴛɪᴏɴ ғᴏᴜɴᴅ.\nUse /clear to clear your state !!")
        return

    # Extract the character ID from the caption
    match = re.search(r"🆔: (\d+)", message.caption)
    if not match:
        await message.reply_text(f"❗ Fᴀɪʟᴇᴅ ᴛᴏ ғɪɴᴅ {WAIFU} ID ɪɴ ᴛʜᴇ ᴄᴀᴘᴛɪᴏɴ.")
        return
    
    character_id = match.group(1)
    character = await get_character_details(character_id)
    if not character:
        await message.reply_text(f"❗ {WAIFU} ɴᴏᴛ ғᴏᴜɴᴅ.")
        return

    # Display character details
    name = character.get("name", "Unknown")
    anime = character.get("anime", "Unknown")
    rarity_sign = character.get("rarity_sign", "Unknown")
    rarity = character.get("rarity", "Unknown")
    img_url = character.get("img_url", None)
    
    x = (
        f"**Name**: {name}\n"
        f"**Team**: {anime}\n"
        f"{rarity_sign} **Rarity**: {rarity}\n"
        f"**ID**: {character_id}"
    )
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎭 Edit Name", callback_data=f"edit_name_{character_id}")],
        [InlineKeyboardButton(text="🌆 Edit Image", callback_data=f"edit_image_{character_id}")],
        [InlineKeyboardButton(text="♨️ Edit Team", callback_data=f"edit_anime_{character_id}")],
        [InlineKeyboardButton(text="🧿 Edit Rarity", callback_data=f"edit_rarity_{character_id}")],
        [InlineKeyboardButton(text="🌐 Edit Event", callback_data=f"edit_event_{character_id}")],
        [InlineKeyboardButton(text=f"⛩️ Reset {WAIFU}", callback_data=f"reset_character_{character_id}")],
        [InlineKeyboardButton(text="🛑 Cancel", callback_data = "xxx")]
    ])

    if img_url:
        await message.reply_photo(photo=img_url, caption=x, reply_markup=keyboard)
    else:
        await message.reply_text(x, reply_markup=keyboard)

@app.on_callback_query(filters.regex("edit_name_"))
async def edit(c : Client , q : types.CallbackQuery):

    await q.message.delete()

    character_id = q.data.split("_")[-1]

    character = await get_character_details(character_id)
    old_name = character.get("name", "Unknown")

    m : Message = await c.ask(q.from_user.id , text = "📝 Pʟᴇᴀsᴇ sᴇɴᴅ ᴛʜᴇ ɴᴇᴡ ɴᴀᴍᴇ." , filters= filters.text , timeout=60)    
    
    new_name = m.text
    
    await update_name(character_id, new_name)

    await m.reply_text(f"✅ Nᴀᴍᴇ ᴜᴘᴅᴀᴛᴇᴅ ᴛᴏ {new_name}.")
    
    # Log the change to SUPPORT_CHAT_ID
    await c.send_message(
        chat_id=SUPPORT_CHAT_ID,
        text=f"🔄 **{WAIFU} Name Edited**\n\n"
             f"👤 **Edited By:** [{m.from_user.full_name}](tg://user?id={m.from_user.id})\n"
             f"📎 **{WAIFU} ID:** {character_id}\n"
             f"📝 **Old Name:** {old_name}\n"
             f"✏ **New Name:** {new_name}",
             parse_mode=ParseMode.MARKDOWN
    )

    # Log the change to SUPPORT_CHAT_ID
    await c.send_message(
        chat_id=LOG_CHANNEL,
        text=f"🔄 **{WAIFU} Name Edited**\n\n"
             f"👤 **Edited By:** [{m.from_user.full_name}](tg://user?id={m.from_user.id})\n"
             f"📎 **{WAIFU} ID:** {character_id}\n"
             f"📝 **Old Name:** {old_name}\n"
             f"✏ **New Name:** {new_name}",
             parse_mode=ParseMode.MARKDOWN
    )
    
@app.on_callback_query(filters.regex("edit_anime_"))
async def el(c : Client , q : CallbackQuery):
    
    character_id = q.data.split("_")[-1]

    await q.message.delete()

    btn = InlineKeyboardMarkup([[InlineKeyboardButton(f"Sᴇᴀʀᴄʜ {ANIME}" , switch_inline_query_current_chat=".anime ")]])
    m : Message = await c.ask(q.from_user.id , f"🔍 Sᴇᴀʀᴄʜ ғᴏʀ {ANIME}:" , filters=filters.via_bot , timeout=60 , reply_markup = btn)
    
    text = m.text

    if not text:
        await m.reply_text(f"❗ Nᴏ ᴛᴇxᴛ ғᴏᴜɴᴅ ɪɴ ᴛʜᴇ ᴍᴇssᴀɢᴇ.")
        return

    # Extract the anime ID from the message text
    match = re.search(r"🆔 ID: (\d+)", text)
    if match:
        anime_id = int(match.group(1))  # Convert anime_id to integer
    else:
        await m.reply_text(f"❗ Fᴀɪʟᴇᴅ ᴛᴏ ғɪɴᴅ {ANIME} ID ɪɴ ᴛʜᴇ ᴛᴇxᴛ.")
        return

    # Find the anime in the database
    anime = await find_anime(anime_id)

    if anime:

        # Find the current anime associated with the character
        character = await find_waifu(character_id)
        old_anime_name = character.get("anime", "Unknown Anime")
        old_anime_id = character.get("anime_id", "Unknown ID")

        # Update the character with the new anime information
        await update_anime(character_id , anime_id , anime.get("name"))

        # Send confirmation message
        await m.reply_text(f"✅ {ANIME} ᴜᴘᴅᴀᴛᴇᴅ ᴛᴏ {anime.get('name')}.")
        
        # Log the change to SUPPORT_CHAT_ID
        await c.send_message(
            chat_id=SUPPORT_CHAT_ID,
            text=f"🔄 **{WAIFU} Anime Edited**\n\n"
                 f"👤 **Edited By:** [{m.from_user.full_name}](tg://user?id={m.from_user.id})\n"
                 f"📎 **{WAIFU} ID:** {character_id}\n"
                 f"🎞 **Old {ANIME}:** {old_anime_name} (ID: {old_anime_id})\n"
                 f"🎞 **New {ANIME}:** {anime.get('name')} (ID: {anime_id})",
                 parse_mode = ParseMode.MARKDOWN
        )

        await c.send_message(
            chat_id=LOG_CHANNEL,
            text=f"🔄 **{WAIFU} Anime Edited**\n\n"
                 f"👤 **Edited By:** [{m.from_user.full_name}](tg://user?id={m.from_user.id})\n"
                 f"📎 **{WAIFU} ID:** {character_id}\n"
                 f"🎞 **Old {ANIME}:** {old_anime_name} (ID: {old_anime_id})\n"
                 f"🎞 **New {ANIME}:** {anime.get('name')} (ID: {anime_id})",
                 parse_mode = ParseMode.MARKDOWN
        )

    else:
        # Send an error message if anime not found
        await m.reply_text(f"❗ {ANIME} ɴᴏᴛ ғᴏᴜɴᴅ.")


@app.on_callback_query(filters.regex("edit_rarity_"))
async def n(c : Client , q : CallbackQuery):
    
    character_id = q.data.split("_")[-1]
    
    await q.message.delete()
    
    rarity_buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton(f"{v['sign']} {v['name']}", callback_data=f"lol_{k}")] 
        for k, v in RARITY_MAPPING.items()
        ])
    
    rarity_choice : CallbackQuery = await c.ask(
            q.from_user.id,
            text="🎚 Pʟᴇᴀsᴇ ᴄʜᴏᴏsᴇ ɴᴇᴡ ʀᴀʀɪᴛʏ.",
            timeout=60,
            filters=filters.regex("lol_.*"),
            reply_markup=rarity_buttons,
            listener_type=ListenerTypes.CALLBACK_QUERY
        )
    rarity_key = rarity_choice.data.split("_")[1]
    rarity_info = RARITY_MAPPING[rarity_key]

    if rarity_info:
        # Find the current rarity associated with the character
        character = await find_waifu(character_id)
        old_rarity = character.get("rarity", "Unknown Rarity")
        old_rarity_sign = character.get("rarity_sign", "Unknown Sign")

        await update_rarity(character_id, rarity_info["name"] ,  rarity_info["sign"])
        
        await rarity_choice.message.reply_text(f"✅ Rᴀʀɪᴛʏ ᴜᴘᴅᴀᴛᴇᴅ ᴛᴏ {rarity_info['sign']} {rarity_info['name']}.")
        await rarity_choice.message.delete()
        # Log the change to SUPPORT_CHAT_ID
        await c.send_message(
            chat_id=SUPPORT_CHAT_ID,
            text=f"🔄 **{WAIFU} Rarity Edited**\n\n"
                 f"👤 **Edited By:** [{q.from_user.full_name}](tg://user?id={q.from_user.id})\n"
                 f"📎 **{WAIFU} ID:** {character_id}\n"
                 f"{old_rarity_sign} **Old Rarity:**  {old_rarity}\n"
                 f"{rarity_info['sign']} **New Rarity:**  {rarity_info['name']}",
                 parse_mode= ParseMode.MARKDOWN
        )

        await c.send_message(
            chat_id=LOG_CHANNEL,
            text=f"🔄 **{WAIFU} Rarity Edited**\n\n"
                 f"👤 **Edited By:** [{q.from_user.full_name}](tg://user?id={q.from_user.id})\n"
                 f"📎 **{WAIFU} ID:** {character_id}\n"
                 f"{old_rarity_sign} **Old Rarity:**  {old_rarity}\n"
                 f"{rarity_info['sign']} **New Rarity:**  {rarity_info['name']}",
                 parse_mode= ParseMode.MARKDOWN
        )
        
    else:
        await rarity_choice.message.reply_text("❗ Iɴᴠᴀʟɪᴅ ʀᴀʀɪᴛʏ sᴇʟᴇᴄᴛᴇᴅ.")


@app.on_callback_query(filters.regex("edit_event_"))
async def edit_event_handler(c: Client, q: CallbackQuery):
    character_id = q.data.split("_")[-1]
    await q.message.delete()

    # Prepare event selection buttons
    event_buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton(f"{v['sign']} {v['name']}", callback_data=f"evt_{k}_{character_id}")]
        for k, v in EVENT_MAPPING.items()
    ] + [
        [InlineKeyboardButton("Skip Event", callback_data=f"evt_remove_{character_id}")]
    ])

    try:
        # Wait for user's choice (event selection or skip)
        event_choice: CallbackQuery = await c.ask(
            q.from_user.id,
            text="Choose an event (or skip):",
            timeout=60,
            filters=filters.regex(r"^evt_(.*)"),  # Listen for evt_ prefixed callbacks
            reply_markup=event_buttons,
            listener_type=ListenerTypes.CALLBACK_QUERY
        )
    except TimeoutError:
        await c.send_message(q.from_user.id, "❌ Selection timed out. Please try again.")
        return

    # Process the user's choice
    action, *data = event_choice.data.split("_")
    character_id = data[-1]  # Last part is always character ID

    if "remove" in data:
        # Handle event removal
        character = await find_waifu(character_id)
        if not character:
            await event_choice.message.reply_text(f"❗ {WAIFU} ɴᴏᴛ ғᴏᴜɴᴅ.")
            return

        old_event = character.get("event", "No Event")
        old_event_sign = character.get("event_sign", "No Sign")

        await remove_event(character_id)

        await event_choice.message.reply_text(f"🚫 ᴇᴠᴇɴᴛ ʀᴇᴍᴏᴠᴇᴅ ғʀᴏᴍ ᴛʜᴇ {WAIFU}.")

        # Logging
        log_text = (
            f"🔄 **{WAIFU} Event Removed**\n\n"
            f"👤 **Edited By:** [{q.from_user.full_name}](tg://user?id={q.from_user.id})\n"
            f"📎 **{WAIFU} ID:** {character_id}\n"
            f"{old_event_sign} **Old Event:** {old_event}\n"
            f"🚫 **New Event:** None"
        )
        await c.send_message(SUPPORT_CHAT_ID, log_text, parse_mode=ParseMode.MARKDOWN)
        await c.send_message(LOG_CHANNEL, log_text, parse_mode=ParseMode.MARKDOWN)

    else:
        # Handle event selection
        try:
            event_key = data[0]
            event_info = EVENT_MAPPING[event_key]
        except (IndexError, KeyError):
            await event_choice.message.reply_text("❗ Invalid event selected.")
            return

        # Update character's event
        character = await find_waifu(character_id)
        if not character:
            await event_choice.message.reply_text(f"❗ {WAIFU} ɴᴏᴛ ғᴏᴜɴᴅ.")
            return

        old_event = character.get("event", "No Event")
        old_event_sign = character.get("event_sign", "No Sign")

        await update_event(character_id , event_info["name"] , event_info["sign"])

        await event_choice.message.reply_text(
            f"✅ ᴇᴠᴇɴᴛ ᴜᴘᴅᴀᴛᴇᴅ ᴛᴏ {event_info['sign']} {event_info['name']}."
        )
        await event_choice.message.delete()
        # Logging
        log_text = (
            f"🔄 **{WAIFU} Event Edited**\n\n"
            f"👤 **Edited By:** [{q.from_user.full_name}](tg://user?id={q.from_user.id})\n"
            f"📎 **{WAIFU} ID:** {character_id}\n"
            f"{old_event_sign} **Old Event:** {old_event}\n"
            f"{event_info['sign']} **New Event:** {event_info['name']}"
        )
        await c.send_message(SUPPORT_CHAT_ID, log_text, parse_mode=ParseMode.MARKDOWN)
        await c.send_message(LOG_CHANNEL, log_text, parse_mode=ParseMode.MARKDOWN)

@app.on_callback_query(filters.regex("edit_image_"))
async def fuyye(c : Client , q : CallbackQuery):

    try :

        character_id = q.data.split("_")[-1]
        await q.message.delete()
    
        m : Message = await c.ask(q.from_user.id , "🖼 Pʟᴇᴀsᴇ ᴜᴘʟᴏᴀᴅ ᴛʜᴇ ɴᴇᴡ ɪᴍᴀɢᴇ." , filters = filters.photo , timeout=60)
    
        file_path = await m.download()
        
        img_url= None
    
        # Upload the file to Catbox
        with open(file_path, "rb") as image_file:
            response = requests.post(
                CATBOX_API_URL,
                data={"reqtype": "fileupload"},
                files={"fileToUpload": image_file},
            )
    
        # Check if the upload was successful
        if response.status_code == 200 and response.text.startswith("https"):
                img_url = response.text.strip()   
    
        import os
        
        os.remove(file_path)
    
        await update_image(character_id , img_url)
        await m.reply_text(f"✅ Iᴍᴀɢᴇ sᴜᴄᴄᴇssғᴜʟʟʏ ᴜᴘᴅᴀᴛᴇᴅ. Nᴇᴡ ɪᴍᴀɢᴇ URL: {img_url}")
    except:
        return


@app.on_callback_query(filters.regex("reset_character_"))
async def knur(c : Client , q : CallbackQuery):
    
    character_id = q.data.split("_")[-1]
    await q.message.delete()
    

    await reset_waifu(character_id)
    await q.message.reply_text(f"✅ {WAIFU} {character_id} ʜᴀs ʙᴇᴇɴ ʀᴇsᴇᴛ ᴀnᴅ ʀᴇᴍᴏᴠᴇᴅ ғʀᴏᴍ ᴀʟʟ ᴄᴏʟʟᴇᴄᴛɪᴏɴs.")

@app.on_callback_query(filters.regex("add_ipl_player"))
@capture_and_handle_error
async def start_ipl_character_upload(client: Client, callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    await callback_query.message.delete()

    btn = InlineKeyboardMarkup([
        [InlineKeyboardButton("Cancel Upload", callback_data="close_upload")]
    ])

    try:
        img_message: Message = await client.ask(
            user_id,
            text=f"Please send the image of the IPL {WAIFU} you want to upload!",
            filters=filters.photo,
            timeout=60,
            reply_markup=btn
        )
        file_path = await img_message.download()

        # Upload the file to Catbox
        with open(file_path, "rb") as image_file:
            response = requests.post(
                CATBOX_API_URL,
                data={"reqtype": "fileupload"},
                files={"fileToUpload": image_file},
            )

        if response.status_code == 200 and response.text.startswith("https"):
            img_url = response.text.strip()

        upload_details[user_id] = {"img_url": img_url.strip()}

        btn = InlineKeyboardMarkup([
            [InlineKeyboardButton("Cancel Upload", callback_data="close_upload")]
        ])
        name_message: Message = await client.ask(
            user_id,
            text=f"Image uploaded: {img_url}\n\nNow please send the {WAIFU} name.",
            timeout=60,
            reply_markup=btn
        )
        upload_details[user_id]["name"] = name_message.text.strip()

        btn = InlineKeyboardMarkup([
            [
                InlineKeyboardButton(f"Sᴇᴀʀᴄʜ {ANIME}", switch_inline_query_current_chat=".anime "),
                InlineKeyboardButton("Cancel", callback_data="close_upload")
            ]
        ])
        team_message: Message = await client.ask(
            user_id,
            text=f"Please send the {ANIME} ID. Use the button below to search for the {ANIME}.",
            timeout=60,
            reply_markup=btn
        )
        team_id_text = team_message.text.strip()
        if "🆔 ID:" in team_id_text:
            match = re.search(r'🆔\s*ID:\s*(\d+)', team_id_text)
            if match:
                team_id = int(match.group(1))
                upload_details[user_id]["anime_id"] = team_id
                try : 
                    a = await get_anime_details_by_anime_id(team_id)
                    upload_details[user_id]["anime"] = a["name"]
                except Exception as e :
                    print(e)
            else :
                await team_message.reply_text(f"Failed To Get The {ANIME} Info , Please Create That {ANIME} And Try Again !!")
                return

        rarity_buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton(f"{v['sign']} {v['name']}", callback_data=f"glob_{k}")] 
        for k, v in RARITY_MAPPING.items()
        ])
        rarity_choice : CallbackQuery = await client.ask(
            user_id,
            text="Now choose the rarity:",
            timeout=60,
            filters=filters.regex("glob_.*"),
            reply_markup=rarity_buttons,
            listener_type=ListenerTypes.CALLBACK_QUERY
        )
        rarity_key = rarity_choice.data.split("_")[1]
        rarity = RARITY_MAPPING[rarity_key]
        upload_details[user_id].update({"rarity": rarity["name"], "rarity_sign": rarity["sign"]})
        await rarity_choice.message.delete()

        # Add IPL event automatically
        upload_details[user_id].update({"event": "IPL 2025", "event_sign": "🏏"})

        # Ask for start date
        start_date_message: Message = await client.ask(
            user_id,
            text=f"Please enter the start date for this IPL {WAIFU} card (format: YYYY-MM-DD):",
            timeout=60,
            filters=filters.text,
            reply_markup=btn
        )
        
        try:
            import datetime
            start_date = datetime.datetime.strptime(start_date_message.text.strip(), "%Y-%m-%d").date()
            upload_details[user_id]["date_range"] = {"start": start_date}
        except ValueError:
            await start_date_message.reply_text("Invalid date format. Please use YYYY-MM-DD format.")
            return

        # Ask for end date
        end_date_message: Message = await client.ask(
            user_id,
            text=f"Please enter the end date for this IPL {WAIFU} card (format: YYYY-MM-DD):",
            timeout=60,
            filters=filters.text,
            reply_markup=btn
        )
        
        try:
            end_date = datetime.datetime.strptime(end_date_message.text.strip(), "%Y-%m-%d").date()
            upload_details[user_id]["date_range"]["end"] = end_date
            
            # Validate date range
            if end_date < start_date:
                await end_date_message.reply_text("End date cannot be earlier than start date.")
                return
        except ValueError:
            await end_date_message.reply_text("Invalid date format. Please use YYYY-MM-DD format.")
            return

        data = upload_details[user_id]

        confirmation_text = (
            f"Please confirm the following details:\n\n"
            f"📸 Image URL: {data['img_url']}\n"
            f"📝 Name: {data['name']}\n"
            f"📺 {ANIME}: {data.get('anime', 'N/A')}\n"
            f"🆔 {ANIME} ID: {data['anime_id']}\n"
            f"🌟 Rarity: {data['rarity']} {data['rarity_sign']}\n"
            f"🏏 Event: {data['event']} {data['event_sign']}\n"
            f"📅 Available From: {data['date_range']['start']} to {data['date_range']['end']}\n"
        )

        confirm_buttons = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("Confirm Upload", callback_data="ipl_confirm"),
                InlineKeyboardButton("Cancel", callback_data="close_upload")
            ]
        ])
        await client.send_photo(
            user_id,
            photo=data['img_url'],
            caption=confirmation_text,
            reply_markup=confirm_buttons
        )

    except Exception as e:
        await callback_query.message.reply(f"Error: {str(e)}")

@app.on_callback_query(filters.regex("ipl_confirm"))
@capture_and_handle_error
async def confirm_ipl_upload_handler(client: Client, callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    data = upload_details.get(user_id)
    if not data:
        await callback_query.message.reply("No upload data found for IPL Upload")
        return

    character_id = await get_next_id()
    
    # Convert date objects to ISO format strings for MongoDB compatibility
    start_date = data['date_range']['start']
    end_date = data['date_range']['end']
    
    # Convert to string format that MongoDB can store
    start_date_str = start_date.isoformat()
    end_date_str = end_date.isoformat()
    
    character_doc = {
        "id": str(character_id),
        "img_url": data['img_url'],
        "name": data['name'],
        "anime": data.get('anime', "Unknown"),
        "anime_id": data['anime_id'],
        "rarity": data['rarity'],
        "rarity_sign": data['rarity_sign'],
        "event": data['event'],
        "event_sign": data['event_sign'],
        "date_range": {
            "start": start_date_str,
            "end": end_date_str
        }
    }

    await upload_waifu(character_doc)
    await callback_query.message.edit_caption(f"IPL {WAIFU} successfully uploaded." , reply_markup=None)
    del upload_details[user_id]
    
    text = f"<b>🏏 New IPL {WAIFU} Uploaded by {callback_query.from_user.mention}!!</b>\n\n"
    text += f"🎀 <b>Name :</b> {data['name']}\n"
    text += f"⛩️ <b>{ANIME} :</b> {data['anime']}\n"
    text += f"{data['rarity_sign']} <b>Rarity</b> : {data['rarity']}\n"
    text += f"📅 <b>Available From</b> : {start_date_str} to {end_date_str}\n\n"
    
    await app.send_photo(chat_id=SUPPORT_CHAT_ID , photo = data['img_url'] , caption=text , parse_mode=ParseMode.HTML)
    await app.send_photo(chat_id=LOG_CHANNEL , photo = data['img_url'] , caption=text , parse_mode=ParseMode.HTML)

@app.on_callback_query(filters.regex("view_ipl_players"))
@capture_and_handle_error
async def view_ipl_players(client: Client, callback_query: CallbackQuery):
    """
    View all IPL players in the database.
    
    Args:
        client: The Pyrogram client
        callback_query: The callback query
    """
    await callback_query.message.delete()
    
    try:
        # Find all characters with IPL 2025 event
        ipl_characters = await get_ipl_players()
        
        if not ipl_characters:
            await client.send_message(
                callback_query.from_user.id,
                f"No IPL {WAIFU} found in the database."
            )
            return
            
        # Group characters by date range
        from collections import defaultdict
        
        date_grouped = defaultdict(list)
        
        for character in ipl_characters:
            if "date_range" in character:
                start_date = character["date_range"]["start"]
                end_date = character["date_range"]["end"]
                date_key = f"{start_date} to {end_date}"
                date_grouped[date_key].append(character)
            else:
                date_grouped["No Date Range"].append(character)
                
        # Create a message with all IPL players grouped by date range
        reply_text = f"**🏏 All IPL {WAIFU} ({len(ipl_characters)} total):**\n\n"
        
        for date_range, characters in date_grouped.items():
            reply_text += f"**📅 {date_range}:**\n"
            
            for idx, character in enumerate(characters, 1):
                name = character.get("name", "Unknown")
                team = character.get("anime", "Unknown")
                rarity = character.get("rarity", "Unknown")
                rarity_sign = character.get("rarity_sign", "")
                char_id = character.get("id", "Unknown")
                
                reply_text += f"{idx}. **{name}** - {team} ({rarity_sign} {rarity}) [ID: {char_id}]\n"
                
            reply_text += "\n"
            
        # Split message if it's too long
        if len(reply_text) > 4000:
            chunks = [reply_text[i:i+4000] for i in range(0, len(reply_text), 4000)]
            for chunk in chunks:
                await client.send_message(
                    callback_query.from_user.id,
                    chunk
                )
        else:
            await client.send_message(
                callback_query.from_user.id,
                reply_text
            )
            
    except Exception as e:
        await client.send_message(
            callback_query.from_user.id,
            f"Error: {str(e)}"
        )

@app.on_message(filters.command("ipllist") & sudo_filter & filters.private)
@capture_and_handle_error
async def list_ipl_players(client: Client, message: Message):
    """
    List all IPL players in the database.
    
    Args:
        client: The Pyrogram client
        message: The message containing the command
    """
    try:
        # Find all characters with IPL 2025 event
        ipl_characters = await get_ipl_players()
        
        if not ipl_characters:
            await message.reply(f"No IPL {WAIFU} found in the database.")
            return
            
        # Group characters by date range
        from collections import defaultdict
        import datetime
        from pytz import timezone
        
        date_grouped = defaultdict(list)
        
        # Get current date in IST
        ist = timezone('Asia/Kolkata')
        current_date = datetime.datetime.now(ist).date()
        current_date_str = current_date.isoformat()
        
        for character in ipl_characters:
            if "date_range" in character:
                start_date = character["date_range"]["start"]
                end_date = character["date_range"]["end"]
                date_key = f"{start_date} to {end_date}"
                
                # Check if the character is currently active
                is_active = start_date <= current_date_str <= end_date
                status = "✅ ACTIVE" if is_active else "❌ INACTIVE"
                date_key = f"{date_key} [{status}]"
                
                date_grouped[date_key].append(character)
            else:
                date_grouped["No Date Range"].append(character)
                
        # Create a message with all IPL players grouped by date range
        reply_text = f"**🏏 All IPL {WAIFU} ({len(ipl_characters)} total):**\n\n"
        
        for date_range, characters in date_grouped.items():
            reply_text += f"**📅 {date_range}:**\n"
            
            for idx, character in enumerate(characters, 1):
                name = character.get("name", "Unknown")
                team = character.get("anime", "Unknown")
                rarity = character.get("rarity", "Unknown")
                rarity_sign = character.get("rarity_sign", "")
                char_id = character.get("id", "Unknown")
                
                reply_text += f"{idx}. **{name}** - {team} ({rarity_sign} {rarity}) [ID: {char_id}]\n"
                
            reply_text += "\n"
            
        # Split message if it's too long
        if len(reply_text) > 4000:
            chunks = [reply_text[i:i+4000] for i in range(0, len(reply_text), 4000)]
            for chunk in chunks:
                await message.reply(chunk)
        else:
            await message.reply(reply_text)
            
    except Exception as e:
        await message.reply(f"Error: {str(e)}")
