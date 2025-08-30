from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
from Bot.database.collectiondb import get_user_collection, update_user_collection
from Bot.database.characterdb import get_character_details
import asyncio
from Bot.handlers.shared import pending_trades, pending_gifts, pending_mass_gifts
from Bot import app, Command
from Bot.utils import command_filter, warned_user_filter
from typing import Set
from texts import WAIFU , ANIME
from Bot.handlers.users.manualsell import active_sells

trade_lock = asyncio.Lock()
ongoing_trade_confirmations: Set[str] = set()


@app.on_message(Command("trade") & filters.reply & filters.group & command_filter)
@warned_user_filter
async def initiate_trade(client: Client, message: Message):
    user_a = message.from_user

    if user_a.id in pending_gifts or user_a.id in pending_mass_gifts:
        await message.reply("🔄 Yᴏᴜ ʜᴀᴠᴇ ᴀ ᴘᴇɴᴅɪɴɢ ɢɪғᴛ. Pʟᴇᴀsᴇ ᴄᴏᴍᴘʟᴇᴛᴇ ᴏʀ ᴄᴀɴᴄᴇʟ ɪᴛ ʙᴇғᴏʀᴇ ɪɴɪᴛɪᴀᴛɪɴɢ ᴀ ᴛʀᴀᴅᴇ.")
        return
        
    if user_a.id in active_sells:
        await message.reply("🔄 Yᴏᴜ ʜᴀᴠᴇ ᴀ ᴘᴇɴᴅɪɴɢ sᴇʟʟ. Pʟᴇᴀsᴇ ᴄᴏᴍᴘʟᴇᴛᴇ ᴏʀ ᴄᴀɴᴄᴇʟ ɪᴛ ʙᴇғᴏʀᴇ ɪɴɪᴛɪᴀᴛɪɴɢ ᴀ ᴛʀᴀᴅᴇ.")
        return

    if len(message.command) != 3:
        await message.reply("🔄 **Usᴀɢᴇ: `/trade Yᴏᴜʀ_Cʜᴀʀᴀᴄᴛᴇʀ_ID Usᴇʀ's_Cʜᴀʀᴀᴄᴛᴇʀ_ID`, ʀᴇᴘʟʏ ᴛᴏ ᴛʜᴇ ᴜsᴇʀ ʏᴏᴜ ᴡᴀɴᴛ ᴛᴏ ᴛʀᴀᴅᴇ ᴡɪᴛʜ.**")
        return

    char_a_id = message.command[1]
    char_b_id = message.command[2]

    user_b = message.reply_to_message.from_user if message.reply_to_message else None

    if not user_b:
        await message.reply("❗ Yᴏᴜ ɴᴇᴇᴅ ᴛᴏ ʀᴇᴘʟʏ ᴛᴏ ᴛʜᴇ ᴜsᴇʀ ʏᴏᴜ ᴡᴀɴᴛ ᴛᴏ ᴛʀᴀᴅᴇ ᴡɪᴛʜ.")
        return

    if user_a.id == user_b.id or user_b.is_bot:
        await message.reply("🚫 Yᴏᴜ ᴄᴀɴ'ᴛ ᴛʀᴀᴅᴇ ᴡɪᴛʜ ʏᴏᴜʀsᴇʟғ ᴏʀ ʙᴏᴛs.")
        return

    if user_a.id in pending_trades:
        cancel_button = InlineKeyboardMarkup([
            [InlineKeyboardButton("❌ Cᴀɴᴄᴇʟ Lᴀsᴛ Tʀᴀᴅᴇ", callback_data=f"cancel_last_trade|{user_a.id}")]
        ])
        await message.reply("🔄 Yᴏᴜ ʜᴀᴠᴇ ᴀʟʀᴇᴀᴅʏ ɪɴɪᴛɪᴀᴛᴇᴅ ᴀ ᴛʀᴀᴅᴇ. Pʟᴇᴀsᴇ ᴄᴏɴғɪʀᴍ ᴏʀ ᴄᴀɴᴄᴇʟ ɪᴛ ʙᴇғᴏʀᴇ sᴛᴀʀᴛɪɴɢ ᴀ ɴᴇᴡ ᴏɴᴇ.", reply_markup=cancel_button)
        return

    # Check if user_b is in a pending trade
    if user_b.id in pending_trades:
        await message.reply("🚫 Tʜᴇ ᴜsᴇʀ ʏᴏᴜ ᴀʀᴇ ᴛʀʏɪɴɢ ᴛᴏ ᴛʀᴀᴅᴇ ᴡɪᴛʜ ɪs ᴀʟʀᴇᴀᴅʏ ʙᴜsʏ ɪɴ ᴀɴᴏᴛʜᴇʀ ᴛʀᴀᴅᴇ.")
        return

    if user_b.id in pending_gifts or user_b.id in pending_mass_gifts:
        await message.reply("🚫 Tʜᴇ ᴜsᴇʀ ʏᴏᴜ ᴀʀᴇ ᴛʀʏɪɴɢ ᴛᴏ ᴛʀᴀᴅᴇ ᴡɪᴛʜ ɪs ᴀʟʀᴇᴀᴅʏ ʙᴜsʏ ɪɴ ᴀɴᴏᴛʜᴇʀ Gift.")
        return
        
    if user_b.id in active_sells:
        await message.reply("🚫 Tʜᴇ ᴜsᴇʀ ʏᴏᴜ ᴀʀᴇ ᴛʀʏɪɴɢ ᴛᴏ ᴛʀᴀᴅᴇ ᴡɪᴛʜ ɪs ᴀʟʀᴇᴀᴅʏ ʙᴜsʏ ɪɴ ᴀ sᴇʟʟ.")
        return

    # Fetch user collections
    user_a_collection = await get_user_collection(user_a.id)
    user_b_collection = await get_user_collection(user_b.id)

    if not user_a_collection or not any(img['image_id'] == char_a_id for img in user_a_collection.get('images', [])):
        await message.reply(f"⚠️ Yᴏᴜ ᴅᴏɴ'ᴛ ʜᴀᴠᴇ ᴛʜᴇ sᴘᴇᴄɪғɪᴇᴅ {WAIFU} ᴛᴏ ᴛʀᴀᴅᴇ.")
        return

    if not user_b_collection or not any(img['image_id'] == char_b_id for img in user_b_collection.get('images', [])):
        await message.reply(f"⚠️ Tʜᴇ ᴜsᴇʀ ᴅᴏᴇsɴ'ᴛ ʜᴀᴠᴇ ᴛʜᴇ sᴘᴇᴄɪғɪᴇᴅ {WAIFU} ᴛᴏ ᴛʀᴀᴅᴇ.")
        return

    if char_a_id == char_b_id:
        await message.reply(f"🚫 Yᴏᴜ ᴄᴀɴ'ᴛ ᴛʀᴀᴅᴇ ᴛʜᴇ sᴀᴍᴇ {WAIFU}.")
        return

    # Fetch character details
    char_a = await get_character_details(char_a_id)
    char_b = await get_character_details(char_b_id)

    if not char_a or not char_b:
        await message.reply(f"❓ Oɴᴇ ᴏғ ᴛʜᴇ {WAIFU}s ᴅᴏᴇsɴ'ᴛ ᴇxɪsᴛ.")
        return

    # Save the trade information
    trade_id = f"{user_a.id}_{user_b.id}"
    pending_trades[user_a.id] = trade_id
    pending_trades[user_b.id] = trade_id

    # Send the trade request message with inline buttons
    buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Cᴏɴғɪʀᴍ", callback_data=f"confirm_trade|{trade_id}|{char_a_id}|{char_b_id}"),
         InlineKeyboardButton("❌ Cᴀɴᴄᴇʟ", callback_data=f"cancel_trade|{trade_id}")]
    ])

    await message.reply(
        f"🔄 {user_a.mention} ᴡᴀnᴛs ᴛᴏ ᴛʀᴀᴅᴇ :\n\n**Name** : {char_a.get('name', 'Unknown Character')} [{char_a.get('rarity_sign')}]\n**Team** : {char_a.get('anime')}\n\nᴡɪᴛʜ {user_b.mention}'s sᴍᴀsʜᴇᴅ ᴡᴀɪғᴜ :\n\n**Name** : {char_b.get('name', 'Unknown Character')} [{char_b.get('rarity_sign')}].\n**Anime** : {char_b.get('anime')}\n\n**Cᴏɴғɪʀᴍ ᴏʀ Cᴀɴᴄᴇʟ Tʜᴇ Tʀᴀᴅᴇs Usɪɴɢ Tʜᴇ Bᴜᴛᴛᴏɴs Gɪᴠᴇɴ Bᴇʟᴏᴡ**",
        reply_markup=buttons
    )


