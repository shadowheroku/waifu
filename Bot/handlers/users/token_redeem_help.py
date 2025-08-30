from Bot import app, Command
from Bot.utils import command_filter, warned_user_filter
from Bot.config import REDEEM_AMOUNT

@app.on_message(Command("thelp") & command_filter)
@warned_user_filter
async def token_redeem_help_command(client, message):
    """
    Help command to explain how to use the token redeem features.
    """
    help_text = (
        "💰 **Token Redeem System Help**\n\n"
        f"The token redeem system allows you to generate and redeem special codes worth {REDEEM_AMOUNT} GrabTokens!\n\n"
        "**Commands:**\n\n"
        "• `/tget` - Generate a special redeem code (limited to 5 per day)\n"
        "• `/tredeem CODE` - Redeem a code to get tokens\n\n"
        "**How it works:**\n\n"
        "1. Use `/tget` to generate a redeem code\n"
        "2. You'll receive a shortened link\n"
        "3. Visit the link and complete any required actions to reveal your code\n"
        "4. Use `/tredeem CODE` to claim your tokens\n\n"
        "**Notes:**\n"
        "• Each code is worth 500,000 GrabTokens\n"
        "• Codes expire after 24 hours\n"
        "• You can only generate 5 codes per day\n"
        "• Each code can only be redeemed once\n\n"
        "Happy collecting! 🏏"
    )
    
    await message.reply_text(help_text) 