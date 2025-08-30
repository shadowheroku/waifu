from pyrogram import filters, Client
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, Message
from pyrogram.enums import ListenerTypes, ParseMode
from Bot import app  , RARITY_MAPPING , EVENT_MAPPING
from Bot.database.iddb import get_next_id
from Bot.database.animedb import get_anime_details_by_anime_id
from Bot.errors import capture_and_handle_error
import requests
from Bot.config import SUPPORT_CHAT_ID, LOG_CHANNEL
from Bot.utils import sudo_filter
from Bot.database.uploaddb import upload_waifu
from texts import WAIFU, ANIME

CATBOX_API_URL = "https://catbox.moe/user/api.php"

video_upload_details = {}

@app.on_callback_query(filters.regex("upload_video_waifu"))
@capture_and_handle_error
async def start_video_character_upload(client: Client, callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    await callback_query.message.delete()

    btn = InlineKeyboardMarkup([
        [InlineKeyboardButton("Cancel Upload", callback_data="close_video_upload")]
    ])

    try:
        # Ask for video
        video_message: Message = await client.ask(
            user_id,
            text=f"Please send the video of the {WAIFU} you want to upload! (Max duration: 25 seconds)",
            filters=filters.video,
            timeout=120,
            reply_markup=btn
        )

        # Check video duration
        if video_message.video.duration > 25:
            await video_message.reply_text("❌ Video duration must be 25 seconds or less.")
            return

        file_path = await video_message.download()

        # Upload the video file to Catbox
        with open(file_path, "rb") as video_file:
            response = requests.post(
                CATBOX_API_URL,
                data={"reqtype": "fileupload"},
                files={"fileToUpload": video_file},
            )

        if response.status_code == 200 and response.text.startswith("https"):
            video_url = response.text.strip()
            video_upload_details[user_id] = {"video_url": video_url.strip()}
        else:
            await video_message.reply_text("❌ Failed to upload video. Please try again.")
            return

        # Ask for name
        name_message: Message = await client.ask(
            user_id,
            text=f"Video uploaded: {video_url}\n\nNow please send the {WAIFU} name.",
            timeout=60,
            reply_markup=btn
        )
        video_upload_details[user_id]["name"] = name_message.text.strip()

        # Ask for anime
        btn = InlineKeyboardMarkup([
            [
                InlineKeyboardButton(f"Search {ANIME}", switch_inline_query_current_chat=".anime "),
                InlineKeyboardButton("Cancel", callback_data="close_video_upload")
            ]
        ])
        team_message: Message = await client.ask(
            user_id,
            text=f"Please send the {ANIME} ID. Use the button below to search for the {ANIME}.",
            timeout=60,
            reply_markup=btn
        )
        
        import re
        team_id_text = team_message.text.strip()
        if "🆔 ID:" in team_id_text:
            match = re.search(r'🆔\s*ID:\s*(\d+)', team_id_text)
            if match:
                team_id = int(match.group(1))
                video_upload_details[user_id]["anime_id"] = team_id
                try:
                    a = await get_anime_details_by_anime_id(team_id)
                    video_upload_details[user_id]["anime"] = a["name"]
                except Exception as e:
                    print(e)
            else:
                await team_message.reply_text(f"Failed To Get The {ANIME} Info, Please Create That {ANIME} And Try Again!")
                return

        # Ask for rarity
        rarity_buttons = InlineKeyboardMarkup([
            [InlineKeyboardButton(f"{v['sign']} {v['name']}", callback_data=f"vidglob_{k}")] 
            for k, v in RARITY_MAPPING.items()
        ])
        rarity_choice: CallbackQuery = await client.ask(
            user_id,
            text="Now choose the rarity:",
            timeout=60,
            filters=filters.regex("vidglob_.*"),
            reply_markup=rarity_buttons,
            listener_type=ListenerTypes.CALLBACK_QUERY
        )
        rarity_key = rarity_choice.data.split("_")[1]
        rarity = RARITY_MAPPING[rarity_key]
        video_upload_details[user_id].update({
            "rarity": rarity["name"], 
            "rarity_sign": rarity["sign"]
        })
        await rarity_choice.message.delete()

        # Ask for event (optional)
        event_buttons = InlineKeyboardMarkup([
            [InlineKeyboardButton(f"{v['sign']} {v['name']}", callback_data=f"videvent_{k}")]
            for k, v in EVENT_MAPPING.items()
        ] + [[InlineKeyboardButton("Skip Event", callback_data="videvent_skip")]])

        event_choice: CallbackQuery = await client.ask(
            user_id,
            text="Choose an event (or skip):",
            timeout=60,
            filters=filters.regex("videvent_.*"),
            reply_markup=event_buttons,
            listener_type=ListenerTypes.CALLBACK_QUERY
        )
        
        if event_choice.data != "videvent_skip":
            event_key = event_choice.data.split("_")[1]
            event = EVENT_MAPPING[event_key]
            video_upload_details[user_id].update({
                "event": event["name"],
                "event_sign": event["sign"]
            })
        await event_choice.message.delete()

        data = video_upload_details[user_id]

        # Show confirmation
        confirmation_text = (
            f"Please confirm the following details:\n\n"
            f"🎥 Video URL: {data['video_url']}\n"
            f"📝 Name: {data['name']}\n"
            f"📺 {ANIME}: {data.get('anime', 'N/A')}\n"
            f"🆔 {ANIME} ID: {data['anime_id']}\n"
            f"🌟 Rarity: {data['rarity']} {data['rarity_sign']}\n"
        )
        if data.get("event"):
            confirmation_text += f"🎉 Event: {data['event']} {data['event_sign']}\n"

        confirm_buttons = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("Confirm Upload", callback_data="vidglob_confirm"),
                InlineKeyboardButton("Cancel", callback_data="close_video_upload")
            ]
        ])
        
        # Send video preview with confirmation
        await client.send_video(
            user_id,
            video=data['video_url'],
            caption=confirmation_text,
            reply_markup=confirm_buttons
        )

    except Exception as e:
        await callback_query.message.reply(f"Error: {str(e)}")

