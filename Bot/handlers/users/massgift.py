from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
from collections import Counter
from Bot.database.characterdb import get_character_details
from Bot.database.collectiondb import get_user_collection, update_user_collection
from Bot.handlers.shared import pending_trades, pending_gifts, pending_mass_gifts
from Bot import app, Command
from Bot.utils import command_filter, warned_user_filter
from pyrogram.handlers import CallbackQueryHandler
from texts import WAIFU
from Bot.handlers.users.manualsell import active_sells

@app.on_message(Command("massgift") & filters.group & filters.reply & command_filter)
@warned_user_filter
async def mass_gift_characters(client: Client, message: Message):
    from_user_id = message.from_user.id

    if from_user_id in pending_trades or from_user_id in pending_gifts or from_user_id in pending_mass_gifts:
        await message.reply("**🔄 You have a pending trade or gift. Please complete or cancel it first.**")
        return
        
    if from_user_id in active_sells:
        await message.reply("**🔄 You have a pending sell. Please complete or cancel it first.**")
        return

    if len(message.command) < 2:
        await message.reply("**🔄 Usage: /massgift [id1] [id2]... (reply to user)**")
        return

    image_ids = message.command[1:]
    
    if not message.reply_to_message or not message.reply_to_message.from_user:
        await message.reply("**❗ You need to reply to the user you want to gift characters to.**")
        return
        
    to_user = message.reply_to_message.from_user
    to_user_id = to_user.id

    if to_user_id == from_user_id:
        await message.reply(f"**🚫 You cannot gift {WAIFU} to yourself.**")
        return

    if to_user.is_bot:
        await message.reply(f"**🤖 You cannot gift {WAIFU} to bots.**")
        return
        
    if to_user_id in active_sells:
        await message.reply(f"**🚫 The user you are trying to gift to is already busy in a sell.**")
        return

    # Count occurrences of each ID
    image_id_counts = Counter(image_ids)
    
    # Get sender's collection
    from_user_collection = await get_user_collection(from_user_id)
    if not from_user_collection:
        await message.reply(f"**⚠️ You don't have any {WAIFU} to gift.**")
        return

    # Validate characters
    user_images = {img['image_id']: img for img in from_user_collection.get('images', [])}
    missing_ids = []
    insufficient_counts = []
    
    for img_id, req_count in image_id_counts.items():
        if img_id not in user_images:
            missing_ids.append(img_id)
        elif user_images[img_id]['count'] < req_count:
            insufficient_counts.append(f"{img_id} (needs {req_count})")

    if missing_ids:
        await message.reply(f"**❌ Missing {WAIFU}s:** {', '.join(missing_ids)}")
        return
        
    if insufficient_counts:
        await message.reply(f"**⚠️ Insufficient counts for:** {', '.join(insufficient_counts)}")
        return

    # Get character details
    characters = []
    for img_id in image_id_counts:
        character = await get_character_details(img_id)
        if not character:
            await message.reply(f"**❌ {WAIFU} {img_id} not found**")
            return
        characters.append((character, image_id_counts[img_id]))

    # Build confirmation message
    char_list = []
    for char, count in characters:
        count_text = f"{count}x " if count > 1 else ""
        char_list.append(f"☘️ {count_text}{char['name']} [{char['rarity_sign']}]\n🌙 {char['anime']}")
    
    confirmation_msg = (
        f"**ℹ️ Are you sure you want to gift these {WAIFU}s to {to_user.mention}?**\n\n" +
        "\n\n".join(char_list) )
    
    # Store pending mass gift
    pending_mass_gifts[from_user_id] = {
        'to_user_id': to_user_id,
        'image_id_counts': image_id_counts
    }

    # Create confirmation buttons
    buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Confirm", callback_data=f"confirm_mass_gift|{from_user_id}")],
        [InlineKeyboardButton("❌ Cancel", callback_data=f"cancel_mass_gift|{from_user_id}")]
    ])

    await message.reply(confirmation_msg, reply_markup=buttons)


