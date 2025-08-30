from Bot import app , Command
from Bot.database.grabtokendb import decrease_grab_token, add_grab_token, get_user_balance
import random
import asyncio
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from pyrogram.errors import FloodWait
from collections import defaultdict
from Bot.errors import capture_and_handle_error
from Bot.utils import warned_user_filter , command_filter

active_requests = {}
active_locks = defaultdict(asyncio.Lock)
FIGHT_STAKE = 10000

def get_existing_request_id(user_id: int) -> str:
    """Find the request ID containing the given user"""
    for rid in active_requests.keys():
        if str(user_id) in rid.split('-'):
            return rid
    return None

@app.on_message(Command("fight") & filters.reply & command_filter)
@capture_and_handle_error
@warned_user_filter
async def initiate_fight(client: Client, message: Message):
    # Basic validations
    if not message.reply_to_message or not message.reply_to_message.from_user:
        return await message.reply("❌ Please reply to a user's message to challenge them!")
    
    challenger = message.from_user
    challenged = message.reply_to_message.from_user
    
    if challenger.id == challenged.id:
        return await message.reply("🚫 You can't fight yourself!")

    # Check balances
    try:
        challenger_balance = await get_user_balance(challenger.id)
        challenged_balance = await get_user_balance(challenged.id)
    except Exception as e:
        return await message.reply("🔧 Error checking balances. Please try again later.")

    if challenger_balance < FIGHT_STAKE:
        return await message.reply(f"❌ You need at least {FIGHT_STAKE:,} GRAB to fight!")
    if challenged_balance < FIGHT_STAKE:
        return await message.reply("❌ Challenged user doesn't have enough GRAB tokens!")

    # Check existing requests
    existing_request = get_existing_request_id(challenger.id)
    if existing_request:
        markup = InlineKeyboardMarkup([[
            InlineKeyboardButton("Cancel Last Fight 🚫", callback_data=f"fight_cancel_{existing_request}")
        ]])
        return await message.reply("⏳ You already have a pending fight request!", reply_markup=markup)
    
    existing_request = get_existing_request_id(challenged.id)
    if existing_request:
        return await message.reply("⏳ This user is already in another fight!")

    # Create fight request
    request_id = f"{challenger.id}-{challenged.id}"
    markup = InlineKeyboardMarkup([
        [InlineKeyboardButton("Accept ⚔️", callback_data=f"fight_accept_{challenger.id}"),
         InlineKeyboardButton("Decline 🚫", callback_data="fight_decline")]
    ])
    
    try:
        fight_msg = await message.reply(
            f"⚡ **Fight Challenge!** ⚡\n\n"
            f"{challenger.mention} vs {challenged.mention}\n"
            f"**Stake:** {FIGHT_STAKE:,} GRAB Tokens\n\n"
            "⏳ Expires in 2 minutes",
            reply_markup=markup
        )
        active_requests[request_id] = fight_msg.id
    except FloodWait as e:
        await asyncio.sleep(e.value)
        return await initiate_fight(client, message)

    # Auto-cleanup after 120 seconds
    await asyncio.sleep(120)
    if request_id in active_requests:
        del active_requests[request_id]
        try:
            await fight_msg.edit("⌛ Fight request expired.", reply_markup=None)
        except Exception:
            pass

@app.on_callback_query(filters.regex(r"^fight_(accept|decline|cancel)"))
@capture_and_handle_error
async def handle_fight_responses(client: Client, query: CallbackQuery):
    data = query.data.split('_')
    action = data[1]
    
    if action == "cancel":
        request_id = data[2]
        # Validate user participation
        parts = request_id.split('-')
        if str(query.from_user.id) not in parts:
            await query.answer("❌ This isn't your fight to cancel!", show_alert=True)
            return
        
        if request_id not in active_requests:
            await query.answer("❌ Request already expired/canceled", show_alert=True)
            return
            
        # Delete original fight message
        try:
            await client.delete_messages(query.message.chat.id, active_requests[request_id])
        except Exception:
            pass
        
        # Cleanup and confirm
        del active_requests[request_id]
        await query.message.edit("✅ Fight request canceled.")
        return

    elif action == "decline":

        if query.from_user.id != query.message.reply_to_message.reply_to_message.from_user.id:
            await query.answer("❌ This challenge isn't for you!", show_alert=True)
            return


        request_id = get_existing_request_id(query.from_user.id)
        if not request_id:
            await query.answer("❌ No active request found", show_alert=True)
            return
        
        del active_requests[request_id]
        await query.message.edit("❌ Fight declined.")
        return

    # Handle fight acceptance
    elif action == "accept":
        if query.from_user.id != query.message.reply_to_message.reply_to_message.from_user.id:
            await query.answer("❌ This challenge isn't for you!", show_alert=True)
            return

        challenger_id = int(data[2])
        challenged_id = query.from_user.id
        request_id = f"{challenger_id}-{challenged_id}"

        if request_id not in active_requests:
            await query.answer("❌ Request expired!", show_alert=True)
            return

        async with active_locks[request_id]:
            # Re-check balances
            try:
                if (await get_user_balance(challenger_id) < FIGHT_STAKE or 
                    await get_user_balance(challenged_id) < FIGHT_STAKE):
                    raise ValueError("Insufficient balance")
            except Exception:
                del active_requests[request_id]
                return await query.message.edit("❌ Insufficient funds! Fight canceled.", reply_markup=None)

            await query.message.edit("⚔️ Fight starting...", reply_markup=None)
            await animate_fight(client, query.message, challenger_id, challenged_id)

async def animate_fight(client: Client, message: Message, uid1: int, uid2: int):
    try:
        animations = [
            "🔥💥 **CLASH!** 💥🔥",
            "🌪️💥 **FINAL IMPACT!** 💥🌪️"
        ]
        
        for frame in animations:
            await message.edit(frame)
            await asyncio.sleep(1.5)
        
        # Determine winner
        winner_id = random.choice([uid1, uid2])
        loser_id = uid1 if winner_id != uid1 else uid2
        
        # Update balances
        success = await decrease_grab_token(loser_id, FIGHT_STAKE)
        if not success:
            return await message.edit("❌ Transaction failed! Fight canceled.")
        
        await add_grab_token(winner_id, FIGHT_STAKE)
        
        # Get mentions
        winner = (await client.get_users(winner_id)).mention
        loser = (await client.get_users(loser_id)).mention
        
        # Final result
        result = (
            f"🏆 **FIGHT RESULTS** 🏆\n\n"
            f"🎉 **Winner:** {winner}\n"
            f"💰 **Reward:** +{FIGHT_STAKE:,} GRAB\n\n"
            f"😞 **Loser:** {loser}\n"
            f"💸 **Loss:** -{FIGHT_STAKE:,} GRAB"
        )
        await message.edit(result)
        
    except FloodWait as e:
        await asyncio.sleep(e.value)
        await animate_fight(client, message, uid1, uid2)
    finally:
        request_id = f"{uid1}-{uid2}"
        if request_id in active_requests:
            del active_requests[request_id]

def find_request_id(msg: Message):
    for req_id, msg_id in active_requests.items():
        if msg_id == msg.id:
            return req_id
    return None

def validate_request(request_id: str, msg_id: int):
    return active_requests.get(request_id) == msg_id