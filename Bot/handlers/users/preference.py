from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
from Bot.database.preferencedb import get_smode_preference
from Bot.database.characterdb import get_character_details
from Bot import app , Command
from Bot.utils import command_filter , warned_user_filter
from Bot.errors import capture_and_handle_error
from Bot.database.smashdb import *
from Bot.database.collectiondb import get_user_collection
from Bot.database.preferencedb import fav_player , cmode_caption ,unfav_player , smode_detaile , smode_alpha , smode_anime_coun , smode_defaul , smode_rarit
from texts import WAIFU , ANIME

@app.on_message(Command("fav") & command_filter)
@warned_user_filter
@capture_and_handle_error
async def set_fav(client: Client, message: Message):
    user_id = message.from_user.id

    if len(message.command) < 2:
        await message.reply(f"Pʟᴇᴀsᴇ ᴘʀᴏᴠɪᴅᴇ ᴛʜᴇ {WAIFU} ID ᴛᴏ sᴇᴛ ᴀs ғᴀᴠᴏʀɪᴛᴇ.")
        return

    fav_character_id = message.command[1]

    # Fetch the user's collection
    user_collection = await get_user_collection(user_id)

    if not user_collection or not any(image["image_id"] == fav_character_id for image in user_collection["images"]):
        await message.reply(f"Yᴏᴜ ᴅᴏɴ'ᴛ ʜᴀᴠᴇ ᴛʜɪs {WAIFU} ɪɴ ʏᴏᴜʀ ᴄᴏʟʟᴇᴄᴛɪᴏɴ.")
        return

    # Fetch the character details
    character = await get_character_details(fav_character_id)
    if not character or "img_url" not in character:
        await message.reply(f"{WAIFU} ᴅᴇᴛᴀɪʟs ɴᴏᴛ ғᴏᴜɴᴅ.")
        return

    # Send confirmation message with character image and inline buttons
    await client.send_photo(
        chat_id=message.chat.id,
        photo=character["img_url"],
        caption=f"ᴅᴏ ʏᴏᴜ ᴡᴀnᴛ ᴛᴏ sᴇᴛ {character['name']} ᴀs ʏᴏᴜʀ ғᴀᴠᴏʀɪᴛᴇ {WAIFU}?",
        reply_markup=InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton("Cᴏɴғɪʀᴍ", callback_data=f"fav_confirm:{user_id}:{fav_character_id}"),
                    InlineKeyboardButton("Cᴀɴᴄᴇʟ", callback_data=f"fav_cancel:{user_id}")
                ]
            ]
        )
    )


@app.on_message(Command("unfav") & command_filter)
@warned_user_filter
@capture_and_handle_error
async def unfav(client: Client, message: Message):
    user_id = message.from_user.id

    # Remove the favorite character
    await unfav_player(user_id)

    await message.reply(f"Fᴀᴠᴏʀɪᴛᴇ {WAIFU} ʀᴇᴍᴏᴠᴇᴅ sᴜᴄᴄᴇssғᴜʟʟʏ!")


