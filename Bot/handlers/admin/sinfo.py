from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery, User
from pyrogram.errors import RPCError, PeerIdInvalid
from pyrogram.enums import MessageEntityType
from datetime import datetime
import asyncio
from Bot.database.privacydb import is_user_og , db
from Bot.database.bankdb import withdraw_from_bank
from Bot.database.grabtokendb import reset_user_balance
from Bot.database.collectiondb import delete_user_collection
from Bot.database.userdb import get_user_info
from Bot.config import OWNER_ID, LOG_CHANNEL, SUPPORT_CHAT_ID
from Bot import app, Command
from Bot.utils import og_filter
from Bot.errors import capture_and_handle_error
from texts import WAIFU , ANIME

async def resolve_user(client: app, message: Message):  # type: ignore
    try:
        if message.reply_to_message and message.reply_to_message.from_user:
            return message.reply_to_message.from_user

        if message.command:
            args = message.command[1:]
            if args:
                query = args[0]

                if query.isdigit():
                    try:
                        return await app.get_users(int(query))
                    except RPCError:
                        return None

                if query.startswith("@"):
                    try:
                        return await app.get_users(query)
                    except RPCError:
                        return None

        if message.entities:
            for entity in message.entities:
                if entity.type == MessageEntityType.TEXT_MENTION and entity.user:
                    return entity.user

        return None

    except PeerIdInvalid:
        return None

async def get_user_string(user: User) -> str:
    return f"{user.mention} (`{user.id}`)" if user else "Unknown User"

async def log_action(action: str, admin: User, target_user: User, details: str = ""):
    log_text = (
        "📜 **Admin Action Log**\n"
        f"🛠 **Action**: {action}\n"
        f"👮 **Admin**: {await get_user_string(admin)}\n"
        f"🎯 **Target**: {await get_user_string(target_user)}\n"
        f"📝 **Details**: {details}\n"
        f"🕒 **Timestamp**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    )
    await app.send_message(LOG_CHANNEL, log_text)
    await app.send_message(SUPPORT_CHAT_ID, log_text)

async def generate_user_info(target_user: User) -> str:
    try:
        # Get user info from database
        info = await get_user_info(target_user)
        
        response_text = (
            f"━━**ℹ User Info ℹ**━━\n"
            f"💫 **Name** : {info['first_name']}\n"
            f"👤 **Username** : @{info['username']}\n"
            f"🪪 **User ID** : {info['user_id']}\n"
            f"🏷️ **Mention** : {info['mention']}\n"
            f"🔹 **DC ID** : {info['dc_id']}\n\n"
            f"━━**Collection Stats**━━\n"
            f"🌿 **Total {WAIFU}** : {info['total_characters']}\n"
            f"🗨 **Unique {WAIFU}** : {info['unique_characters']}\n"
            f"🌄 **Collection Percentage** : {info['harem_percentage']:.2f}%\n"
            f"💸 **Balance** : {info['wallet_balance']}\n"
            f"🏦 **Bank Balance** : {info['bank_balance']}\n\n"   
            f"━━**Rarity Breakdown━━**\n"
            f"🟡 **Legendary** : {info['rarities']['Legendary']}\n"
            f"🟠 **Rare** : {info['rarities']['Rare']}\n"
            f"🟢 **Medium** : {info['rarities']['Medium']}\n"
            f"⚪️ **Common** : {info['rarities']['Common']}\n"
            f"💮 **Exclusive** : {info['rarities']['Exclusive']}\n"
            f"💠 **Cosmic** : {info['rarities']['Cosmic']}\n"
            f"🔮 **Limited Edition** : {info['rarities']['Limited Edition']}\n"
            f"🔱 **Ultimate** : {info['rarities']['Ultimate']}\n"   
            f"👑 **Supreme** : {info['rarities']['Supreme']}\n"   
            f"🟤 **Uncommon** : {info['rarities']['Uncommon']}\n"   
            f"⚜️ **Epic** : {info['rarities']['Epic']}\n"   
            f"🔴 **Mythic** : {info['rarities']['Mythic']}\n"   
            f"💫 **Divine** : {info['rarities']['Divine']}\n"   
            f"❄️ **Ethereal** : {info['rarities']['Ethereal']}\n"   
            f"🧿 **Premium** : {info['rarities']['Premium']}\n\n"
            f"🌏 **Global Position** : {info['global_position']}\n"
        )
        
        return response_text
    except Exception as e:
        return f"❌ Error generating info: {str(e)}"

@app.on_message(Command("info") & og_filter)
@capture_and_handle_error
async def info_handler(c: Client, m: Message):
    
    x = await m.reply_text("Getting User Info.....")
    
    try:
        target_user = await resolve_user(c, m)
        if not target_user:
            return await m.reply("❌ User not found!")

        btn = InlineKeyboardMarkup([[InlineKeyboardButton("🎛️ Aᴅᴍɪɴ Pᴀɴᴇʟ", callback_data=f"i_admin_{target_user.id}")],
                                    [InlineKeyboardButton("Cancel", callback_data="xxx")]])

        # Existing info generation code
        response = await generate_user_info(target_user)
        await m.reply(response, reply_markup=btn)
        await x.delete()
    except Exception as e:
        await m.reply(f"❌ Error: {str(e)}")
        await x.delete()

@app.on_callback_query(filters.regex(r"^i_admin_(\d+)$"))
async def adminpanel(c: Client, cb: CallbackQuery):
    if not await is_user_og(cb.from_user.id):
        await cb.answer("Nikal Lawde !!", show_alert=True)
        return

    target_id = int(cb.matches[0].group(1))  # Now correctly extracts the user ID

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("❌ Delete Collection", callback_data=f"kill_collection_{target_id}")],
        [InlineKeyboardButton("💸 Reset Wallet", callback_data=f"clean_wallet_{target_id}")],
        [InlineKeyboardButton("🏦 Clear Bank", callback_data=f"clear_bank_{target_id}")],
        [InlineKeyboardButton("⚡ Full Reset", callback_data=f"full_reset_{target_id}")],
        [InlineKeyboardButton("Cancel", callback_data="xxx")]
    ])

    await cb.message.edit_reply_markup(reply_markup=keyboard)    