@app.on_callback_query(filters.regex(r"^(confirm_trade|cancel_trade|cancel_last_trade)\|") & command_filter)
async def handle_trade_callback(client: Client, callback_query: CallbackQuery):
    try:
        data = callback_query.data.split("|")
        action = data[0]

        if action == "cancel_last_trade":
            user_id = callback_query.from_user.id
            trade_id = pending_trades.pop(user_id, None)
            if trade_id:
                other_user_id = int(trade_id.split("_")[0]) if int(trade_id.split("_")[0]) != user_id else int(trade_id.split("_")[1])
                if other_user_id in pending_trades:
                    del pending_trades[other_user_id]
                await callback_query.edit_message_text("**Yᴏᴜʀ ʟᴀsᴛ ᴛʀᴀᴅᴇ ʜᴀs ʙᴇᴇɴ ᴄᴀɴᴄᴇʟᴇᴅ.**")
            else:
                await callback_query.answer("Nᴏ ᴘᴇɴᴅɪɴɢ ᴛʀᴀᴅᴇ ғᴏᴜɴᴅ ᴛᴏ ᴄᴀɴᴄᴇʟ.", show_alert=True)
            return

        if len(data) < 2:
            await callback_query.answer("Iɴᴠᴀʟɪᴅ ᴛʀᴀᴅᴇ ᴅᴀᴛᴀ.", show_alert=True)
            return

        trade_id = data[1]

        if action == "confirm_trade" and len(data) < 4:
            await callback_query.answer("Iɴᴠᴀʟɪᴅ ᴛʀᴀᴅᴇ ᴅᴀᴛᴀ.", show_alert=True)
            return

        # Check if trade is pending
        if trade_id not in pending_trades.values():
            await callback_query.answer("Tʜɪs ᴛʀᴀᴅᴇ ɪs ɴᴏ ʟᴏɴɢᴇʀ ᴘᴇɴᴅɪɴɢ.", show_alert=True)
            await callback_query.edit_message_reply_markup(reply_markup=None)  # Remove buttons if the trade is not pending
            return

        user_a_id, user_b_id = map(int, trade_id.split("_"))

        # Ensure only the user who received the trade request can click the buttons
        if callback_query.from_user.id != user_b_id:
            await callback_query.answer("Yᴏᴜ ᴀʀᴇ ɴᴏᴛ ᴀʟʟᴏᴡᴇᴅ ᴛᴏ ᴘᴇʀғᴏʀᴍ ᴛʜɪs ᴀᴄᴛɪᴏɴ.", show_alert=True)
            return

        # Check if the trade is already being confirmed
        if trade_id in ongoing_trade_confirmations:
            await callback_query.answer("Tʜɪs ᴛʀᴀᴅᴇ ɪs ᴀʟʀᴇᴀᴅʏ ʙᴇɪɴɢ ᴘʀᴏᴄᴇssᴇᴅ.", show_alert=True)
            return

        # Lock this trade ID to prevent multiple confirmations
        ongoing_trade_confirmations.add(trade_id)

        try:
            if action == "cancel_trade":
                if user_a_id in pending_trades:
                    del pending_trades[user_a_id]
                if user_b_id in pending_trades:
                    del pending_trades[user_b_id]
                await callback_query.edit_message_text("**Tʀᴀᴅᴇ Cᴀɴᴄᴇʟᴇᴅ.**")
            elif action == "confirm_trade":
                char_a_id = data[2]
                char_b_id = data[3]
                
                # Verify characters still exist in collections
                user_a_collection = await get_user_collection(user_a_id)
                user_b_collection = await get_user_collection(user_b_id)
                
                if not user_a_collection or not any(img['image_id'] == char_a_id for img in user_a_collection.get('images', [])):
                    await callback_query.answer(f"Tʜᴇ ᴏᴛʜᴇʀ ᴜsᴇʀ ɴᴏ ʟᴏɴɢᴇʀ ʜᴀs ᴛʜᴇ {WAIFU} ᴛᴏ ᴛʀᴀᴅᴇ.", show_alert=True)
                    # Clean up pending trades
                    if user_a_id in pending_trades:
                        del pending_trades[user_a_id]
                    if user_b_id in pending_trades:
                        del pending_trades[user_b_id]
                    return
                
                if not user_b_collection or not any(img['image_id'] == char_b_id for img in user_b_collection.get('images', [])):
                    await callback_query.answer("Yᴏᴜ ɴᴏ ʟᴏɴɢᴇʀ ʜᴀᴠᴇ ᴛʜᴇ ᴄʜᴀʀᴀᴄᴛᴇʀ ᴛᴏ ᴛʀᴀᴅᴇ.", show_alert=True)
                    # Clean up pending trades
                    if user_a_id in pending_trades:
                        del pending_trades[user_a_id]
                    if user_b_id in pending_trades:
                        del pending_trades[user_b_id]
                    return
                
                async with trade_lock:
                    # Update user A's collection
                    updated_user_a_images = []
                    for img in user_a_collection.get("images", []):
                        if img["image_id"] == char_a_id:
                            if img["count"] > 1:
                                img["count"] -= 1
                                updated_user_a_images.append(img)
                        else:
                            updated_user_a_images.append(img)

                    # Update user B's collection
                    updated_user_b_images = []
                    for img in user_b_collection.get("images", []):
                        if img["image_id"] == char_b_id:
                            if img["count"] > 1:
                                img["count"] -= 1
                                updated_user_b_images.append(img)
                        else:
                            updated_user_b_images.append(img)

                    # Add character A to user B's collection
                    char_a_added = False
                    for img in updated_user_b_images:
                        if img["image_id"] == char_a_id:
                            img["count"] += 1
                            char_a_added = True
                            break
                    if not char_a_added:
                        updated_user_b_images.append({"image_id": char_a_id, "count": 1})

                    # Add character B to user A's collection
                    char_b_added = False
                    for img in updated_user_a_images:
                        if img["image_id"] == char_b_id:
                            img["count"] += 1
                            char_b_added = True
                            break
                    if not char_b_added:
                        updated_user_a_images.append({"image_id": char_b_id, "count": 1})

                    # Update the collections in the database
                    await update_user_collection(user_a_id, updated_user_a_images)
                    await update_user_collection(user_b_id, updated_user_b_images)

                    # Clean up pending trades
                    if user_a_id in pending_trades:
                        del pending_trades[user_a_id]
                    if user_b_id in pending_trades:
                        del pending_trades[user_b_id]
                    
                    user_a = await client.get_users(user_a_id)
                    user_b = await client.get_users(user_b_id)
                    char_a_details = await get_character_details(char_a_id)
                    char_b_details = await get_character_details(char_b_id)
                    
                    await callback_query.edit_message_text(
                        f"ᴛʀᴀᴅᴇ ᴄᴏᴍᴘʟᴇᴛᴇᴅ: {user_a.mention} ᴛʀᴀᴅᴇᴅ {char_a_details.get('name', 'Unknown Character')} ғᴏʀ {user_b.mention}'s {char_b_details.get('name', 'Unknown Character')}."
                    )
        finally:
            # Always remove from ongoing confirmations
            ongoing_trade_confirmations.discard(trade_id)
    except Exception as e:
        # Handle any unexpected errors
        await callback_query.answer(f"An error occurred: {str(e)[:20]}...", show_alert=True)
        # Make sure to clean up
        try:
            if 'trade_id' in locals():
                ongoing_trade_confirmations.discard(trade_id)
                user_a_id, user_b_id = map(int, trade_id.split("_"))
                if user_a_id in pending_trades:
                    del pending_trades[user_a_id]
                if user_b_id in pending_trades:
                    del pending_trades[user_b_id]
        except:
            pass