@app.on_callback_query(filters.regex(r"^fav_confirm:\d+:\d+$"))
@capture_and_handle_error
async def fav_confirm(client: Client, callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    data = callback_query.data.split(":")

    if len(data) != 3 or int(data[1]) != user_id:
        await callback_query.answer("🚫 Tʜɪs ᴀᴄᴛɪᴏɴ ɪs ɴᴏᴛ ғᴏʀ ʏᴏᴜ.", show_alert=True)
        return

    fav_character_id = data[2]

    # Set the favorite character
    await fav_player(user_id, fav_character_id)

    # Edit the message to confirm the action
    character = await get_character_details(fav_character_id)
    await callback_query.message.edit_caption(
        caption=f"✨{character['name']} ʜᴀs ʙᴇᴇn sᴇᴛ ᴀs ʏᴏᴜʀ ғᴀᴠᴏʀɪᴛᴇ {WAIFU}! 🎉",
        reply_markup=None
    )

    await callback_query.answer(f"✅ Fᴀᴠᴏʀɪᴛᴇ {WAIFU} sᴇᴛ sᴜᴄᴄᴇssғᴜʟʟʏ!")


@app.on_callback_query(filters.regex(r"^fav_cancel:\d+$"))
@capture_and_handle_error
async def fav_cancel(client: Client, callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    data = callback_query.data.split(":")
    
    if len(data) != 2 or int(data[1]) != user_id:
        await callback_query.answer("Tʜɪs ᴀᴄᴛɪᴏɴ ɪs ɴᴏᴛ ғᴏʀ ʏᴏᴜ.", show_alert=True)
        return

    # Edit the message to indicate the operation was canceled
    await callback_query.message.edit_caption(
        caption="Oᴘᴇʀᴀᴛɪᴏɴ ᴄᴀɴᴄᴇʟᴇᴅ.",
        reply_markup=None
    )

    await callback_query.answer("❌ Oᴘᴇʀᴀᴛɪᴏɴ ᴄᴀɴᴄᴇʟᴇᴅ.")



@app.on_message(Command("smode") & command_filter)
@capture_and_handle_error
@warned_user_filter
async def smode(client: Client, message: Message):
    user_id = message.from_user.id

    await message.reply(
        "🔧 **Cᴜsᴛᴏᴍɪᴢᴇ ʏᴏᴜʀ ʜᴜɴᴛꜱ  ɪɴᴛᴇʀғᴀᴄᴇ ᴜsɪɴɢ ᴛʜᴇ ʙᴜᴛᴛᴏɴs ʙᴇʟᴏᴡ:**",
        reply_markup=InlineKeyboardMarkup(
            [
                [InlineKeyboardButton(f"📚 Sᴏʀᴛ ʙʏ {ANIME}", callback_data=f"smode_anime:{user_id}"),
                 InlineKeyboardButton("🔢 Sᴏʀᴛ ʙʏ Rᴀʀɪᴛʏ", callback_data=f"smode_sort:{user_id}")],
                [InlineKeyboardButton("🔍 Dᴇᴛᴀɪʟᴇᴅ Mᴏᴅᴇ", callback_data=f"smode_detailed:{user_id}")],
                [InlineKeyboardButton("🖼 Dᴇғᴀᴜʟᴛ", callback_data=f"smode_default:{user_id}")],
                [InlineKeyboardButton("❌ Cʟᴏsᴇ", callback_data=f"smode_close:{user_id}")]
            ]
        )
    )


@app.on_callback_query(filters.regex(r"^smode_anime:\d+$"))
@capture_and_handle_error
async def smode_anime(client: Client, callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    data = callback_query.data.split(":")

    if len(data) != 2 or int(data[1]) != user_id:
        await callback_query.answer("🚫 Tʜɪs ᴀᴄᴛɪᴏɴ ɪs ɴᴏᴛ ғᴏʀ ʏᴏᴜ.", show_alert=True)
        return

    await callback_query.message.edit_text(
        f"🔧 **Cʜᴏᴏsᴇ ʏᴏᴜʀ sᴏʀᴛɪɴɢ ᴍᴇᴛʜᴏᴅ ғᴏʀ {ANIME}:**",
        reply_markup=InlineKeyboardMarkup(
            [
                [InlineKeyboardButton("🔤 Aʟᴘʜᴀʙᴇᴛɪᴄᴀʟʟʏ", callback_data=f"smode_anime_alpha:{user_id}")],
                [InlineKeyboardButton("📈 Bʏ Cᴏᴜɴᴛɪɴɢ", callback_data=f"smode_anime_count:{user_id}")],
                [InlineKeyboardButton("❌ Cʟᴏsᴇ", callback_data=f"smode_close:{user_id}")]
            ]
        )
    )

@app.on_callback_query(filters.regex(r"^smode_detailed:\d+$"))
@capture_and_handle_error
async def smode_detailed(client: Client, callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    data = callback_query.data.split(":")

    if len(data) != 2 or int(data[1]) != user_id:
        await callback_query.answer("🚫 Tʜɪs ᴀᴄᴛɪᴏɴ ɪs ɴᴏᴛ ғᴏʀ ʏᴏᴜ.", show_alert=True)
        return

    # Update the preference for Detailed Mode
    await smode_detaile(user_id)

    await callback_query.message.edit_text(
        f"🔄 **Yᴏᴜʀ ᴄᴏʟʟᴇᴄᴛɪᴏɴ ɪɴᴛᴇʀғᴀᴄᴇ ʜᴀs ʙᴇᴇɴ sᴇᴛ ᴛᴏ: Dᴇᴛᴀɪʟᴇᴅ Mᴏᴅᴇ**",
        reply_markup=None
    )

    await callback_query.answer("✅ ᴄᴏʟʟᴇᴄᴛɪᴏɴ ɪɴᴛᴇʀғᴀᴄᴇ sᴇᴛ ᴛᴏ Dᴇᴛᴀɪʟᴇᴅ Mᴏᴅᴇ.")

@app.on_callback_query(filters.regex(r"^smode_anime_alpha:\d+$"))
@capture_and_handle_error
async def smode_anime_alpha(client: Client, callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    data = callback_query.data.split(":")

    if len(data) != 2 or int(data[1]) != user_id:
        await callback_query.answer("🚫 Tʜɪs ᴀᴄᴛɪᴏɴ ɪs ɴᴏᴛ ғᴏʀ ʏᴏᴜ.", show_alert=True)
        return

    # Update the preference for Anime Alphabetically
    await smode_alpha(user_id)

    await callback_query.message.edit_text(
        f"🔄 **Yᴏᴜʀ ᴄᴏʟʟᴇᴄᴛɪᴏɴᴛꜱ ɪɴᴛᴇʀғᴀᴄᴇ ʜᴀs ʙᴇᴇɴ sᴇᴛ ᴛᴏ: {ANIME} Aʟᴘʜᴀʙᴇᴛɪᴄᴀʟʟʏ**",
        reply_markup=None
    )

    await callback_query.answer(f"✅ ᴄᴏʟʟᴇᴄᴛɪᴏɴ ɪɴᴛᴇʀғᴀᴄᴇ sᴇᴛ ᴛᴏ {ANIME} ᴀʟᴘʜᴀʙᴇᴛɪᴄᴀʟʟʏ.")

@app.on_callback_query(filters.regex(r"^smode_anime_count:\d+$"))
@capture_and_handle_error
async def smode_anime_count(client: Client, callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    data = callback_query.data.split(":")

    if len(data) != 2 or int(data[1]) != user_id:
        await callback_query.answer("🚫 Tʜɪs ᴀᴄᴛɪᴏɴ ɪs ɴᴏᴛ ғᴏʀ ʏᴏᴜ.", show_alert=True)
        return

    # Update the preference for Anime by Counting
    await smode_anime_coun(user_id)

    await callback_query.message.edit_text(
        f"🔄 **Yᴏᴜʀ ᴄᴏʟʟᴇᴄᴛɪᴏɴ ɪɴᴛᴇʀғᴀᴄᴇ ʜᴀs ʙᴇᴇɴ sᴇᴛ ᴛᴏ: {ANIME} ʙʏ Cᴏᴜɴᴛɪɴɢ**",
        reply_markup=None
    )

    await callback_query.answer(f"✅ ᴄᴏʟʟᴇᴄᴛɪᴏɴ ɪɴᴛᴇʀғᴀᴄᴇ sᴇᴛ ᴛᴏ {ANIME} ʙʏ ᴄᴏᴜɴᴛɪɴɢ.")

@app.on_callback_query(filters.regex(r"^smode_default:\d+$"))
@capture_and_handle_error
async def smode_default(client: Client, callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    data = callback_query.data.split(":")

    if len(data) != 2 or int(data[1]) != user_id:
        await callback_query.answer("🚫 Tʜɪs ᴀᴄᴛɪᴏɴ ɪs ɴᴏᴛ ғᴏʀ ʏᴏᴜ.", show_alert=True)
        return

    # Update the preference with default enabled and reset detailed mode
    await smode_defaul(user_id)

    await callback_query.message.edit_text(
        f"🔄 **Yᴏᴜʀ ᴄᴏʟʟᴇᴄᴛɪᴏɴ ɪɴᴛᴇʀғᴀᴄᴇ ʜᴀs ʙᴇᴇɴ sᴇᴛ ᴛᴏ: Dᴇғᴀᴜʟᴛ**",
        reply_markup=None
    )

    await callback_query.answer(f"✅ ᴄᴏʟʟᴇᴄᴛɪᴏɴ ɪɴᴛᴇʀғᴀᴄᴇ sᴇᴛ ᴛᴏ ᴅᴇғᴀᴜʟᴛ.")


@app.on_callback_query(filters.regex(r"^smode_sort:\d+$"))
@capture_and_handle_error
async def smode_sort(client: Client, callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    data = callback_query.data.split(":")

    if len(data) != 2 or int(data[1]) != user_id:
        await callback_query.answer("Tʜɪs ᴀᴄᴛɪᴏɴ ɪs ɴᴏᴛ ғᴏʀ ʏᴏᴜ.", show_alert=True)
        return

    smode_preference = await get_smode_preference(user_id)
    chosen_rarity = smode_preference.get("rarity", "None")

    await callback_query.message.edit_text(
        f"**Yᴏᴜʀ Hᴀʀᴇᴍ Sᴏʀᴛ Collects ɪs sᴇᴛ ᴛᴏ: {chosen_rarity}**",
        reply_markup=InlineKeyboardMarkup(
            [
                [InlineKeyboardButton("🟡 Lᴇɢᴇɴᴅᴀʀʏ", callback_data=f"smode_rarity:Legendary:{user_id}")],
                [InlineKeyboardButton("🟣 Rᴀʀᴇ", callback_data=f"smode_rarity:Rare:{user_id}")],
                [InlineKeyboardButton("🟢 Mᴇᴅɪᴜᴍ", callback_data=f"smode_rarity:Medium:{user_id}")],
                [InlineKeyboardButton("⚪️ Cᴏᴍᴍᴏɴ", callback_data=f"smode_rarity:Common:{user_id}")],
                [InlineKeyboardButton("💮 Exᴄʟᴜsɪᴠᴇ", callback_data=f"smode_rarity:Exclusive:{user_id}")],
                [InlineKeyboardButton("💠 Cᴏsᴍɪᴄ", callback_data=f"smode_rarity:Cosmic:{user_id}")],
                [InlineKeyboardButton("🔮 Lɪᴍɪᴛᴇᴅ Eᴅɪᴛɪᴏɴ", callback_data=f"smode_rarity:Limited Edition:{user_id}")],
                [InlineKeyboardButton("🔱 ᴜʟᴛɪᴍᴀᴛᴇ", callback_data=f"smode_rarity:Ultimate:{user_id}")],
                [InlineKeyboardButton("👑 ꜱᴜᴘʀᴇᴍᴇ", callback_data=f"smode_rarity:Supreme:{user_id}")],
                [InlineKeyboardButton("🟤 Uncommon", callback_data=f"smode_rarity:Uncommon:{user_id}")],
                [InlineKeyboardButton("⚜️ Epic", callback_data=f"smode_rarity:Epic:{user_id}")],
                [InlineKeyboardButton("🔴 Mythic", callback_data=f"smode_rarity:Mythic:{user_id}")],
                [InlineKeyboardButton("💫 Divine", callback_data=f"smode_rarity:Divine:{user_id}")],
                [InlineKeyboardButton("❄️ Ethereal", callback_data=f"smode_rarity:Ethereal:{user_id}")],
                [InlineKeyboardButton("🧿 Premium", callback_data=f"smode_rarity:Premium:{user_id}")],
                [InlineKeyboardButton("Cʟᴏsᴇ", callback_data=f"smode_close:{user_id}")]
            ]
        )
    )

@app.on_callback_query(filters.regex(r"^smode_rarity:[^:]+:\d+$"))
@capture_and_handle_error
async def smode_rarity(client: Client, callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    data = callback_query.data.split(":")

    if len(data) != 3 or int(data[2]) != user_id:
        await callback_query.answer("Tʜɪs ᴀᴄᴛɪᴏɴ ɪs ɴᴏᴛ ғᴏʀ ʏᴏᴜ.", show_alert=True)
        return

    rarity = callback_query.data.split(":")[1]

    # Update the preference for the chosen rarity
    await smode_rarit(user_id, rarity)

    await callback_query.message.edit_text(
        f"🔄 **Yᴏᴜʀ ᴄᴏʟʟᴇᴄᴛɪᴏɴ sᴏʀᴛ sʏsᴛᴇᴍ ʜᴀs ʙᴇᴇɴ sᴜᴄᴄᴇssғᴜʟʟʏ sᴇᴛ ᴛᴏ:{rarity}**",
        reply_markup=None
    )

    await callback_query.answer("✅ Collect's sᴏʀᴛ sʏsᴛᴇᴍ ᴜᴘᴅᴀᴛᴇᴅ.")

@app.on_callback_query(filters.regex(r"^smode_close:\d+$"))
@capture_and_handle_error
async def smode_close(client: Client, callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    data = callback_query.data.split(":")

    if len(data) != 2 or int(data[1]) != user_id:
        await callback_query.answer("Tʜɪs ᴀᴄᴛɪᴏɴ ɪs ɴᴏᴛ ғᴏʀ ʏᴏᴜ.", show_alert=True)
        return

    await callback_query.message.delete()

    await callback_query.answer("Oᴘᴇʀᴀᴛɪᴏɴ ᴄᴀɴᴄᴇʟᴇᴅ.")


@app.on_message(Command("cmode") & command_filter)
@warned_user_filter
@capture_and_handle_error
async def set_cmode(client: Client, message: Message):
    user_id = message.from_user.id

    await client.send_message(
        chat_id=message.chat.id,
        text="**📝 Please select your caption mode:**",
        reply_markup=InlineKeyboardMarkup(
            [
                [InlineKeyboardButton("🔹 Cᴀᴘᴛɪᴏɴ 1", callback_data=f"cmode_select:{user_id}:Caption 1")],
                [InlineKeyboardButton("🔸 Cᴀᴘᴛɪᴏɴ 2", callback_data=f"cmode_select:{user_id}:Caption 2")],
                [InlineKeyboardButton("❌ Cʟᴏsᴇ", callback_data=f"cmode_close:{user_id}")]
            ]
        )
    )

@app.on_callback_query(filters.regex(r"^cmode_select:\d+:") & command_filter)
@capture_and_handle_error
async def cmode_select(client: Client, callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    data = callback_query.data.split(":")
    selected_mode = data[2]

    if int(data[1]) != user_id:
        await callback_query.answer("Yᴏᴜ ᴀʀᴇ ɴᴏᴛ ᴀᴜᴛʜᴏʀɪᴢᴇᴅ ᴛᴏ ᴘᴇʀғᴏʀᴍ ᴛʜɪs ᴀᴄᴛɪᴏɴ.", show_alert=True)
        return

    await cmode_caption(user_id, selected_mode)

    await callback_query.edit_message_text(
    f"**Yᴏᴜʀ ɪɴʟɪɴᴇ ᴄᴀᴘᴛɪᴏɴ ᴘʀᴇғᴇʀᴇɴᴄᴇ ʜᴀs ʙᴇᴇɴ sᴇᴛ ᴛᴏ:**\n\n"
    f"**{selected_mode}** ✅"
)

@app.on_callback_query(filters.regex(r"^cmode_close:\d+$") & command_filter)
@capture_and_handle_error
async def cmode_close(client: Client, callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    data = callback_query.data.split(":")

    if int(data[1]) != user_id:
        await callback_query.answer("Yᴏᴜ ᴀʀᴇ ɴᴏᴛ ᴀᴜᴛʜᴏʀɪᴢᴇᴅ ᴛᴏ ᴘᴇʀғᴏʀᴍ ᴛʜɪs ᴀᴄᴛɪᴏɴ.", show_alert=True)
        return

    await callback_query.message.delete()
