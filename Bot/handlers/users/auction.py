from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, InputMediaPhoto
from Bot import app, Command, llog as glog
from Bot.database.auctiondb import auction_house
from Bot.database.characterdb import get_character_details
from Bot.database.grabtokendb import get_user_balance
from Bot.utils import admin_filter
from datetime import datetime, timedelta
import asyncio
from typing import DefaultDict
from Bot.config import SUPPORT_CHAT_ID
from Bot.errors import capture_and_handle_error
from Bot.utils import warned_user_filter , command_filter
from texts import WAIFU , ANIME


active_locks = DefaultDict(asyncio.Lock)

# Helper function to format time remaining
async def format_time_remaining(end_time):
    """Format the time remaining for an auction in a human-readable format"""
    now = datetime.utcnow()
    if end_time < now:
        return "Ended"
    
    time_left = end_time - now
    days, seconds = time_left.days, time_left.seconds
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    seconds = seconds % 60
    
    if days > 0:
        return f"{days}d {hours}h {minutes}m"
    elif hours > 0:
        return f"{hours}h {minutes}m {seconds}s"
    elif minutes > 0:
        return f"{minutes}m {seconds}s"
    else:
        return f"{seconds}s"

# Command to create a new auction - restricted to admins only
@app.on_message(Command("auction") & filters.private & admin_filter)
@capture_and_handle_error
@warned_user_filter
async def create_auction(client: Client, message: Message):
    user_id = message.from_user.id
    
    # Ask for player ID
    try:
        player_msg = await client.ask(
            chat_id=message.chat.id,
            text=f"Please send the {WAIFU} ID you want to auction:",
            user_id=user_id,
            filters=filters.text,
            timeout=300
        )
        
        player_id = player_msg.text.strip()
        
        # Verify ownership and get character details
        char_data = await get_character_details(player_id)
        if not char_data:
            await message.reply(f"Invalid {WAIFU} ID.")
            return
            
        # Check if it's a video waifu
        if char_data.get("is_video", False):
            await message.reply(f"⚠️ Video {WAIFU}s cannot be placed in auctions!")
            return
        
        # Check if this player is already in an active auction
        existing_auctions = await auction_house.search_auctions(player_id=player_id)
        if existing_auctions:
            await message.reply(f"⚠️ This {WAIFU} is already in an active auction! Cannot create duplicate auction.")
            return
        
        # Ask for starting price
        price_msg = await client.ask(
            chat_id=message.chat.id,
            text="Set your starting price in GRABTOKENS:",
            user_id=user_id,
            filters=filters.text,
            timeout=300
        )
        
        try:
            starting_price = int(price_msg.text)
            if starting_price < 0:
                await message.reply("Price should be positive")
                return
        except ValueError:
            await message.reply("Invalid price format. Please use whole numbers only.")
            return
        
        # Ask for auction duration
        duration_msg = await client.ask(
            chat_id=message.chat.id,
            text="Set auction duration in hours (6-72):",
            user_id=user_id,
            filters=filters.text,
            timeout=300
        )
        
        try:
            duration_hours = int(duration_msg.text)
            if duration_hours < 6 or duration_hours > 72:
                await message.reply("Duration must be between 6 and 72 hours.")
                return
        except ValueError:
            await message.reply("Invalid duration format. Please use whole numbers only.")
            return
        
        # Ask for reserve price (optional)
        reserve_msg = await client.ask(
            chat_id=message.chat.id,
            text="Set a reserve price (minimum price that must be met) or type 'skip' to skip:",
            user_id=user_id,
            filters=filters.text,
            timeout=300
        )
        
        reserve_price = None
        if reserve_msg.text.lower() != "skip":
            try:
                reserve_price = int(reserve_msg.text)
                if reserve_price < starting_price:
                    await message.reply("Reserve price cannot be lower than starting price.")
                    return
            except ValueError:
                await message.reply("Invalid price format. Using no reserve price.")
        
        # Create confirmation message
        end_time = datetime.utcnow() + timedelta(hours=duration_hours)
        end_time_str = end_time.strftime("%Y-%m-%d %H:%M UTC")
        
        caption = (
            f"**Name:** {char_data['name']}\n"
            f"{char_data['rarity_sign']} **Rarity:** {char_data['rarity']}\n"
            f"**{ANIME}:** {char_data['anime']}\n"
            f"**Starting Price:** {starting_price} GRABTOKENS\n"
            f"**Duration:** {duration_hours} hours (Ends: {end_time_str})\n"
        )
        
        if reserve_price:
            caption += f"**Reserve Price:** {reserve_price} GRABTOKENS\n"
        
        caption += f"\nAre you sure you want to auction this {WAIFU}?"
        
        markup = InlineKeyboardMarkup([
            [InlineKeyboardButton(
                "✅ Confirm", 
                callback_data=f"confirm_auction:{player_id}:{starting_price}:{duration_hours}:{reserve_price or 0}"
            )],
            [InlineKeyboardButton("❌ Cancel", callback_data="cancel_auction")]
        ])
        
        await message.reply_photo(
            photo=char_data["img_url"],
            caption=caption,
            reply_markup=markup
        )
        
    except asyncio.TimeoutError:
        await message.reply("Auction creation timed out. Please try again.")

