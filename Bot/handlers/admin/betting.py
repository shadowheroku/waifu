from Bot import app, Command
from Bot.utils import command_filter, og_filter
from Bot.database.betdb import create_bet, get_bet, complete_bet, place_bet, get_user_bets, get_active_bets
from Bot.database.grabtokendb import decrease_grab_token, add_grab_token, get_user_balance
from Bot.errors import capture_and_handle_error
from pyrogram.types import Message
from Bot.config import SUPPORT_CHAT_ID , BET_STICKER_ID 
import asyncio
 
@app.on_message(Command("createbet") & og_filter)
@capture_and_handle_error
async def create_bet_command(client, message : Message):
    """Create a new bet between two teams"""
    if len(message.command) < 3:
        await message.reply_text(
            "❌ Please provide both team names.\n"
            "Usage: `/createbet Team1 Team2 [-time X]`\n"
            "Where X is the time limit in hours (optional)"
        )
        return
    
    team1 = message.command[1]
    team2 = message.command[2]
    time_limit = None
    
    # Check for time limit parameter
    if len(message.command) > 3 and message.command[3] == "-time":
        try:
            time_limit = int(message.command[4])
            if time_limit <= 0:
                await message.reply_text("❌ Time limit must be greater than 0 hours.")
                return
        except (ValueError, IndexError):
            await message.reply_text(
                "❌ Invalid time limit format.\n"
                "Usage: `/createbet Team1 Team2 -time X`\n"
                "Where X is the time limit in hours"
            )
            return
    
    bet_id = await create_bet(team1, team2, message.from_user.id, time_limit)
    
    time_limit_text = f"\n⏰ **Time Limit:** {time_limit} hours" if time_limit else ""
    
    await message.reply_text(
        f"🎮 **New Bet Created!**\n\n"
        f"**Team 1:** {team1}\n"
        f"**Team 2:** {team2}\n"
        f"**Bet ID:** `{bet_id}`{time_limit_text}\n\n"
        f"Users can now place bets using:\n"
        f"> `/betteam {bet_id} team1 or team2 amount`"
    )
    x = await app.send_message(SUPPORT_CHAT_ID, (
        f"🎮 **New Bet Created!**\n\n"
        f"**Team 1:** {team1}\n"
        f"**Team 2:** {team2}\n"
        f"**Bet ID:** `{bet_id}`{time_limit_text}\n\n"
        f"Users can now place bets using:\n"
        f"> `/betteam {bet_id} team1 or team2 amount`"
    ))
    await x.pin()

@app.on_message(Command("betteam") & command_filter)
@capture_and_handle_error
async def place_bet_command(client, message : Message):
    """Place a bet on a team"""
    if len(message.command) != 4:
        await message.reply_text(
            "❌ Please provide bet ID, team selection, and amount.\n"
            "Usage: `/betteam BET_ID team1 or team2 amount`"
        )
        return
    
    bet_id = message.command[1].upper()
    team = message.command[2].lower()
    try:
        amount = int(message.command[3])
    except ValueError:
        await message.reply_text("❌ Please provide a valid amount.")
        return
    
    if amount <= 0:
        await message.reply_text("❌ Bet amount must be greater than 0.")
        return

    if amount > 3000000:
        await message.reply_text("❌ Bet amount must be less than or equal to 30,00,000.")
        return
    
    # Check if user has enough tokens
    user_balance = await get_user_balance(message.from_user.id)
    if user_balance < amount:
        await message.reply_text("❌ You don't have enough Grab-Tokens to place this bet.")
        return
    
    # Place the bet
    success, msg = await place_bet(bet_id, message.from_user.id, team, amount)
    if not success:
        await message.reply_text(f"❌ {msg}")
        return
    
    # Deduct tokens from user's balance
    await decrease_grab_token(message.from_user.id, amount)
    
    # Get bet details for response
    bet = await get_bet(bet_id)
    team_name = bet["team1"] if team == "team1" else bet["team2"]
    
    x = await message.reply_cached_media(BET_STICKER_ID)
    
   
    await asyncio.sleep(1)
    await x.delete()
    
    await message.reply_text(
        f"✅ **Bet Placed Successfully!**\n\n"
        f"**Team:** {team_name}\n"
        f"**Amount:** {amount:,} Grab-Tokens\n"
        f"**Bet ID:** `{bet_id}`\n\n"
        f"Good luck! 🍀"
    )

