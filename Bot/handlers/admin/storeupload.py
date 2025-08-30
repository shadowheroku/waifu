from pyrogram import filters, Client
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, Message
import re
from pyrogram.enums import ListenerTypes
from Bot import app, EVENT_MAPPING
from Bot.database.uploaddb import RARITY_MAPPING_FOR_STORE, save_character_to_store, get_anime_for_upload, get_rarity_info_for_store
from Bot.errors import capture_and_handle_error
import requests
from Bot.config import SUPPORT_CHAT_ID, LOG_CHANNEL
from pyrogram.enums import ParseMode
from texts import WAIFU , ANIME

CATBOX_API_URL = "https://catbox.moe/user/api.php"

upload_details = {}

@app.on_callback_query(filters.regex("upload_waifu_to_store"))
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
            text=f"Please send the image of the {WAIFU} you want to upload to the store!",
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

        # Check if the upload was successful
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
                InlineKeyboardButton("Search Team", switch_inline_query_current_chat=".anime "),
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
                a = await get_anime_for_upload(team_id)
                upload_details[user_id]["anime"] = a["name"]
            else:
                await team_message.reply_text(f"Failed To Get The {ANIME} Info, Please Create That {ANIME} And Try Again !!")
                return

        rarity_buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton(f"{v['sign']} {v['name']}", callback_data=f"strrarity_{k}")] 
        for k, v in RARITY_MAPPING_FOR_STORE.items()
        ])
        rarity_choice : CallbackQuery = await client.ask(
            user_id,
            text=f"Now choose the rarity:",
            timeout=60,
            filters=filters.regex("strrarity_.*"),
            reply_markup=rarity_buttons,
            listener_type=ListenerTypes.CALLBACK_QUERY
        )
        rarity_key = rarity_choice.data.split("_")[1]
        rarity = await get_rarity_info_for_store(rarity_key)
        upload_details[user_id].update({"rarity": rarity["name"], "rarity_sign": rarity["sign"]})
        await rarity_choice.message.delete()

        event_buttons = InlineKeyboardMarkup([
            [InlineKeyboardButton(f"{v['sign']} {v['name']}", callback_data=f"strevent_{k}")]
            for k, v in EVENT_MAPPING.items()
        ] + [[InlineKeyboardButton("Skip Event", callback_data="strevent_skip")]])

        event_choice : CallbackQuery = await client.ask(
            user_id,
            text=f"Choose an event (or skip):",
            timeout=60,
            filters=filters.regex("strevent_.*"),
            reply_markup=event_buttons,
            listener_type=ListenerTypes.CALLBACK_QUERY
        )
        if event_choice.data != "strevent_skip":
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
                InlineKeyboardButton("Confirm Upload", callback_data="strconfirm_upload"),
                InlineKeyboardButton("Cancel", callback_data="strclose_upload")
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

@app.on_callback_query(filters.regex("strconfirm_upload"))
@capture_and_handle_error
async def confirm_upload_handler(client: Client, callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    data = upload_details.get(user_id)
    if not data:
        await callback_query.message.reply("No upload data found For Store Upload.")
        return

    await save_character_to_store(data)
    await callback_query.message.edit_caption(f"{WAIFU} successfully uploaded to the store.", reply_markup=None)
    del upload_details[user_id]
    text = f"**New {WAIFU} Uploaded To Store !!**\n\n"
    text += f"**Name :** {data['name']}\n"
    text += f"**{ANIME} :** {data['anime']}\n"
    text += f"{data['rarity_sign']} **Rarity** : {data['rarity']}\n\n"
    text += f"> You Can Purchase It {WAIFU} From Store !!"
    
    await app.send_photo(chat_id=SUPPORT_CHAT_ID, photo=data['img_url'], caption=text, parse_mode=ParseMode.MARKDOWN)
    await app.send_photo(chat_id=LOG_CHANNEL, photo=data['img_url'], caption=text, parse_mode=ParseMode.MARKDOWN)


@app.on_callback_query(filters.regex("strclose_upload"))
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