# Auction confirmation handler
@app.on_callback_query(filters.regex(r"^confirm_auction:|^cancel_auction"))
@capture_and_handle_error
async def handle_auction_confirmation(client: Client, query: CallbackQuery):
    user_id = query.from_user.id
    
    # Verify admin status
    if not await auction_house._is_admin(user_id):
        await query.answer("Only administrators can create auctions!", show_alert=True)
        return
    
    if query.data == "cancel_auction":
        await query.message.edit_caption("Auction creation cancelled.")
        await query.answer("Auction cancelled!")
        return
    
    # Parse callback data
    parts = query.data.split(":")
    player_id = parts[1]
    starting_price = int(parts[2])
    duration_hours = int(parts[3])
    reserve_price = int(parts[4])
    if reserve_price == 0:
        reserve_price = None
    
    # Double-check if this player is already in an active auction
    existing_auctions = await auction_house.search_auctions(player_id=player_id)
    if existing_auctions:
        await query.message.edit_caption(f"⚠️ This {WAIFU} is already in an active auction! Cannot create duplicate auction.")
        await query.answer("Duplicate auction prevented!", show_alert=True)
        return
    
    async with active_locks[f"auction_{user_id}"]:
        # Create the auction
        auction_id = await auction_house.create_auction(
            seller_id=user_id,
            player_id=player_id,
            starting_price=starting_price,
            duration_hours=duration_hours,
            min_bid_increment=1000,  # Default increment
            reserve_price=reserve_price,
            seller_name=query.from_user.username
        )
        
        if auction_id:
            end_time = datetime.utcnow() + timedelta(hours=duration_hours)
            end_time_str = end_time.strftime("%Y-%m-%d %H:%M UTC")
            
            success_caption = (
                f"✅ Auction created successfully!\n\n"
                f"**Auction ID:** `{auction_id}`\n"
                f"**Starting Price:** {starting_price} GRABTOKENS\n"
                f"**Ends at:** {end_time_str}\n\n"
                f"Users can bid using:\n/bid {auction_id} [amount]"
            )
            
            await query.message.edit_caption(success_caption)
            await query.answer("Auction created!")
            
            # Send notification to support chat
            char_data = await get_character_details(player_id)
            
            # Create notification message
            notification_caption = (
                f"🔥 **NEW AUCTION ALERT** 🔥\n\n"
                f"**Name:** {char_data['name']}\n"
                f"{char_data['rarity_sign']} **Rarity:** {char_data['rarity']}\n"
                f"**{ANIME}:** {char_data['anime']}\n"
                f"**Starting Price:** {starting_price} GRABTOKENS\n"
                f"**Duration:** {duration_hours} hours (Ends: {end_time_str})\n"
                f"**Auction ID:** `{auction_id}`\n\n"
                f"Use /bid {auction_id} [amount] to place a bid!"
            )
            
            try:
                # Send to support chat
                x = await client.send_photo(
                    chat_id=SUPPORT_CHAT_ID,
                    photo=char_data["img_url"],
                    caption=notification_caption
                )
                await x.pin()
                # Also log to global log
                await glog(f"New auction created by {query.from_user.mention} for {char_data['name']} (ID: {player_id})")
            except Exception as e:
                # Log error but don't fail the auction creation
                print(f"Failed to send auction notification: {e}")
        else:
            await query.message.edit_caption(
                f"❌ Failed to create auction. Make sure you own this {WAIFU}."
            )
            await query.answer("Failed to create auction!", show_alert=True)