@app.on_callback_query(filters.regex(r"^kill_collection_(\d+)$"))
@capture_and_handle_error
async def delete_collection_callback(c: Client, cb: CallbackQuery):
    if not await is_user_og(cb.from_user.id):
        await cb.answer("Access Denied!", show_alert=True)
        return
    
    target_id = int(cb.matches[0].group(1))
    admin_user = cb.from_user
    
    try:
        target_user = await app.get_users(target_id)
    except PeerIdInvalid:
        await cb.answer("User not found!", show_alert=True)
        return

    collection_data = await delete_user_collection(target_id)
    if not collection_data:
        await cb.answer("User has no collection!", show_alert=True)
        return

    await send_collection_data(admin_user, target_user, collection_data)
    await log_action("Collection Deleted", admin_user, target_user, f"{len(collection_data)} items")
    await cb.message.edit_text(f"✅ Collection cleared for {target_user.mention}!")

@app.on_callback_query(filters.regex(r"^clean_wallet_(\d+)$"))
@capture_and_handle_error
async def reset_wallet_callback(c: Client, cb: CallbackQuery):
    if not await is_user_og(cb.from_user.id):
        await cb.answer("Nikal Lawde !!", show_alert=True)
        return

    target_id = int(cb.matches[0].group(1))
    admin_user = cb.from_user
    target_user = await app.get_users(target_id)

    previous_balance = await get_user_info(target_user)["wallet_balance"]
    await reset_user_balance(target_id)
    
    await log_action("Wallet Reset", admin_user, target_user, f"From {previous_balance} to 0")
    await cb.message.edit_text("Wallet balance reset to 0!")

@app.on_callback_query(filters.regex(r"^clear_bank_(\d+)$"))
@capture_and_handle_error
async def clear_bank_callback(c: Client, cb: CallbackQuery):
    if not await is_user_og(cb.from_user.id):
        await cb.answer("Nikal Lawde !!", show_alert=True)
        return

    target_id = int(cb.matches[0].group(1))
    admin_user = cb.from_user
    target_user = await app.get_users(target_id)

    previous_balance = await get_user_info(target_user)["bank_balance"]
    await withdraw_from_bank(target_id, amount=previous_balance)
    
    await log_action("Bank Cleared", admin_user, target_user, f"From {previous_balance} to 0")
    await cb.message.edit_text("Bank balance cleared!")

@app.on_callback_query(filters.regex(r"^full_reset_(\d+)$"))
@capture_and_handle_error
async def full_reset_callback(c: Client, cb: CallbackQuery):
    if not await is_user_og(cb.from_user.id):
        await cb.answer("Access Denied!", show_alert=True)
        return

    target_id = int(cb.matches[0].group(1))
    admin_user = cb.from_user
    
    try:
        target_user = await app.get_users(target_id)
    except PeerIdInvalid:
        await cb.answer("User not found!", show_alert=True)
        return

    # Get user info before reset
    user_info = await get_user_info(target_user)
    wallet_balance = user_info["wallet_balance"]
    bank_balance = user_info["bank_balance"]
    
    # Get collection data for logging
    collection_data = await delete_user_collection(target_id)
    if collection_data:
        await send_collection_data(admin_user, target_user, collection_data)

    # Execute all reset operations
    await asyncio.gather(
        reset_user_balance(target_id),
        withdraw_from_bank(target_id, bank_balance)
    )
    
    await log_action("Full Account Reset", admin_user, target_user, 
                    f"Wallet: {wallet_balance} → 0, Bank: {bank_balance} → 0")
    
    await cb.message.edit_text(f"✅ Full reset complete for {target_user.mention}!")
    
    