@app.on_message(Command("completebet") & og_filter)
@capture_and_handle_error
async def complete_bet_command(client, message : Message):
    """Complete a bet and distribute winnings"""
    if len(message.command) != 3:
        await message.reply_text(
            "❌ Please provide bet ID and winning team.\n"
            "Usage: `/completebet BET_ID team1/team2`"
        )
        return
    
    bet_id = message.command[1].upper()
    winning_team = message.command[2].lower()
    
    # Complete the bet
    success, msg = await complete_bet(bet_id, winning_team)
    if not success:
        await message.reply_text(f"❌ {msg}")
        return
    
    # Get bet details
    bet = await get_bet(bet_id)
    winning_team_name = bet["team1"] if winning_team == "team1" else bet["team2"]
    
    # Distribute winnings to winners
    winners = bet["bets"][winning_team]
    for winner in winners:
        user_id = winner["user_id"]
        amount = winner["amount"]
        winnings = int(amount * 1.5)  # 1.5x return
        await add_grab_token(user_id, winnings)
    
    # Send completion message
    await message.reply_text(
        f"🏆 **Bet Completed!**\n\n"
        f"**Winning Team:** {winning_team_name}\n"
        f"**Bet ID:** `{bet_id}`\n\n"
        f"Winners have received 1.5x their bet amount! 🎉"
    ) 
    x = await app.send_message(SUPPORT_CHAT_ID, (
        f"🏆 **Bet Completed!**\n\n"
        f"**Winning Team:** {winning_team_name}\n"
        f"**Bet ID:** `{bet_id}`\n\n"
        f"Winners have received 1.5x their bet amount! 🎉"
    ))
    await x.pin()

@app.on_message(Command("mybets") & command_filter)
@capture_and_handle_error
async def my_bets_command(client, message: Message):
    """Show user's active bets"""
    user_id = message.from_user.id
    user_bets = await get_user_bets(user_id)
    
    if not user_bets:
        await message.reply_text("📝 You don't have any active bets.")
        return
    
    response = "🎮 **Your Active Bets**\n\n"
    for bet in user_bets:
        # Find which team the user bet on
        user_team = None
        bet_amount = 0
        for team in ["team1", "team2"]:
            for bet_info in bet["bets"][team]:
                if bet_info["user_id"] == user_id:
                    user_team = bet["team1"] if team == "team1" else bet["team2"]
                    bet_amount = bet_info["amount"]
                    break
            if user_team:
                break
        
        response += (
            f"**Bet ID:** `{bet['bet_id']}`\n"
            f"**Teams:** {bet['team1']} vs {bet['team2']}\n"
            f"**Your Bet:** {user_team} ({bet_amount:,} tokens)\n"
            f"**Potential Win:** {int(bet_amount * 1.5):,} tokens\n\n"
        )
    
    await message.reply_text(response)

@app.on_message(Command("activebets") & command_filter)
@capture_and_handle_error
async def active_bets_command(client, message: Message):
    """Show all active bets"""
    active_bets = await get_active_bets()
    
    if not active_bets:
        await message.reply_text("📝 There are no active bets at the moment.")
        return
    
    response = "🎮 **Active Bets**\n\n"
    for bet in active_bets:
        # Calculate total bets for each team
        team1_total = sum(b["amount"] for b in bet["bets"]["team1"])
        team2_total = sum(b["amount"] for b in bet["bets"]["team2"])
        
        response += (
            f"**Bet ID:** `{bet['bet_id']}`\n"
            f"**Teams:** {bet['team1']} vs {bet['team2']}\n"
            f"**Total Bets:**\n"
            f"  • {bet['team1']}: {team1_total:,} tokens\n"
            f"  • {bet['team2']}: {team2_total:,} tokens\n"
            f"**Created:** {bet['created_at'].strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        )
    
    await message.reply_text(response)

@app.on_message(Command("betinfo") & command_filter)
@capture_and_handle_error
async def bet_info_command(client, message: Message):
    """Show detailed information about a specific bet"""
    if len(message.command) != 2:
        await message.reply_text(
            "❌ Please provide a bet ID.\n"
            "Usage: `/betinfo BET_ID`"
        )
        return
    
    bet_id = message.command[1].upper()
    bet = await get_bet(bet_id)
    
    if not bet:
        await message.reply_text("❌ Bet not found.")
        return
    
    # Calculate total bets for each team
    team1_total = sum(b["amount"] for b in bet["bets"]["team1"])
    team2_total = sum(b["amount"] for b in bet["bets"]["team2"])
    
    # Count number of betters for each team
    team1_count = len(bet["bets"]["team1"])
    team2_count = len(bet["bets"]["team2"])
    
    response = (
        f"🎮 **Bet Information**\n\n"
        f"**Bet ID:** `{bet['bet_id']}`\n"
        f"**Status:** {'✅ Completed' if bet['status'] == 'completed' else '🔄 Active'}\n"
        f"**Teams:** {bet['team1']} vs {bet['team2']}\n"
        f"**Created:** {bet['created_at'].strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        f"**Team 1 ({bet['team1']}):**\n"
        f"  • Total Bets: {team1_total:,} tokens\n"
        f"  • Number of Betters: {team1_count}\n\n"
        f"**Team 2 ({bet['team2']}):**\n"
        f"  • Total Bets: {team2_total:,} tokens\n"
        f"  • Number of Betters: {team2_count}\n"
    )
    
    if bet['status'] == 'completed':
        winning_team = bet['team1'] if bet['winning_team'] == 'team1' else bet['team2']
        response += f"\n**🏆 Winning Team:** {winning_team}"
    
    await message.reply_text(response)
    