# Command to view auctions
@app.on_message(Command("auctions") & filters.private & command_filter)
@capture_and_handle_error
@warned_user_filter
async def view_auctions(client: Client, message: Message, page: int = 1):
    per_page = 8
    auctions, total = await auction_house.get_active_auctions(page, per_page)
    
    if not auctions:
        await message.reply("No active auctions found!")
        return
    
    buttons = []
    for auction in auctions:
        char_data = auction.get("player_details", {})
        name = char_data.get("name", "Unknown Player")
        current_price = auction["current_price"]
        time_left = await format_time_remaining(auction["ends_at"])
        
        btn_text = f"{name} - {current_price} GT - {time_left}"
        buttons.append([
            InlineKeyboardButton(btn_text, callback_data=f"view_auction_{auction['_id']}")
        ])
    
    # Pagination controls
    pagination = []
    if page > 1:
        pagination.append(InlineKeyboardButton("⬅️ Previous", callback_data=f"auctions_{page-1}"))
    if total > page * per_page:
        pagination.append(InlineKeyboardButton("Next ➡️", callback_data=f"auctions_{page+1}"))
    
    if pagination:
        buttons.append(pagination)
    
    await message.reply(
        f"**Active Auctions** (Page {page}/{(total + per_page - 1) // per_page})",
        reply_markup=InlineKeyboardMarkup(buttons)
    )

# Auction pagination handler
@app.on_callback_query(filters.regex(r"^auctions_(\d+)"))
@capture_and_handle_error
async def handle_auctions_pagination(client: Client, query: CallbackQuery):
    page = int(query.matches[0].group(1))
    await view_auctions(client, query.message, page)
    await query.answer()

# View auction details
@app.on_callback_query(filters.regex(r"^view_auction_(.+)"))
@capture_and_handle_error
async def view_auction_details(client: Client, query: CallbackQuery):
    auction_id = query.matches[0].group(1)
    auction = await auction_house.get_auction(auction_id)
    
    if not auction:
        await query.answer("Auction not found or has ended!", show_alert=True)
        return
    
    char_data = auction.get("player_details", {})
    
    # Format time remaining
    time_left = await format_time_remaining(auction["ends_at"])
    
    # Format bid history
    bids = auction.get("bids", [])
    bid_history = ""
    if bids:
        # Show last 3 bids
        for bid in bids[-3:]:
            bidder = bid.get("bidder_name", f"User {bid['bidder_id']}")
            bid_history += f"• {bidder}: {bid['amount']} GT\n"
    else:
        bid_history = "No bids yet"
    
    caption = (
        f"**Name:** {char_data.get('name', 'Unknown')}\n"
        f"{char_data.get('rarity_sign', '')} **Rarity:** {char_data.get('rarity', 'Unknown')}\n"
        f"**{ANIME}:** {char_data.get('anime', 'Unknown')}\n\n"
        f"**Current Price:** {auction['current_price']} GRABTOKENS\n"
        f"**Time Remaining:** {time_left}\n"
        f"**Minimum Bid:** {auction['current_price'] + auction['min_bid_increment']} GRABTOKENS\n\n"
        f"**Recent Bids:**\n{bid_history}"
    )
    
    # Add reserve price info if set
    if auction.get("reserve_price"):
        if auction["current_price"] >= auction["reserve_price"]:
            caption += f"\n**Reserve Price:** ✅ Met"
        else:
            caption += f"\n**Reserve Price:** ❌ Not met yet"
    
    # Create buttons
    buttons = [
        [InlineKeyboardButton("🔄 Refresh", callback_data=f"view_auction_{auction_id}")],
        [InlineKeyboardButton("💰 Place Bid", callback_data=f"place_bid_{auction_id}")],
        [InlineKeyboardButton("⬅️ Back to Auctions", callback_data="auctions_1")]
    ]
    
    # Show image if available
    if char_data.get("img_url"):
        await query.message.edit_media(
            InputMediaPhoto(
                char_data["img_url"],
                caption=caption
            ),
            reply_markup=InlineKeyboardMarkup(buttons)
        )
    else:
        await query.message.edit_text(
            caption,
            reply_markup=InlineKeyboardMarkup(buttons)
        )
    
    await query.answer()

