from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery 
from Bot.database.characterdb import get_character_details 
from Bot.database.collectiondb import get_user_collection, update_user_collection
from Bot.handlers.shared import pending_trades, pending_gifts, pending_mass_gifts
from Bot import app, Command
from Bot.utils import command_filter, warned_user_filter
from pyrogram.handlers import CallbackQueryHandler
from typing import Set, Tuple
from texts import WAIFU , ANIME 
from Bot.handlers.users.manualsell import active_sells

ongoing_gift_confirmations: Set[Tuple[int, int, str]] = set()


@app.on_message(Command("gift") & filters.group & filters.reply & command_filter)
@warned_user_filter
async def gift_character(client: Client, message: Message):
    from_user_id = message.from_user.id

    # Check if the user is already in a pending trade
    if from_user_id in pending_trades:
        await message.reply("**🔄 ʏᴏᴜ ʜᴀᴠᴇ ᴀ ᴘᴇnᴅɪnɢ ᴛʀᴀᴅᴇ. ᴘʟᴇᴀsᴇ ᴄᴏᴍᴘʟᴇᴛᴇ ᴏʀ ᴄᴀnᴄᴇʟ ɪᴛ ʙᴇғᴏʀᴇ ɪnɪᴛɪᴀᴛɪnɢ ᴀ ɢɪғᴛ.**")
        return
        
    if from_user_id in active_sells:
        await message.reply("**🔄 ʏᴏᴜ ʜᴀᴠᴇ ᴀ ᴘᴇnᴅɪnɢ sᴇʟʟ. ᴘʟᴇᴀsᴇ ᴄᴏᴍᴘʟᴇᴛᴇ ᴏʀ ᴄᴀnᴄᴇʟ ɪᴛ ʙᴇғᴏʀᴇ ɪnɪᴛɪᴀᴛɪnɢ ᴀ ɢɪғᴛ.**")
        return

    if len(message.command) != 2:
        await message.reply(f"**🔄 ᴜsᴀɢᴇ: /ɢɪғᴛ [id of {WAIFU}], ʀᴇᴘʟʏ ᴛᴏ ᴛʜᴇ ᴜsᴇʀ ʏᴏᴜ ᴡᴀnᴛ ᴛᴏ ɢɪғᴛ.**")
        return

    image_id = message.command[1]
    to_user_id = message.reply_to_message.from_user.id if message.reply_to_message else None

    if not to_user_id:
        await message.reply("**❗ ʏᴏᴜ nᴇᴇᴅ ᴛᴏ ʀᴇᴘʟʏ ᴛᴏ ᴛʜᴇ ᴜsᴇʀ ʏᴏᴜ ᴡᴀnᴛ ᴛᴏ ɢɪғᴛ.**")
        return

    if to_user_id == from_user_id:
        await message.reply(f"**🚫 ʏᴏᴜ ᴄᴀnnᴏᴛ ɢɪғᴛ ᴀ {WAIFU} ᴛᴏ ʏᴏᴜʀsᴇʟғ.**")
        return

    if message.reply_to_message.from_user.is_bot:
        await message.reply(f"**🤖 ʏᴏᴜ ᴄᴀnnᴏᴛ ɢɪғᴛ ᴀ {WAIFU} ᴛᴏ ᴀ ʙᴏᴛ.**")
        return
        
    if to_user_id in active_sells:
        await message.reply(f"**🚫 ᴛʜᴇ ᴜsᴇʀ ʏᴏᴜ ᴀʀᴇ ᴛʀʏɪnɢ ᴛᴏ ɢɪғᴛ ᴛᴏ ɪs ᴀʟʀᴇᴀᴅʏ ʙᴜsʏ ɪn ᴀ sᴇʟʟ.**")
        return

    if from_user_id in pending_gifts or from_user_id in pending_mass_gifts:
        cancel_last_gift_button = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        "❌ ᴄᴀnᴄᴇʟ ʟᴀsᴛ ɢɪғᴛ",
                        callback_data=f"cancel_last_gift|{from_user_id}"
                    )
                ]
            ]
        )
        await message.reply("**🔄 ʏᴏᴜ ʜᴀᴠᴇ ᴀʟʀᴇᴀᴅʏ ɪnɪᴛɪᴀᴛᴇᴅ ᴀ ɢɪғᴛ. ᴘʟᴇᴀsᴇ ᴄᴏnғɪʀᴍ ᴏʀ ᴄᴀnᴄᴇʟ ɪᴛ ʙᴇғᴏʀᴇ sᴛᴀʀᴛɪnɢ ᴀ nᴇᴡ ᴏnᴇ.**", reply_markup=cancel_last_gift_button)
        return

    # Fetch from_user's collection
    from_user_collection = await get_user_collection(from_user_id)

    if not from_user_collection or not any(img['image_id'] == image_id for img in from_user_collection.get('images', [])):
        await message.reply(f"**⚠️ ʏᴏᴜ ᴅᴏɴ'ᴛ ʜᴀᴠᴇ {WAIFU} ɪɴ ʏᴏᴜʀ ᴄᴏʟʟᴇᴄᴛɪᴏɴ.**")
        return

    character = await get_character_details(image_id)
    if not character:
        await message.reply(f"**❓ {WAIFU} nᴏᴛ ғᴏᴜɴᴅ**.")
        return

    # Send confirmation message with inline buttons placed vertically
    confirm_button = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "✅ ᴄᴏnғɪʀᴍ",
                    callback_data=f"confirm_gift|{from_user_id}|{to_user_id}|{image_id}"
                )
            ],
            [
                InlineKeyboardButton(
                    "❌ ᴄᴀnᴄᴇʟ",
                    callback_data=f"cancel_gift|{from_user_id}"
                )
            ]
        ]
    )
    
    pending_gifts[from_user_id] = True
    
    await message.reply(
        f"**ℹ️ ᴀʀᴇ ʏᴏᴜ sᴜʀᴇ ʏᴏᴜ ᴡᴀnᴛ ᴛᴏ ɢɪғᴛ:**\n"
        f"☘️ **Name**: {character['name']} [{character['rarity_sign']}]\n"
        f"🌙 **{ANIME}**: {character['anime']}\n\n"
        f"**To**: {message.reply_to_message.from_user.mention}?",
        reply_markup=confirm_button
    )
    

