from Bot import app , Command
from Bot.database import db 
from Bot.database.characterdb import get_character_details
from bson.objectid import ObjectId
from pyrogram import Client, filters
from pyrogram.types import (
    Message, InlineKeyboardMarkup,
    InlineKeyboardButton, CallbackQuery,
    InputMediaPhoto
)
import asyncio
from typing import DefaultDict
from Bot.errors import capture_and_handle_error
from Bot.utils import warned_user_filter , command_filter
from Bot.database.globalmarket import GlobalMarket
from texts import WAIFU , ANIME

market = GlobalMarket()
active_locks = DefaultDict(asyncio.Lock)  

# List command handler
@app.on_message(Command("list") & filters.private & command_filter)
@capture_and_handle_error
@warned_user_filter
async def list_player(client: Client, message: Message):
    user_id = message.from_user.id
    try:
        # First ask for player ID
        player_msg = await client.ask(
            chat_id=message.chat.id,
            text=f"Please send the {WAIFU} ID you want to list:",
            user_id=user_id,
            filters=filters.text,
            timeout=300
        )
        
        # Verify ownership and get character details
        char_data = await get_character_details(player_msg)
        if not char_data:
            await message.reply(f"Invalid {WAIFU} ID.")
            return
            
        # Check if it's a video waifu
        if char_data.get("is_video", False):
            await message.reply(f"⚠️ Video {WAIFU}s cannot be placed in auctions!")
            return
        
        # Then ask for price
        price_msg = await client.ask(
            chat_id=message.chat.id,
            text="Set your asking price in GRABTOKENS:",
            user_id=user_id,
            filters=filters.text,
            timeout=300
        )
        
        try:
            player_id = player_msg.text.strip()
            price = int(price_msg.text)
            if price < 0 :
                await message.reply("Price Should Be Positive")
                return
        except ValueError:
            await message.reply("Invalid price format. Please use whole numbers only.")
            return

        # Verify ownership and get character details
        char_data = await get_character_details(player_id)
        if not char_data:
            await message.reply(f"Invalid {WAIFU} ID.")
            return
            
        user_collection = await db.Collection.find_one({"user_id": user_id})
        if not user_collection or not any(img["image_id"] == player_id for img in user_collection.get("images", [])):
            await message.reply(f"You don't own this {WAIFU}!")
            return

        # Create confirmation message
        markup = InlineKeyboardMarkup([
            [InlineKeyboardButton("✅ Confirm", callback_data=f"confirm_list:{player_id}:{price}"),
             InlineKeyboardButton("❌ Cancel", callback_data="cancel_list")]
        ])
        
        await message.reply_photo(
            photo=char_data["img_url"],
            caption=f"**Name:** {char_data['name']}\n"
                    f"{char_data['rarity_sign']} **Rarity:** {char_data['rarity']}\n"
                    f"**{ANIME}**: {char_data['anime']}\n"
                    f"**Price:** {price} GRABTOKENS\n"
                    f"Are you sure you want to list this {WAIFU}?",
            reply_markup=markup
        )
        
    except asyncio.TimeoutError:
        await message.reply("Listing process timed out. Please try again.")

# List confirmation handler
@app.on_callback_query(filters.regex(r"^confirm_list:|^cancel_list"))
@capture_and_handle_error
async def handle_list_confirmation(client: Client, query: CallbackQuery):
    user_id = query.from_user.id
    async with active_locks[user_id]:  # Prevent multiple concurrent listings
        if query.data == "cancel_list":
            await query.message.delete()
            await query.answer("Listing canceled!")
            return
            
        _, player_id, price = query.data.split(":")
        price = int(price)
        
        # Verify ownership again in case state changed
        user_collection = await db.Collection.find_one({"user_id": user_id})
        if not user_collection or not any(img["image_id"] == player_id for img in user_collection.get("images", [])):
            await query.answer(f"You no longer own this {WAIFU}!", show_alert=True)
            await query.message.delete()
            return
            
        # Proceed with listing
        listing_id = await market.list_player(user_id, player_id, price, query.from_user.username)
        if listing_id:
            await query.message.edit_caption(
                caption=f"✅ Successfully listed {WAIFU} for {price} GRABTOKENS!",
                reply_markup=None
            )
        else:
            await query.answer(f"Failed to list {WAIFU}. Please try again.", show_alert=True)

# Unlist command handler
@app.on_message(Command("unlist") & filters.private & command_filter)
@capture_and_handle_error
@warned_user_filter
async def unlist_player(client: Client, message: Message):
    user_id = message.from_user.id
    listings = await market.search_listings(seller_id=user_id)
    
    if not listings:
        await message.reply("You have no active listings!")
        return
        
    buttons = []
    for listing in listings:
        char_data = await get_character_details(listing["player_id"])
        btn_text = f"{char_data['name']} - {listing['price']} GRABTOKENS"
        buttons.append(
            [InlineKeyboardButton(btn_text, callback_data=f"unlist_{listing['_id']}")]
        )
        
    await message.reply(
        "**Your Active Listings:**\nSelect one to unlist:",
        reply_markup=InlineKeyboardMarkup(buttons)
    )