# Place bid handler
@app.on_callback_query(filters.regex(r"^place_bid_(.+)"))
@capture_and_handle_error
async def handle_place_bid(client: Client, query: CallbackQuery):
    user_id = query.from_user.id
    auction_id = query.matches[0].group(1)
    
    # Get auction details
    auction = await auction_house.get_auction(auction_id)
    if not auction:
        await query.answer("Auction not found or has ended!", show_alert=True)
        return
    
    # Check if user is the seller
    if auction["seller_id"] == user_id:
        await query.answer("You cannot bid on your own auction!", show_alert=True)
        return
    
    # Check if user is an admin (additional check to prevent token leakage)
    if await auction_house._is_admin(user_id) and await auction_house._is_admin(auction["seller_id"]):
        await query.answer("Admins cannot bid on other admin auctions to prevent token leakage!", show_alert=True)
        return
    
    # Check if auction is still active
    if auction["status"] != "active" or datetime.utcnow() > auction["ends_at"]:
        await query.answer("This auction has ended!", show_alert=True)
        return
    
    min_bid = auction["current_price"] + auction["min_bid_increment"]
    
    # Ask for bid amount
    await query.answer("Enter your bid amount")
    
    try:
        bid_msg = await client.ask(
            chat_id=query.message.chat.id,
            text=f"Current price: {auction['current_price']} GRABTOKENS\n"
                 f"Minimum bid: {min_bid} GRABTOKENS\n\n"
                 f"Enter your bid amount:",
            user_id=user_id,
            filters=filters.text,
            timeout=120
        )
        
        try:
            bid_amount = int(bid_msg.text)
            
            # Check if bid is high enough
            if bid_amount < min_bid:
                await query.message.reply(f"Bid must be at least {min_bid} GRABTOKENS!")
                return
            
            # Check if user has enough balance
            user_balance = await get_user_balance(user_id)
            if user_balance < bid_amount:
                await query.message.reply(
                    f"Insufficient balance! You have {user_balance} GRABTOKENS."
                )
                return
            
            # Confirm bid
            confirm_markup = InlineKeyboardMarkup([
                [InlineKeyboardButton("✅ Confirm Bid", callback_data=f"confirm_bid_{auction_id}_{bid_amount}")],
                [InlineKeyboardButton("❌ Cancel", callback_data=f"view_auction_{auction_id}")]
            ])
            
            await query.message.reply(
                f"You are about to bid {bid_amount} GRABTOKENS on this auction.\n"
                f"This amount will be held until you are outbid or the auction ends.\n\n"
                f"Are you sure?",
                reply_markup=confirm_markup
            )
            
        except ValueError:
            await query.message.reply("Invalid bid amount. Please enter a number.")
            
    except asyncio.TimeoutError:
        await query.message.reply("Bid process timed out. Please try again.")

