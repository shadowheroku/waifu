from Bot import app, Command
from Bot.utils import command_filter, og_filter
from Bot.database.questiondb import (
    create_question, get_question, complete_question, place_question_bet,
    get_user_question_bets, get_active_questions, get_question_stats
)
from Bot.database.grabtokendb import decrease_grab_token, add_grab_token, get_user_balance
from Bot.errors import capture_and_handle_error
from pyrogram.types import Message
from Bot.config import SUPPORT_CHAT_ID
import re
from datetime import datetime

def parse_command_args(text: str):
    """Parse command arguments with named parameters"""
    args = {}
    # Extract parameters using regex
    pattern = r'-(\w+)\s+([^-]+)'
    matches = re.finditer(pattern, text)
    for match in matches:
        key = match.group(1)
        value = match.group(2).strip()
        args[key] = value
    return args

@app.on_message(Command(["createquestion" , "createques"]) & og_filter)
@capture_and_handle_error
async def create_question_command(client, message: Message):
    """Create a new question with options and betting parameters"""
    args = parse_command_args(message.text)
    
    # Validate required parameters
    required_params = ["question", "options", "fee", "winamount"]
    missing_params = [param for param in required_params if param not in args]
    
    if missing_params:
        await message.reply_text(
            "❌ Missing required parameters.\n"
            "Usage: `/createquestion -question (question) -options (options separated by ,) "
            "-fee (amount) -winamount (amount) [-timelimit (hours)]`\n\n"
            f"Missing: {', '.join(missing_params)}"
        )
        return
    
    try:
        fee = int(args["fee"])
        win_amount = int(args["winamount"])
        time_limit = int(args.get("timelimit", 0)) if "timelimit" in args else None
    except ValueError:
        await message.reply_text("❌ Fee, win amount, and time limit must be numbers.")
        return
    
    if fee <= 0 or win_amount <= 0:
        await message.reply_text("❌ Fee and win amount must be greater than 0.")
        return
    
    if time_limit is not None and time_limit <= 0:
        await message.reply_text("❌ Time limit must be greater than 0.")
        return
    
    # Split options by comma and clean them
    options = [opt.strip() for opt in args["options"].split(",")]
    if len(options) < 2:
        await message.reply_text("❌ Please provide at least 2 options.")
        return
    
    # Create the question
    question_id = await create_question(
        args["question"],
        options,
        fee,
        win_amount,
        message.from_user.id,
        time_limit
    )
    
    # Format options for display
    options_text = "\n".join(f"{i+1}. {opt}" for i, opt in enumerate(options))
    
    # Create response text
    response = (
        f"❓ **New Question Created!**\n\n"
        f"**Question:** {args['question']}\n\n"
        f"**Options:**\n{options_text}\n\n"
        f"**Entry Fee:** {fee:,} tokens\n"
        f"**Win Amount:** {win_amount:,} tokens\n"
    )
    
    if time_limit:
        response += f"**Time Limit:** {time_limit} hours\n"
    
    response += f"**Question ID:** `{question_id}`\n\n"
    response += "Users can now answer using:\n"
    response += f"> `/ansques {question_id} option_number`"
    
    await message.reply_text(response)
    
    # Send to support chat and pin
    x = await app.send_message(SUPPORT_CHAT_ID, response)
    await x.pin()

