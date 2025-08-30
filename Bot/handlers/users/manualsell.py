from Bot import app, price
from Bot.database.characterdb import get_character_details
from Bot.database.smashdb import remove_smashed_image 
from Bot.database.grabtokendb import add_grab_token
from Bot.database.collectiondb import get_user_collection
from Bot import Command
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
import asyncio
from Bot.errors import capture_and_handle_error
from Bot.utils import warned_user_filter , command_filter
from texts import WAIFU , ANIME
from Bot.handlers.shared import pending_trades, pending_gifts, pending_mass_gifts

sell_locks = {}
active_sells = {}
mass_sell_locks = {}

def get_sell_lock(user_id: int):
    if user_id not in sell_locks:
        sell_locks[user_id] = asyncio.Lock()
    return sell_locks[user_id]

def get_mass_sell_lock(user_id: int):
    if user_id not in mass_sell_locks:
        mass_sell_locks[user_id] = asyncio.Lock()
    return mass_sell_locks[user_id]

@app.on_message(Command("sell") & command_filter)
@capture_and_handle_error
@warned_user_filter
async def sell(c: Client, m: Message):
    user_id = m.from_user.id
    args = m.text.split()

    if len(args) < 2:
        await m.reply(f"Please provide a {WAIFU} id. Usage: /sell <{WAIFU}_id>")
        return

    bt = InlineKeyboardMarkup([
        [InlineKeyboardButton("Cancel Last Sell", callback_data="zzz")]
    ])

    if user_id in active_sells:
        await m.reply("You have a pending sell action. Please complete or cancel it before starting a new one.", reply_markup=bt)
        return
        
    if user_id in pending_trades:
        await m.reply("🔄 You have a pending trade. Please complete or cancel it before initiating a sell.")
        return
        
    if user_id in pending_gifts or user_id in pending_mass_gifts:
        await m.reply("🔄 You have a pending gift. Please complete or cancel it before initiating a sell.")
        return

    player_id = args[1]

    user_collection = await get_user_collection(user_id)
    if not user_collection or not any(img["image_id"] == player_id for img in user_collection.get("images", [])):
        await m.reply(f"You don't own this {WAIFU}!")
        return

    active_sells[user_id] = True

    y = await get_character_details(player_id)
    
    if y.get("is_video", False):
        await m.reply(f"You cannot sell video {WAIFU}s!")
        return
    
    rarity = y["rarity"]
    p = price(rarity)

    btn = InlineKeyboardMarkup([
        [InlineKeyboardButton("Confirm", callback_data=f"m_{user_id}_{player_id}")],
        [InlineKeyboardButton("Cancel", callback_data="zzz")]
    ])
    
    await m.reply_photo(
        photo=y["img_url"],
        caption=f"**{y['rarity_sign']} {y['name']}**\n"
                f"**{y['anime']}**\n"
                f"**Price:** {p} **GRABTOKENS**\n"
                f"**Are you sure you want to list this {WAIFU} ?**",
        reply_markup=btn
    )


@app.on_callback_query(filters.regex(r"^m_(\d+)_(\S+)$"))
@capture_and_handle_error
async def confirm_sell_handler(c: Client, cb: CallbackQuery):
    try:
        parts = cb.data.split("_", 2)
        user_id = int(parts[1])
        player_id = parts[2]
        user_collection = await get_user_collection(user_id)
        
    except Exception:
        await cb.answer("Invalid callback data.", show_alert=True)
        return

    if cb.from_user.id != user_id:
        await cb.answer("You are not authorized to perform this action.", show_alert=True)
        return
    
    # Check if the character is still in the collection
    character_found = False
        
    for img in user_collection.get("images", []):
        if img["image_id"] == player_id:
            character_found = True
            break
                    
    if not character_found:
        await cb.answer(f"ʏᴏᴜ nᴏ ʟᴏɴɢᴇʀ ʜᴀᴠᴇ ᴛʜɪs {WAIFU} ɪɴ ʏᴏᴜʀ ᴄᴏʟʟᴇᴄᴛɪᴏɴ.", show_alert=True)
        return

    lock = get_sell_lock(user_id)
    async with lock:
        # Only process if the sale is still active
        if user_id not in active_sells:
            await cb.answer("Sell action was canceled.", show_alert=True)
            return
        # Mark the sale as processed
        del active_sells[user_id]

        y = await get_character_details(player_id)
        rarity = y["rarity"]
        p = price(rarity)

        await remove_smashed_image(user_id=user_id, image_id=player_id)
        await add_grab_token(user_id=user_id, amount=p)

        await cb.message.edit_caption(
            f"**{cb.from_user.mention} has successfully sold this {WAIFU} for {p} GrabTokens!**",
            reply_markup=None
        )
        await cb.answer("Sale processed successfully!")


@app.on_callback_query(filters.regex("^zzz$"))
@capture_and_handle_error
async def cancel_sell_handler(c: Client, cb: CallbackQuery):
    user_id = cb.from_user.id
    lock = get_sell_lock(user_id)
    async with lock:
        if user_id in active_sells:
            del active_sells[user_id]
    await cb.message.edit_caption("**Sell canceled.**", reply_markup=None)
    await cb.answer()