# Confirm bid handler
@app.on_callback_query(filters.regex(r"^confirm_bid_(.+)_(\d+)"))
@capture_and_handle_error
async def confirm_bid(client: Client, query: CallbackQuery):
    user_id = query.from_user.id
    auction_id, bid_amount = query.matches[0].groups()
    bid_amount = int(bid_amount)
    
    # Get auction details for additional checks
    auction = await auction_house.get_auction(auction_id)
    if not auction:
        await query.answer("Auction not found or has ended!", show_alert=True)
        return
    
    # Check if user is the seller (double-check)
    if auction["seller_id"] == user_id:
        await query.answer("You cannot bid on your own auction!", show_alert=True)
        return
    
    # Check if user is an admin (additional check to prevent token leakage)
    if await auction_house._is_admin(user_id) and await auction_house._is_admin(auction["seller_id"]):
        await query.answer("Admins cannot bid on other admin auctions to prevent token leakage!", show_alert=True)
        return
    
    async with active_locks[f"bid_{auction_id}"]:
        result = await auction_house.place_bid(
            auction_id=auction_id,
            bidder_id=user_id,
            bid_amount=bid_amount,
            bidder_name=query.from_user.username
        )
        
        if result["success"]:
            await query.message.edit_text(
                f"✅ Bid placed successfully!\n"
                f"You are now the highest bidder at {bid_amount} GRABTOKENS.\n\n"
                f"View the auction with /auctions"
            )
            await query.answer("Bid placed!")
            
            # Notify support chat about high bids (optional)
            if bid_amount >= 1000000:  # For bids over 1M tokens
                char_data = auction.get("player_details", {})
                await glog(
                    f"🔥 High bid alert! {query.from_user.mention} bid {bid_amount} GRABTOKENS on "
                    f"{char_data.get('name', 'Unknown Player')} (Auction ID: {auction_id})"
                )
        else:
            await query.message.edit_text(
                f"❌ Failed to place bid: {result['message']}"
            )
            await query.answer("Bid failed!", show_alert=True)

# Command to bid directly
@app.on_message(Command("bid") & command_filter)
@capture_and_handle_error
@warned_user_filter
async def bid_command(client: Client, message: Message):
    user_id = message.from_user.id
    args = message.text.split()
    
    if len(args) != 3:
        await message.reply(
            "Usage: /bid [auction_id] [amount]\n"
            "Example: /bid 5f7b1a2b3c4d5e6f7a8b9c0d 50000"
        )
        return
    
    auction_id = args[1]
    try:
        bid_amount = int(args[2])
    except ValueError:
        await message.reply("Invalid bid amount. Please enter a number.")
        return
    
    # Get auction details
    auction = await auction_house.get_auction(auction_id)
    if not auction:
        await message.reply("Auction not found or has ended!")
        return
    
    # Check if user is the seller
    if auction["seller_id"] == user_id:
        await message.reply("You cannot bid on your own auction!")
        return
    
    # Check if user is an admin (additional check to prevent token leakage)
    if await auction_house._is_admin(user_id) and await auction_house._is_admin(auction["seller_id"]):
        await message.reply("Admins cannot bid on other admin auctions to prevent token leakage!")
        return
    
    # Check if auction is still active
    if auction["status"] != "active" or datetime.utcnow() > auction["ends_at"]:
        await message.reply("This auction has ended!")
        return
    
    min_bid = auction["current_price"] + auction["min_bid_increment"]
    
    # Check if bid is high enough
    if bid_amount < min_bid:
        await message.reply(f"Bid must be at least {min_bid} GRABTOKENS!")
        return
    
    # Check if user has enough balance
    user_balance = await get_user_balance(user_id)
    if user_balance < bid_amount:
        await message.reply(
            f"Insufficient balance! You have {user_balance} GRABTOKENS."
        )
        return
    
    # Place bid
    async with active_locks[f"bid_{auction_id}"]:
        result = await auction_house.place_bid(
            auction_id=auction_id,
            bidder_id=user_id,
            bid_amount=bid_amount,
            bidder_name=message.from_user.username
        )
        
        if result["success"]:
            await message.reply(
                f"✅ Bid placed successfully!\n"
                f"You are now the highest bidder at {bid_amount} GRABTOKENS."
            )
            
            # Notify support chat about high bids (optional)
            if bid_amount >= 1000000:  # For bids over 1M tokens
                char_data = auction.get("player_details", {})
                await app.send_message(
                    SUPPORT_CHAT_ID,
                    f"🔥 High bid alert! {message.from_user.mention} bid {bid_amount} GRABTOKENS on "
                    f"{char_data.get('name', 'Unknown Player')} (Auction ID: {auction_id})"
                )
        else:
            await message.reply(f"❌ Failed to place bid: {result['message']}")