@app.on_message(Command("ansques") & command_filter)
@capture_and_handle_error
async def answer_question_command(client, message: Message):
    """Answer a question by placing a bet"""
    if len(message.command) != 3:
        await message.reply_text(
            "❌ Please provide question ID and option number.\n"
            "Usage: `/ansques QUESTION_ID option_number`"
        )
        return
    
    question_id = message.command[1].upper()
    try:
        option_number = int(message.command[2]) - 1  # Convert to 0-based index
    except ValueError:
        await message.reply_text("❌ Please provide a valid option number.")
        return
    
    # Get question details
    question = await get_question(question_id)
    if not question:
        await message.reply_text("❌ Question not found.")
        return
    
    if question["status"] != "active":
        await message.reply_text("❌ This question is no longer active.")
        return
    
    if option_number < 0 or option_number >= len(question["options"]):
        await message.reply_text("❌ Invalid option number.")
        return
    
    # Check if user has already answered
    user_bets = [bet for bet in question["bets"] if bet["user_id"] == message.from_user.id]
    if user_bets:
        await message.reply_text("❌ You have already answered this question.")
        return
    
    # Check if user has enough tokens
    user_balance = await get_user_balance(message.from_user.id)
    if user_balance < question["fee"]:
        await message.reply_text(f"❌ You don't have enough Grab-Tokens. Required: {question['fee']:,}")
        return
    
    # Place the bet
    success, msg = await place_question_bet(question_id, message.from_user.id, option_number, question["fee"])
    if not success:
        await message.reply_text(f"❌ {msg}")
        return
    
    # Deduct tokens from user's balance
    await decrease_grab_token(message.from_user.id, question["fee"])
    
    await message.reply_text(
        f"✅ **Answer Submitted!**\n\n"
        f"**Question:** {question['question']}\n"
        f"**Your Answer:** {question['options'][option_number]}\n"
        f"**Entry Fee:** {question['fee']:,} tokens\n"
        f"**Potential Win:** {question['win_amount']:,} tokens\n\n"
        f"Good luck! 🍀"
    )

@app.on_message(Command(["completequestion" , "completeques"]) & og_filter)
@capture_and_handle_error
async def complete_question_command(client, message: Message):
    """Complete a question and distribute winnings"""
    if len(message.command) != 3:
        await message.reply_text(
            "❌ Please provide question ID and correct option number.\n"
            "Usage: `/completequestion QUESTION_ID option_number`"
        )
        return
    
    question_id = message.command[1].upper()
    try:
        correct_option = int(message.command[2]) - 1  # Convert to 0-based index
    except ValueError:
        await message.reply_text("❌ Please provide a valid option number.")
        return
    
    # Complete the question
    success, msg = await complete_question(question_id, correct_option)
    if not success:
        await message.reply_text(f"❌ {msg}")
        return
    
    # Get question details
    question = await get_question(question_id)
    stats = await get_question_stats(question_id)
    
    # Distribute winnings to winners
    winners = [bet for bet in question["bets"] if bet["option_number"] == correct_option]
    for winner in winners:
        await add_grab_token(winner["user_id"], question["win_amount"])
    
    # Format options with bet counts
    options_text = "\n".join(
        f"{i+1}. {opt} ({stats['option_counts'][i]} bets, {stats['option_totals'][i]:,} tokens)"
        for i, opt in enumerate(question["options"])
    )
    
    # Send completion message
    await message.reply_text(
        f"🏆 **Question Completed!**\n\n"
        f"**Question:** {question['question']}\n\n"
        f"**Options:**\n{options_text}\n\n"
        f"**Correct Answer:** {question['options'][correct_option]}\n"
        f"**Total Participants:** {stats['total_bets']}\n"
        f"**Total Pool:** {stats['total_amount']:,} tokens\n"
        f"**Winners:** {len(winners)} users\n"
        f"**Win Amount:** {question['win_amount']:,} tokens each"
    )
    
    # Send to support chat and pin
    x = await app.send_message(SUPPORT_CHAT_ID, (
        f"🏆 **Question Completed!**\n\n"
        f"**Question:** {question['question']}\n\n"
        f"**Options:**\n{options_text}\n\n"
        f"**Correct Answer:** {question['options'][correct_option]}\n"
        f"**Total Participants:** {stats['total_bets']}\n"
        f"**Total Pool:** {stats['total_amount']:,} tokens\n"
        f"**Winners:** {len(winners)} users\n"
        f"**Win Amount:** {question['win_amount']:,} tokens each"
    ))
    await x.pin()