async def confirm_gift(client: Client, callback_query: CallbackQuery):
    try:
        _, from_user_id, to_user_id, image_id = callback_query.data.split("|")
        from_user_id, to_user_id = int(from_user_id), int(to_user_id)

        # Prevent duplicate confirmations
        gift_key = (from_user_id, to_user_id, image_id)
        if gift_key in ongoing_gift_confirmations:
            await callback_query.answer("ᴛʜɪs ɢɪғᴛ ɪs ᴀʟʀᴇᴀᴅʏ ʙᴇɪnɢ ᴘʀᴏᴄᴇssᴇᴅ.", show_alert=True)
            return

        # Lock the gift confirmation
        ongoing_gift_confirmations.add(gift_key)

        try:
            if callback_query.from_user.id != from_user_id:
                await callback_query.answer("ʏᴏᴜ ᴀʀᴇ nᴏᴛ ᴀʟʟᴏᴡᴇᴅ ᴛᴏ ᴄᴏnғɪʀᴍ ᴛʜɪs ɢɪғᴛ.", show_alert=True)
                return

            if from_user_id not in pending_gifts:
                await callback_query.answer("ᴛʜɪs ɢɪғᴛ ɪs nᴏ ʟᴏnɢᴇʀ ᴠᴀʟɪᴅ.", show_alert=True)
                return

            # Fetch both users' collections
            from_user_collection = await get_user_collection(from_user_id)
            to_user_collection = await get_user_collection(to_user_id)

            if not from_user_collection:
                await callback_query.answer("ʏᴏᴜʀ ᴄᴏʟʟᴇᴄᴛɪᴏn ᴄᴏᴜʟᴅ nᴏᴛ ʙᴇ ғᴏᴜnᴅ.", show_alert=True)
                return

            # Check if the character is still in the collection
            character_found = False
            for img in from_user_collection.get("images", []):
                if img["image_id"] == image_id:
                    character_found = True
                    break
                    
            if not character_found:
                await callback_query.answer(f"ʏᴏᴜ nᴏ ʟᴏɴɢᴇʀ ʜᴀᴠᴇ {WAIFU} ɪɴ ʏᴏᴜʀ ᴄᴏʟʟᴇᴄᴛɪᴏɴ.", show_alert=True)
                return

            # Remove the character from the from_user's collection
            updated_from_images = []
            for img in from_user_collection.get("images", []):
                if img["image_id"] == image_id:
                    if img["count"] > 1:
                        img["count"] -= 1
                        updated_from_images.append(img)
                else:
                    updated_from_images.append(img)
            
            # Add the character to the to_user's collection
            to_user_images = []
            if to_user_collection:
                to_user_images = to_user_collection.get("images", [])
                existing_image = next((img for img in to_user_images if img["image_id"] == image_id), None)
                if existing_image:
                    existing_image["count"] += 1
                else:
                    to_user_images.append({"image_id": image_id, "count": 1})
            else:
                to_user_images = [{"image_id": image_id, "count": 1}]

            # Update both collections in the database
            await update_user_collection(from_user_id, updated_from_images)
            await update_user_collection(to_user_id, to_user_images)

            from_user_mention = (await client.get_users(from_user_id)).mention
            to_user_mention = (await client.get_users(to_user_id)).mention
            character = await get_character_details(image_id)

            await callback_query.edit_message_text(f"**{from_user_mention} ɢɪғᴛᴇᴅ {character['name']} ᴛᴏ {to_user_mention}!**")

            # Remove from pending gifts
            if from_user_id in pending_gifts:
                del pending_gifts[from_user_id]
        finally:
            # Unlock the gift confirmation
            ongoing_gift_confirmations.remove(gift_key)
    except Exception as e:
        # Handle any unexpected errors
        await callback_query.answer(f"An error occurred: {str(e)[:20]}...", show_alert=True)
        # Make sure to remove from ongoing confirmations even if an error occurs
        try:
            ongoing_gift_confirmations.remove((from_user_id, to_user_id, image_id))
        except:
            pass
        # Also remove from pending gifts
        if from_user_id in pending_gifts:
            del pending_gifts[from_user_id]


