from datetime import datetime
import random
import string
from Bot.database import db

async def generate_question_id():
    """Generate a unique question ID"""
    while True:
        # Generate a 6-character ID
        question_id = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
        # Check if ID exists
        if not await db.Questions.find_one({"question_id": question_id}):
            return question_id

async def create_question(question: str, options: list, fee: int, win_amount: int, created_by: int, time_limit: int = None):
    """Create a new question"""
    question_id = await generate_question_id()
    question_data = {
        "question_id": question_id,
        "question": question,
        "options": options,
        "fee": fee,
        "win_amount": win_amount,
        "created_by": created_by,
        "created_at": datetime.utcnow(),
        "status": "active",  # active, completed
        "correct_option": None,
        "time_limit": time_limit,  # Time limit in hours
        "bets": []  # List of {user_id, option_number, amount} dictionaries
    }
    await db.Questions.insert_one(question_data)
    return question_id

async def get_question(question_id: str):
    """Get question details by ID"""
    return await db.Questions.find_one({"question_id": question_id})

async def place_question_bet(question_id: str, user_id: int, option_number: int, amount: int):
    """Place a bet on a question option"""
    question = await get_question(question_id)
    if not question:
        return False, "Question not found"
    
    if question["status"] != "active":
        return False, "Question is not active"
    
    # Check if question has expired due to time limit
    if question.get("time_limit"):
        time_elapsed = (datetime.utcnow() - question["created_at"]).total_seconds() / 3600
        if time_elapsed > question["time_limit"]:
            return False, "Question has expired due to time limit"
    
    if option_number < 0 or option_number >= len(question["options"]):
        return False, "Invalid option number"
    
    # Add bet to the question's list
    await db.Questions.update_one(
        {"question_id": question_id},
        {"$push": {"bets": {"user_id": user_id, "option_number": option_number, "amount": amount}}}
    )
    return True, "Bet placed successfully"

async def complete_question(question_id: str, correct_option: int):
    """Complete a question and distribute winnings"""
    question = await get_question(question_id)
    if not question:
        return False, "Question not found"
    
    if question["status"] != "active":
        return False, "Question is already completed"
    
    if correct_option < 0 or correct_option >= len(question["options"]):
        return False, "Invalid correct option"
    
    # Update question status and correct option
    await db.Questions.update_one(
        {"question_id": question_id},
        {
            "$set": {
                "status": "completed",
                "correct_option": correct_option,
                "completed_at": datetime.utcnow()
            }
        }
    )
    
    return True, "Question completed successfully"

async def get_user_question_bets(user_id: int):
    """Get all question bets placed by a user"""
    return await db.Questions.find({
        "bets.user_id": user_id,
        "status": "active"
    }).to_list(length=None)

async def get_active_questions():
    """Get all active questions"""
    return await db.Questions.find({"status": "active"}).to_list(length=None)

async def get_question_stats(question_id: str):
    """Get statistics for a question"""
    question = await get_question(question_id)
    if not question:
        return None
    
    # Calculate total bets for each option
    option_totals = [0] * len(question["options"])
    option_counts = [0] * len(question["options"])
    
    for bet in question["bets"]:
        option_totals[bet["option_number"]] += bet["amount"]
        option_counts[bet["option_number"]] += 1
    
    return {
        "option_totals": option_totals,
        "option_counts": option_counts,
        "total_bets": len(question["bets"]),
        "total_amount": sum(option_totals)
    } 