# Unlist callback handler
@app.on_callback_query(filters.regex(r"^unlist_"))
async def handle_unlist(client: Client, query: CallbackQuery):
    user_id = query.from_user.id
    listing_id = query.data.split("_")[1]
    
    async with active_locks[f"unlist_{listing_id}"]:  # Lock specific listing
        success = await market.unlist_player(listing_id, user_id)
        if success:
            await query.message.edit_text(
                f"✅ {WAIFU} unlisted successfully!",
                reply_markup=None
            )
        else:
            await query.answer("Failed to unlist. Listing not found or unauthorized!", show_alert=True)

# Market command handler with pagination
@app.on_message(Command("market") & filters.private & command_filter)
@capture_and_handle_error
@warned_user_filter
async def show_market(client: Client, message: Message, page: int = 1):
    per_page = 8
    listings, total = await market.get_market_listings(page, per_page)
    
    if not listings:
        await message.reply("Marketplace is empty!")
        return
        
    buttons = []
    for listing in listings:
        char_data = await get_character_details(listing["player_id"])
        btn_text = f"{char_data['name']} - {listing['price']} GRABTOKENS"
        buttons.append(
            [InlineKeyboardButton(
                btn_text, 
                callback_data=f"view_{listing['_id']}"
            )]
        )
        
    # Pagination controls
    pagination = []
    if page > 1:
        pagination.append(InlineKeyboardButton("⬅️ Previous", callback_data=f"market_{page-1}"))
    if total > page * per_page:
        pagination.append(InlineKeyboardButton("Next ➡️", callback_data=f"market_{page+1}"))
        
    if pagination:
        buttons.append(pagination)
        
    await message.reply(
        f"**Global Marketplace** (Page {page})",
        reply_markup=InlineKeyboardMarkup(buttons)
    )

# Market interaction handlers
@app.on_callback_query(filters.regex(r"^market_|^view_"))
@capture_and_handle_error
async def handle_market_interaction(client: Client, query: CallbackQuery):
    user_id = query.from_user.id
    data = query.data.split("_")
    
    if data[0] == "market":
        await show_market(client, query.message, int(data[1]))
        await query.answer()
        return
        
    listing_id = data[1]
    listing = await db.Market.find_one({"_id": ObjectId(listing_id)})
    if not listing:
        await query.answer("Listing no longer available!", show_alert=True)
        return
        
    char_data = await get_character_details(listing["player_id"])
    markup = InlineKeyboardMarkup([
        [InlineKeyboardButton(
            "💰 Buy Now", 
            callback_data=f"buy_{listing_id}"
        )],
        [InlineKeyboardButton("⬅️ Back", callback_data=f"market_1")]
    ])
    
    await query.message.edit_media(
        InputMediaPhoto(
            char_data["img_url"],
            caption=f"**Name:** {char_data['name']}\n"
                    f"{char_data['rarity_sign']} **Rarity:** {char_data['rarity']}\n"
                    f"**{ANIME}**: {char_data['anime']}\n"
                    f"**Price:** {listing['price']} GRABTOKENS\n"
                    f"Seller: {listing.get('listed_by', 'Anonymous')}"
        ),
        reply_markup=markup
    )
    await query.answer()

# Buy handler with double confirmation
@app.on_callback_query(filters.regex(r"^buy_"))
@capture_and_handle_error
async def handle_buy(client: Client, query: CallbackQuery):
    user_id = query.from_user.id
    listing_id = query.data.split("_")[1]
    
    async with active_locks[f"buy_{listing_id}"]:  # Prevent concurrent purchases
        listing = await db.Market.find_one({"_id": ObjectId(listing_id)})
        if not listing:
            await query.answer("This listing has expired!", show_alert=True)
            return
            
        confirm_markup = InlineKeyboardMarkup([
            [InlineKeyboardButton("✅ Confirm Purchase", callback_data=f"confirmbuy_{listing_id}"),
             InlineKeyboardButton("❌ Cancel", callback_data=f"view_{listing_id}")]
        ])
        
        await query.message.edit_caption(
            caption=query.message.caption + f"\n\n**Are you sure you want to buy this {WAIFU}?**",
            reply_markup=confirm_markup
        )
        await query.answer()

# Final buy confirmation handler
@app.on_callback_query(filters.regex(r"^confirmbuy_"))
@capture_and_handle_error
async def confirm_buy(client: Client, query: CallbackQuery):
    user_id = query.from_user.id
    listing_id = query.data.split("_")[1]
    
    async with active_locks[f"buy_{listing_id}"]:
        success = await market.buy_player(listing_id, user_id, query.from_user.username)
        if success:
            await query.message.edit_caption(
                caption=f"🎉 Purchase successful! The {WAIFU} has been added to your collection.",
                reply_markup=None
            )
        else:
            await query.answer("Purchase failed. Insufficient funds or listing expired!", show_alert=True)