@app.on_message(Command(["myquestions" , "myques"]) & command_filter)
@capture_and_handle_error
async def my_questions_command(client, message: Message):
    """Show user's active question bets"""
    user_id = message.from_user.id
    user_questions = await get_user_question_bets(user_id)
    
    if not user_questions:
        await message.reply_text("📝 You don't have any active question bets.")
        return
    
    response = "❓ **Your Active Question Bets**\n\n"
    for question in user_questions:
        # Find user's bet
        user_bet = next(bet for bet in question["bets"] if bet["user_id"] == user_id)
        
        response += (
            f"**Question:** {question['question']}\n"
            f"**Your Answer:** {question['options'][user_bet['option_number']]}\n"
            f"**Entry Fee:** {question['fee']:,} tokens\n"
            f"**Potential Win:** {question['win_amount']:,} tokens\n"
            f"**Question ID:** `{question['question_id']}`\n\n"
        )
    
    await message.reply_text(response)

@app.on_message(Command(["activequestions" , "activeques"]) & command_filter)
@capture_and_handle_error
async def active_questions_command(client, message: Message):
    """Show all active questions"""
    active_questions = await get_active_questions()
    
    if not active_questions:
        await message.reply_text("📝 There are no active questions at the moment.")
        return
    
    response = "❓ **Active Questions**\n\n"
    for question in active_questions:
        stats = await get_question_stats(question["question_id"])
        
        # Format options with bet counts
        options_text = "\n".join(
            f"{i+1}. {opt} ({stats['option_counts'][i]} bets, {stats['option_totals'][i]:,} tokens)"
            for i, opt in enumerate(question["options"])
        )
        
        response += (
            f"**Question:** {question['question']}\n\n"
            f"**Options:**\n{options_text}\n\n"
            f"**Entry Fee:** {question['fee']:,} tokens\n"
            f"**Win Amount:** {question['win_amount']:,} tokens\n"
            f"**Question ID:** `{question['question_id']}`\n"
            f"**Created:** {question['created_at'].strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        )
    
    await message.reply_text(response)

@app.on_message(Command(["questioninfo" , "questioninf"]) & command_filter)
@capture_and_handle_error
async def question_info_command(client, message: Message):
    """Show detailed information about a specific question"""
    if len(message.command) != 2:
        await message.reply_text(
            "❌ Please provide a question ID.\n"
            "Usage: `/questioninfo QUESTION_ID`"
        )
        return
    
    question_id = message.command[1].upper()
    question = await get_question(question_id)
    
    if not question:
        await message.reply_text("❌ Question not found.")
        return
    
    stats = await get_question_stats(question_id)
    
    # Format options with bet counts
    options_text = "\n".join(
        f"{i+1}. {opt} ({stats['option_counts'][i]} bets, {stats['option_totals'][i]:,} tokens)"
        for i, opt in enumerate(question["options"])
    )
    
    # Calculate time remaining if there's a time limit
    time_remaining = None
    if question.get("time_limit"):
        time_elapsed = (datetime.utcnow() - question["created_at"]).total_seconds() / 3600
        time_remaining = max(0, question["time_limit"] - time_elapsed)
    
    response = (
        f"❓ **Question Information**\n\n"
        f"**Question:** {question['question']}\n"
        f"**Status:** {'✅ Completed' if question['status'] == 'completed' else '🔄 Active'}\n"
        f"**Created:** {question['created_at'].strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        f"**Options:**\n{options_text}\n\n"
        f"**Entry Fee:** {question['fee']:,} tokens\n"
        f"**Win Amount:** {question['win_amount']:,} tokens\n"
        f"**Total Participants:** {stats['total_bets']}\n"
        f"**Total Pool:** {stats['total_amount']:,} tokens\n"
    )
    
    if time_remaining is not None:
        response += f"**Time Remaining:** {time_remaining:.1f} hours\n"
    
    if question['status'] == 'completed':
        response += f"\n**🏆 Correct Answer:** {question['options'][question['correct_option']]}"
    
    await message.reply_text(response) 