async def cancel_gift(client: Client, callback_query: CallbackQuery):
    try:
        _, from_user_id = callback_query.data.split("|")
        from_user_id = int(from_user_id)

        if callback_query.from_user.id != from_user_id:
            await callback_query.answer("ʏᴏᴜ ᴀʀᴇ nᴏᴛ ᴀʟʟᴏᴡᴇᴅ ᴛᴏ ᴄᴀnᴄᴇʟ ᴛʜɪs ɢɪғᴛ.", show_alert=True)
            return

        if from_user_id not in pending_gifts:
            await callback_query.answer("ᴛʜɪs ɢɪғᴛ ɪs nᴏ ʟᴏnɢᴇʀ ᴠᴀʟɪᴅ.", show_alert=True)
            return

        await callback_query.edit_message_text("**Gɪғᴛ ᴄᴀɴᴄᴇʟʟᴇᴅ.**")

        # Remove from pending gifts
        if from_user_id in pending_gifts:
            del pending_gifts[from_user_id]
    except Exception as e:
        await callback_query.answer(f"An error occurred: {str(e)[:20]}...", show_alert=True)
        if from_user_id in pending_gifts:
            del pending_gifts[from_user_id]


async def cancel_last_gift(client: Client, callback_query: CallbackQuery):
    try:
        _, from_user_id = callback_query.data.split("|")
        from_user_id = int(from_user_id)

        if callback_query.from_user.id != from_user_id:
            await callback_query.answer("Yᴏᴜ ᴀʀᴇ ɴᴏᴛ ᴀʟʟᴏᴡᴇᴅ ᴛᴏ ᴄᴀɴᴄᴇʟ ᴛʜɪs ɢɪғᴛ.", show_alert=True)
            return

        if from_user_id not in pending_gifts and from_user_id not in pending_mass_gifts:
            await callback_query.answer("Tʜɪs ɢɪғᴛ ɪs ɴᴏ ʟᴏɴɢᴇʀ ᴠᴀʟɪᴅ.", show_alert=True)
            return

        await callback_query.edit_message_text("**Lᴀsᴛ ɢɪғᴛ ᴄᴀɴᴄᴇʟʟᴇᴅ.**")

        # Remove from pending gifts
        if from_user_id in pending_gifts:
            del pending_gifts[from_user_id]
            
        # Also try to remove from pending_mass_gifts if it exists
        if from_user_id in pending_mass_gifts:
            del pending_mass_gifts[from_user_id]
    except Exception as e:
        await callback_query.answer(f"An error occurred: {str(e)[:20]}...", show_alert=True)
        # Clean up both pending gifts and mass gifts
        if from_user_id in pending_gifts:
            del pending_gifts[from_user_id]
        if from_user_id in pending_mass_gifts:
            del pending_mass_gifts[from_user_id]


app.add_handler(CallbackQueryHandler(confirm_gift, filters.regex(r"^confirm_gift\|") & command_filter))
app.add_handler(CallbackQueryHandler(cancel_gift, filters.regex(r"^cancel_gift\|") & command_filter))
app.add_handler(CallbackQueryHandler(cancel_last_gift, filters.regex(r"^cancel_last_gift\|") & command_filter))