async def confirm_mass_gift(client: Client, callback_query: CallbackQuery):
    try:
        _, from_user_id = callback_query.data.split("|")
        from_user_id = int(from_user_id)

        if callback_query.from_user.id != from_user_id:
            await callback_query.answer("You're not authorized to confirm this gift.", show_alert=True)
            return

        if from_user_id not in pending_mass_gifts:
            await callback_query.answer("This gift session has expired.", show_alert=True)
            return

        # Get gift data
        gift_data = pending_mass_gifts.pop(from_user_id)
        to_user_id = gift_data['to_user_id']
        image_id_counts = gift_data['image_id_counts']

        # Update sender's collection
        from_user_collection = await get_user_collection(from_user_id)
        if not from_user_collection:
            await callback_query.answer("Your collection could not be found.", show_alert=True)
            return
            
        # Verify all characters are still in the collection with sufficient counts
        user_images = {img['image_id']: img for img in from_user_collection.get('images', [])}
        for img_id, req_count in image_id_counts.items():
            if img_id not in user_images:
                await callback_query.answer(f"{WAIFU} {img_id} is no longer in your collection.", show_alert=True)
                return
            if user_images[img_id]['count'] < req_count:
                await callback_query.answer(f"Insufficient count for {WAIFU} {img_id}.", show_alert=True)
                return
        
        # Process the gift - update sender's collection
        updated_from_images = []
        for img in from_user_collection.get('images', []):
            img_id = img['image_id']
            if img_id in image_id_counts:
                if img['count'] > image_id_counts[img_id]:
                    img['count'] -= image_id_counts[img_id]
                    updated_from_images.append(img)
            else:
                updated_from_images.append(img)
        
        # Update receiver's collection
        to_user_collection = await get_user_collection(to_user_id)
        to_user_images = []
        
        if to_user_collection:
            to_user_images = to_user_collection.get('images', [])
            
        # Create a dictionary for easier updating
        to_user_img_dict = {img['image_id']: img for img in to_user_images}
        
        # Update or add gifted characters
        for img_id, count in image_id_counts.items():
            if img_id in to_user_img_dict:
                to_user_img_dict[img_id]['count'] += count
            else:
                to_user_img_dict[img_id] = {'image_id': img_id, 'count': count}
        
        # Convert back to list
        updated_to_images = list(to_user_img_dict.values())
        
        # Update both collections in the database
        await update_user_collection(from_user_id, updated_from_images)
        await update_user_collection(to_user_id, updated_to_images)

        # Send confirmation
        from_user_mention = (await client.get_users(from_user_id)).mention
        to_user_mention = (await client.get_users(to_user_id)).mention
        total_chars = sum(image_id_counts.values())
        
        await callback_query.edit_message_text(
            f"**🎁 {from_user_mention} successfully gifted {total_chars} {WAIFU}'s to {to_user_mention}!**"
        )
    except Exception as e:
        # Handle any unexpected errors
        await callback_query.answer(f"An error occurred: {str(e)[:20]}...", show_alert=True)
        # Clean up pending gifts
        if 'from_user_id' in locals() and from_user_id in pending_mass_gifts:
            del pending_mass_gifts[from_user_id]


async def cancel_mass_gift(client: Client, callback_query: CallbackQuery):
    try:
        _, from_user_id = callback_query.data.split("|")
        from_user_id = int(from_user_id)

        if callback_query.from_user.id != from_user_id:
            await callback_query.answer("You're not authorized to cancel this gift.", show_alert=True)
            return

        if from_user_id in pending_mass_gifts:
            del pending_mass_gifts[from_user_id]
        
        await callback_query.edit_message_text("**🚫 Mass gift cancelled.**")
    except Exception as e:
        await callback_query.answer(f"An error occurred: {str(e)[:20]}...", show_alert=True)
        # Clean up pending gifts
        if 'from_user_id' in locals() and from_user_id in pending_mass_gifts:
            del pending_mass_gifts[from_user_id]


app.add_handler(CallbackQueryHandler(confirm_mass_gift, filters.regex(r"^confirm_mass_gift\|") & command_filter))
app.add_handler(CallbackQueryHandler(cancel_mass_gift, filters.regex(r"^cancel_mass_gift\|") & command_filter))