# Command to view your auctions
@app.on_message(Command("myauctions") & filters.private & command_filter)
@capture_and_handle_error
@warned_user_filter
async def my_auctions(client: Client, message: Message):
    user_id = message.from_user.id
    
    # Get user's active auctions
    auctions = await auction_house.get_user_auctions(user_id, "active")
    
    if not auctions:
        await message.reply("You don't have any active auctions!")
        return
    
    buttons = []
    for auction in auctions:
        char_data = auction.get("player_details", {})
        name = char_data.get("name", "Unknown Player")
        current_price = auction["current_price"]
        time_left = await format_time_remaining(auction["ends_at"])
        
        btn_text = f"{name} - {current_price} GT - {time_left}"
        buttons.append([
            InlineKeyboardButton(btn_text, callback_data=f"my_auction_{auction['_id']}")
        ])
    
    await message.reply(
        "**Your Active Auctions:**",
        reply_markup=InlineKeyboardMarkup(buttons)
    )

# View my auction details
@app.on_callback_query(filters.regex(r"^my_auction_(.+)"))
@capture_and_handle_error
async def view_my_auction(client: Client, query: CallbackQuery):
    user_id = query.from_user.id
    auction_id = query.matches[0].group(1)
    
    auction = await auction_house.get_auction(auction_id)
    if not auction:
        await query.answer("Auction not found or has ended!", show_alert=True)
        return
    
    # Verify ownership
    if auction["seller_id"] != user_id:
        await query.answer("This is not your auction!", show_alert=True)
        return
    
    char_data = auction.get("player_details", {})
    
    # Format time remaining
    time_left = await format_time_remaining(auction["ends_at"])
    
    # Format bid history
    bids = auction.get("bids", [])
    bid_history = ""
    if bids:
        # Show last 5 bids
        for bid in bids[-5:]:
            bidder = bid.get("bidder_name", f"User {bid['bidder_id']}")
            bid_history += f"• {bidder}: {bid['amount']} GT\n"
    else:
        bid_history = "No bids yet"
    
    caption = (
        f"**Your Auction**\n\n"
        f"**Name:** {char_data.get('name', 'Unknown')}\n"
        f"{char_data.get('rarity_sign', '')} **Rarity:** {char_data.get('rarity', 'Unknown')}\n"
        f"**Current Price:** {auction['current_price']} GRABTOKENS\n"
        f"**Time Remaining:** {time_left}\n\n"
        f"**Bid History:**\n{bid_history}"
    )
    
    # Add reserve price info if set
    if auction.get("reserve_price"):
        if auction["current_price"] >= auction["reserve_price"]:
            caption += f"\n**Reserve Price ({auction['reserve_price']} GT):** ✅ Met"
        else:
            caption += f"\n**Reserve Price ({auction['reserve_price']} GT):** ❌ Not met yet"
    
    # Create buttons
    buttons = [
        [InlineKeyboardButton("🔄 Refresh", callback_data=f"my_auction_{auction_id}")],
        [InlineKeyboardButton("❌ Cancel Auction", callback_data=f"cancel_auction_{auction_id}")],
        [InlineKeyboardButton("⬅️ Back to My Auctions", callback_data="back_to_myauctions")]
    ]
    
    # Show image if available
    if char_data.get("img_url"):
        await query.message.edit_media(
            InputMediaPhoto(
                char_data["img_url"],
                caption=caption
            ),
            reply_markup=InlineKeyboardMarkup(buttons)
        )
    else:
        await query.message.edit_text(
            caption,
            reply_markup=InlineKeyboardMarkup(buttons)
        )
    
    await query.answer()

# Back to my auctions handler
@app.on_callback_query(filters.regex(r"^back_to_myauctions"))
@capture_and_handle_error
async def back_to_myauctions(client: Client, query: CallbackQuery):
    await my_auctions(client, query.message)
    await query.answer()

# Cancel auction handler
@app.on_callback_query(filters.regex(r"^cancel_auction_(.+)"))
@capture_and_handle_error
async def cancel_auction(client: Client, query: CallbackQuery):
    user_id = query.from_user.id
    auction_id = query.matches[0].group(1)
    
    # Confirm cancellation
    confirm_markup = InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Yes, Cancel", callback_data=f"confirm_cancel_{auction_id}")],
        [InlineKeyboardButton("❌ No, Keep Active", callback_data=f"my_auction_{auction_id}")]
    ])
    
    await query.message.edit_caption(
        query.message.caption + "\n\n⚠️ Are you sure you want to cancel this auction? "
        "If there are bids, they will be refunded and the player will be returned to you."
    )
    await query.message.edit_reply_markup(confirm_markup)
    await query.answer()