async def send_collection_data(admin_user: User, target_user: User, collection_data: list):
    try:
        chunk_size = 200
        chunks = [collection_data[i:i+chunk_size] for i in range(0, len(collection_data), chunk_size)]
        for i, chunk in enumerate(chunks):
            await app.send_message(
                OWNER_ID,
                f"⚠️ Collection Data (Part {i+1}/{len(chunks)})\n"
                f"Admin: {admin_user.mention}\n"
                f"User: {target_user.mention} ({target_user.id})\n"
                f"IDs:\n{' '.join(chunk)}"
            )
    except Exception as e:
        await app.send_message(OWNER_ID, f"⚠️ Error sending collection data: {str(e)}")

@app.on_message(Command("resetwallet") & og_filter)
@capture_and_handle_error
async def manual_reset_wallet(c: Client, m: Message):
    try:
        if not m.command or len(m.command) < 2:
            return await m.reply("❌ Please provide a user ID.\nUsage: /resetwallet <user_id>")
        
        target_id = int(m.command[1])
        admin_user = m.from_user
        
        try:
            target_user = await app.get_users(target_id)
        except PeerIdInvalid:
            return await m.reply("❌ User not found!")

        # Force drop wallet collection for user
        await db.GrabToken.delete_many({"user_id": target_id})
        
        await log_action("Force Wallet Reset", admin_user, target_user, "Wallet collection dropped")
        await m.reply(f"✅ Wallet collection force dropped for {target_user.mention}!")
    except ValueError:
        await m.reply("❌ Invalid user ID format!")
    except Exception as e:
        await m.reply(f"❌ Error: {str(e)}")

@app.on_message(Command("resetcollection") & og_filter)
@capture_and_handle_error
async def manual_reset_collection(c: Client, m: Message):
    try:
        if not m.command or len(m.command) < 2:
            return await m.reply("❌ Please provide a user ID.\nUsage: /resetcollection <user_id>")
        
        target_id = int(m.command[1])
        admin_user = m.from_user
        
        try:
            target_user = await app.get_users(target_id)
        except PeerIdInvalid:
            return await m.reply("❌ User not found!")

        # Force drop collection for user
        await db.Collection.delete_many({"user_id": target_id})
        
        await log_action("Force Collection Reset", admin_user, target_user, "Collection dropped")
        await m.reply(f"✅ Collection force dropped for {target_user.mention}!")
    except ValueError:
        await m.reply("❌ Invalid user ID format!")
    except Exception as e:
        await m.reply(f"❌ Error: {str(e)}")

@app.on_message(Command("resetbank") & og_filter)
@capture_and_handle_error
async def manual_reset_bank(c: Client, m: Message):
    try:
        if not m.command or len(m.command) < 2:
            return await m.reply("❌ Please provide a user ID.\nUsage: /resetbank <user_id>")
        
        target_id = int(m.command[1])
        admin_user = m.from_user
        
        try:
            target_user = await app.get_users(target_id)
        except PeerIdInvalid:
            return await m.reply("❌ User not found!")

        # Force drop bank collection for user
        await db.Bank.delete_many({"user_id": target_id})
        
        await log_action("Force Bank Reset", admin_user, target_user, "Bank collection dropped")
        await m.reply(f"✅ Bank collection force dropped for {target_user.mention}!")
    except ValueError:
        await m.reply("❌ Invalid user ID format!")
    except Exception as e:
        await m.reply(f"❌ Error: {str(e)}")

@app.on_message(Command("fullreset") & og_filter)
@capture_and_handle_error
async def manual_full_reset(c: Client, m: Message):
    try:
        if not m.command or len(m.command) < 2:
            return await m.reply("❌ Please provide a user ID.\nUsage: /fullreset <user_id>")
        
        target_id = int(m.command[1])
        admin_user = m.from_user
        
        try:
            target_user = await app.get_users(target_id)
        except PeerIdInvalid:
            return await m.reply("❌ User not found!")

        # Force drop all collections for user
        await asyncio.gather(
            db.GrabToken.delete_many({"user_id": target_id}),
            db.Bank.delete_many({"user_id": target_id}),
            db.Collection.delete_many({"user_id": target_id})
        )
        
        await log_action("Force Full Reset", admin_user, target_user, "All collections dropped")
        await m.reply(f"✅ All collections force dropped for {target_user.mention}!")
    except ValueError:
        await m.reply("❌ Invalid user ID format!")
    except Exception as e:
        await m.reply(f"❌ Error: {str(e)}")