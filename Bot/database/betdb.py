from Bot.database import db
from datetime import datetime
import random
import string

async def generate_bet_id():
    """Generate a unique bet ID"""
    while True:
        # Generate a random 6 character string
        bet_id = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
        # Check if bet ID already exists
        existing_bet = await db.Bets.find_one({"bet_id": bet_id})
        if not existing_bet:
            return bet_id

async def create_bet(team1: str, team2: str, created_by: int, time_limit: int = None):
    """Create a new bet"""
    bet_id = await generate_bet_id()
    bet_data = {
        "bet_id": bet_id,
        "team1": team1,
        "team2": team2,
        "created_by": created_by,
        "created_at": datetime.utcnow(),
        "status": "active",  # active, completed
        "winning_team": None,
        "time_limit": time_limit,  # Time limit in hours
        "bets": {
            "team1": [],  # List of {user_id, amount} dictionaries
            "team2": []
        }
    }
    await db.Bets.insert_one(bet_data)
    return bet_id

async def get_bet(bet_id: str):
    """Get bet details by ID"""
    return await db.Bets.find_one({"bet_id": bet_id})

async def place_bet(bet_id: str, user_id: int, team: str, amount: int):
    """Place a bet on a team"""
    bet = await get_bet(bet_id)
    if not bet:
        return False, "Bet not found"
    
    if bet["status"] != "active":
        return False, "Bet is not active"
    
    # Check if bet has expired due to time limit
    if bet.get("time_limit"):
        time_elapsed = (datetime.utcnow() - bet["created_at"]).total_seconds() / 3600
        if time_elapsed > bet["time_limit"]:
            return False, "Bet has expired due to time limit"
    
    if team not in ["team1", "team2"]:
        return False, "Invalid team selection"
    
    # Check if user has already placed a bet on this bet
    for team_name in ["team1", "team2"]:
        for bet_info in bet["bets"][team_name]:
            if bet_info["user_id"] == user_id:
                return False, "You have already placed a bet on this match"
    
    # Add bet to the team's list
    await db.Bets.update_one(
        {"bet_id": bet_id},
        {"$push": {f"bets.{team}": {"user_id": user_id, "amount": amount}}}
    )
    return True, "Bet placed successfully"

async def complete_bet(bet_id: str, winning_team: str):
    """Complete a bet and distribute winnings"""
    bet = await get_bet(bet_id)
    if not bet:
        return False, "Bet not found"
    
    if bet["status"] != "active":
        return False, "Bet is already completed"
    
    if winning_team not in ["team1", "team2"]:
        return False, "Invalid winning team"
    
    # Update bet status and winning team
    await db.Bets.update_one(
        {"bet_id": bet_id},
        {
            "$set": {
                "status": "completed",
                "winning_team": winning_team,
                "completed_at": datetime.utcnow()
            }
        }
    )
    
    return True, "Bet completed successfully"

async def get_user_bets(user_id: int):
    """Get all bets placed by a user"""
    return await db.Bets.find({
        "bets.team1.user_id": user_id,
        "status": "active"
    }).to_list(length=None)

async def get_active_bets():
    """Get all active bets"""
    return await db.Bets.find({"status": "active"}).to_list(length=None) 