# Confirm cancel auction handler
@app.on_callback_query(filters.regex(r"^confirm_cancel_(.+)"))
@capture_and_handle_error
async def confirm_cancel_auction(client: Client, query: CallbackQuery):
    user_id = query.from_user.id
    auction_id = query.matches[0].group(1)
    
    async with active_locks[f"cancel_{auction_id}"]:
        result = await auction_house.cancel_auction(auction_id, user_id)
        
        if result["success"]:
            await query.message.edit_caption(
                "✅ Auction cancelled successfully! The player has been returned to your collection."
            )
            await query.message.edit_reply_markup(None)
            await query.answer("Auction cancelled!")
        else:
            await query.message.edit_caption(
                f"❌ Failed to cancel auction: {result['message']}"
            )
            await query.message.edit_reply_markup(None)
            await query.answer("Failed to cancel auction!", show_alert=True)

# Command to view your bids
@app.on_message(Command("mybids") & filters.private & command_filter)
@capture_and_handle_error
@warned_user_filter
async def my_bids(client: Client, message: Message):
    user_id = message.from_user.id
    
    # Get auctions where user has placed bids
    auctions = await auction_house.get_user_bids(user_id)
    
    if not auctions:
        await message.reply("You don't have any active bids!")
        return
    
    # Filter to only active auctions
    active_auctions = [a for a in auctions if a["status"] == "active"]
    
    if not active_auctions:
        await message.reply("You don't have any active bids on ongoing auctions!")
        return
    
    buttons = []
    for auction in active_auctions:
        char_data = auction.get("player_details", {})
        name = char_data.get("name", "Unknown Player")
        
        # Get user's highest bid
        user_bids = auction.get("user_bids", [])
        if user_bids:
            highest_bid = max(bid["amount"] for bid in user_bids)
            is_winning = auction["highest_bidder"] == user_id
            status = "🏆 Winning" if is_winning else "❌ Outbid"
        else:
            highest_bid = 0
            status = "Unknown"
        
        time_left = await format_time_remaining(auction["ends_at"])
        
        btn_text = f"{name} - {highest_bid} GT - {status} - {time_left}"
        buttons.append([
            InlineKeyboardButton(btn_text, callback_data=f"view_auction_{auction['_id']}")
        ])
    
    await message.reply(
        "**Your Active Bids:**",
        reply_markup=InlineKeyboardMarkup(buttons)
    )

# Admin command to process expired auctions
@app.on_message(Command("process_auctions") & admin_filter)
@capture_and_handle_error
async def process_auctions_command(client: Client, message: Message):
    status_msg = await message.reply("Processing expired auctions...")
    
    count = await auction_house.process_expired_auctions()
    
    await status_msg.edit_text(f"✅ Processed {count} expired auctions!")
    
    # Log to support chat
    if count > 0:
        await glog(f"Admin {message.from_user.mention} processed {count} expired auctions")

# Admin command to view auction history
@app.on_message(Command("auction_history") & admin_filter)
@capture_and_handle_error
async def auction_history(client: Client, message: Message):
    args = message.text.split()
    player_id = None
    
    if len(args) > 1:
        player_id = args[1]
    
    auctions = await auction_house.get_auction_history(player_id)
    
    if not auctions:
        await message.reply("No completed auctions found!")
        return
    
    # Format response
    response = "**Auction History:**\n\n"
    
    for auction in auctions[:10]:  # Limit to 10 most recent
        char_data = auction.get("player_details", {})
        name = char_data.get("name", "Unknown Player")
        rarity = char_data.get("rarity", "Unknown")
        final_price = auction["current_price"]
        end_time = auction["ends_at"].strftime("%Y-%m-%d")
        
        response += (
            f"**{name}** ({rarity})\n"
            f"Final Price: {final_price} GT\n"
            f"Completed: {end_time}\n\n"
        )
    
    await message.reply(response)


async def process_expired_auctions_task():
    """Task to be scheduled to process expired auctions"""
    await auction_house.process_expired_auctions()