@app.on_callback_query(filters.regex("vidglob_confirm"))
@capture_and_handle_error
async def confirm_video_upload_handler(client: Client, callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    data = video_upload_details.get(user_id)
    if not data:
        await callback_query.message.reply("No upload data found for Video Upload")
        return

    character_id = await get_next_id()
    character_doc = {
        "id": str(character_id),
        "video_url": data['video_url'],
        "name": data['name'],
        "anime": data.get('anime', "Unknown"),
        "anime_id": data['anime_id'],
        "rarity": data['rarity'],
        "rarity_sign": data['rarity_sign'],
        "is_video": True  # Add video flag
    }

    if data.get("event"):
        character_doc["event"] = data["event"]
        character_doc["event_sign"] = data["event_sign"]

    await upload_waifu(character_doc)
    await callback_query.message.edit_caption(f"Video {WAIFU} successfully uploaded.", reply_markup=None)
    del video_upload_details[user_id]

    # Send notifications
    text = f"<b>🎥 New Video {WAIFU} Uploaded by {callback_query.from_user.mention}!!</b>\n\n"
    text += f"🎀 <b>Name:</b> {data['name']}\n"
    text += f"⛩️ <b>{ANIME}:</b> {data['anime']}\n"
    text += f"{data['rarity_sign']} <b>Rarity:</b> {data['rarity']}\n"
    if data.get("event"):
        text += f"{data['event_sign']} <b>Event:</b> {data['event']}\n"

    # Send to support chat and log channel
    await app.send_video(
        chat_id=SUPPORT_CHAT_ID,
        video=data['video_url'],
        caption=text,
        parse_mode=ParseMode.HTML
    )
    await app.send_video(
        chat_id=LOG_CHANNEL,
        video=data['video_url'],
        caption=text,
        parse_mode=ParseMode.HTML
    )

@app.on_callback_query(filters.regex("close_video_upload"))
@capture_and_handle_error
async def close_video_upload(client: Client, callback: CallbackQuery):
    user_id = callback.from_user.id
    
    # Remove upload details from cache
    if user_id in video_upload_details:
        video_upload_details.pop(user_id, None)
    
    # Delete the message
    await callback.message.delete()
    
    # Send confirmation
    await client.send_message(
        chat_id=user_id,
        text="Video upload process has been canceled successfully."
    ) 