@app.on_message(Command("masssell") & command_filter)
@capture_and_handle_error
@warned_user_filter
async def mass_sell(c: Client, m: Message):
    user_id = m.from_user.id
    args = m.text.split()

    if len(args) < 2:
        await m.reply(f"Please provide {WAIFU} IDs separated by spaces. Usage: /masssell <{WAIFU}_id1> <{WAIFU}_id2> ...")
        return

    bt = InlineKeyboardMarkup([
        [InlineKeyboardButton("Cancel Mass Sell", callback_data="mass_cancel")]
    ])

    if user_id in active_sells:
        await m.reply("You have a pending sell action. Please complete or cancel it before starting a new one.", reply_markup=bt)
        return
        
    if user_id in pending_trades:
        await m.reply("🔄 You have a pending trade. Please complete or cancel it before initiating a mass sell.")
        return
        
    if user_id in pending_gifts or user_id in pending_mass_gifts:
        await m.reply("🔄 You have a pending gift. Please complete or cancel it before initiating a mass sell.")
        return

    # Limit the number of characters that can be sold at once
    MAX_CHARACTERS = 10
    player_ids = list(dict.fromkeys(args[1:]))  # Remove duplicates while preserving order
    
    if len(player_ids) > MAX_CHARACTERS:
        await m.reply(f"You can only sell up to {MAX_CHARACTERS} {WAIFU}s at once!")
        return

    user_collection = await get_user_collection(user_id)
    
    if not user_collection:
        await m.reply(f"You don't have any {WAIFU}s to sell!")
        return

    # Validate all characters exist in user's collection
    valid_ids = []
    total_tokens = 0
    characters_info = []
    seen_ids = set()  # Track seen IDs to prevent duplicates
    
    for player_id in player_ids:
        if player_id in seen_ids:
            continue
            
        if any(img["image_id"] == player_id for img in user_collection.get("images", [])):
            char_details = await get_character_details(player_id)
            if not char_details.get("is_video", False):
                valid_ids.append(player_id)
                total_tokens += price(char_details["rarity"])
                characters_info.append(char_details)
                seen_ids.add(player_id)
            else:
                await m.reply(f"Video {WAIFU}s cannot be sold! Skipping {player_id}")
                continue

    if not valid_ids:
        await m.reply(f"No valid {WAIFU}s found to sell!")
        return

    active_sells[user_id] = True

    # Create confirmation message with character details
    confirmation_text = f"**Mass Sell Confirmation**\n\n"
    for char in characters_info:
        confirmation_text += f"• {char['rarity_sign']} {char['name']} ({char['anime']}) - {price(char['rarity'])} tokens\n"
    confirmation_text += f"\n**Total Tokens to Receive:** {total_tokens}\n\n**Are you sure you want to sell these {WAIFU}s?**"

    # Store the valid IDs in active_sells for later use
    active_sells[user_id] = valid_ids

    btn = InlineKeyboardMarkup([
        [InlineKeyboardButton("Confirm Mass Sell", callback_data=f"mass_{user_id}")],
        [InlineKeyboardButton("Cancel", callback_data="mass_cancel")]
    ])
    
    await m.reply(confirmation_text, reply_markup=btn)

@app.on_callback_query(filters.regex(r"^mass_(\d+)$"))
@capture_and_handle_error
async def confirm_mass_sell_handler(c: Client, cb: CallbackQuery):
    try:
        user_id = int(cb.data.split("_")[1])
        if user_id not in active_sells:
            await cb.answer("Mass sell action was canceled.", show_alert=True)
            return
            
        valid_ids = active_sells[user_id]
        user_collection = await get_user_collection(user_id)
        
    except Exception:
        await cb.answer("Invalid callback data.", show_alert=True)
        return

    if cb.from_user.id != user_id:
        await cb.answer("You are not authorized to perform this action.", show_alert=True)
        return

    # Check if all characters are still in the collection
    final_valid_ids = []
    total_tokens = 0
    characters_info = []
    
    for player_id in valid_ids:
        if any(img["image_id"] == player_id for img in user_collection.get("images", [])):
            char_details = await get_character_details(player_id)
            if not char_details.get("is_video", False):
                final_valid_ids.append(player_id)
                total_tokens += price(char_details["rarity"])
                characters_info.append(char_details)

    if not final_valid_ids:
        await cb.answer(f"No valid {WAIFU}s found to sell!", show_alert=True)
        return

    lock = get_mass_sell_lock(user_id)
    async with lock:
        if user_id not in active_sells:
            await cb.answer("Mass sell action was canceled.", show_alert=True)
            return

        # Process all sales atomically
        for player_id in final_valid_ids:
            await remove_smashed_image(user_id=user_id, image_id=player_id)
        
        # Add total tokens at once
        await add_grab_token(user_id=user_id, amount=total_tokens)
        
        # Mark the sale as processed
        del active_sells[user_id]

        # Create success message
        success_text = f"**Mass Sell Successful!**\n\n"
        for char in characters_info:
            success_text += f"• Sold {char['rarity_sign']} {char['name']} ({char['anime']}) for {price(char['rarity'])} tokens\n"
        success_text += f"\n**Total Tokens Received:** {total_tokens}"

        await cb.message.edit_text(success_text, reply_markup=None)
        await cb.answer("Mass sale processed successfully!")

@app.on_callback_query(filters.regex("^mass_cancel$"))
@capture_and_handle_error
async def cancel_mass_sell_handler(c: Client, cb: CallbackQuery):
    user_id = cb.from_user.id
    lock = get_mass_sell_lock(user_id)
    async with lock:
        if user_id in active_sells:
            del active_sells[user_id]
    await cb.message.edit_text("**Mass sell canceled.**", reply_markup=None)
    await cb.answer()