# Command to check auction details in both private and group chats
@app.on_message(Command("aucinfo") & command_filter)
@capture_and_handle_error
@warned_user_filter
async def auction_info_command(client: Client, message: Message):
    args = message.text.split()
    
    if len(args) != 2:
        await message.reply(
            "Usage: /aucinfo [auction_id]\n"
            "Example: /aucinfo 5f7b1a2b3c4d5e6f7a8b9c0d"
        )
        return
    
    auction_id = args[1]
    
    # Get auction details
    auction = await auction_house.get_auction(auction_id)
    if not auction:
        await message.reply("Auction not found or has ended!")
        return
    
    # Get player details
    char_data = auction.get("player_details", {})
    
    # Format time remaining
    time_left = await format_time_remaining(auction["ends_at"])
    
    # Format bid history
    bids = auction.get("bids", [])
    bid_history = ""
    if bids:
        # Show last 3 bids
        for bid in bids[-3:]:
            bidder = bid.get("bidder_name", f"User {bid['bidder_id']}")
            bid_history += f"• {bidder}: {bid['amount']} GT\n"
    else:
        bid_history = "No bids yet"
    
    # Get seller info
    seller_name = auction.get("seller_name", f"User {auction['seller_id']}")
    
    # Create detailed auction info
    caption = (
        f"🔍 **Auction Details** 🔍\n\n"
        f"**Name:** {char_data.get('name', 'Unknown')}\n"
        f"{char_data.get('rarity_sign', '')} **Rarity:** {char_data.get('rarity', 'Unknown')}\n"
        f"**{ANIME}:** {char_data.get('anime', 'Unknown')}\n\n"
        f"**Current Price:** {auction['current_price']} GRABTOKENS\n"
        f"**Starting Price:** {auction['starting_price']} GRABTOKENS\n"
        f"**Time Remaining:** {time_left}\n"
        f"**Minimum Bid:** {auction['current_price'] + auction['min_bid_increment']} GRABTOKENS\n"
        f"**Seller:** {seller_name}\n\n"
        f"**Recent Bids:**\n{bid_history}"
    )
    
    # Add reserve price info if set
    if auction.get("reserve_price"):
        if auction["current_price"] >= auction["reserve_price"]:
            caption += f"\n**Reserve Price:** ✅ Met"
        else:
            caption += f"\n**Reserve Price:** ❌ Not met yet"
    
    # Add bid instructions
    caption += f"\n\nTo place a bid, use:\n`/bid {auction_id} [amount]`"
    
    
    if char_data.get("img_url"):
        await message.reply_photo(
            photo=char_data["img_url"],
            caption=caption
        )
    else:
        await message.reply(
            caption
        )

@app.on_message(Command("achelp") & command_filter)
@capture_and_handle_error
@warned_user_filter
async def auction_help_command(client: Client, message: Message):
    """Provide detailed help information about auction commands"""
    help_text = (
        "🔰 **Auction System Help** 🔰\n\n"
        "**For All Users:**\n"
        "• `/auctions` - View all active auctions\n"
        "• `/bid [auction_id] [amount]` - Place a bid on an auction\n"
        "• `/mybids` - View your active bids\n"
        "• `/myauctions` - View auctions you've created\n"
        "• `/aucinfo [auction_id]` - Get detailed information about a specific auction\n\n"
        
        "**Bidding Rules:**\n"
        "• Your bid must be higher than the current price plus minimum increment\n"
        "• You must have enough GRABTOKENS in your balance\n"
        "• You cannot bid on your own auctions\n"
        "• Some auctions may have a reserve price that must be met for the sale to complete\n\n"
        
        "**For Auction Creators:**\n"
        "• You can cancel your auction if there are no bids yet\n"
        "• When an auction ends, the highest bidder gets the player and you receive the GRABTOKENS\n\n"
        
        "**For Admins:**\n"
        "• `/auction` - Create a new auction (admin only)\n"
        "• `/process_auctions` - Process all expired auctions (admin only)\n"
        "• `/auction_history` - View auction history (admin only)\n\n"
        
        "Need more help? Contact support in our official group!"
    )
    
    await message.reply(help_text)


