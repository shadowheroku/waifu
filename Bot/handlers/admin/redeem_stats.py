from Bot import app, Command
from Bot.database.statsdb import get_redeem_stats, clear_expired_redeem_codes
from Bot.utils import admin_filter

@app.on_message(Command("rstats") & admin_filter)
async def redeem_stats_command(client, message):
    stats = await get_redeem_stats()
    
    top_generators_text = ""
    for i, user in enumerate(stats["top_generators"], 1):
        user_name = user["user_name"]
        count = user["count"]
        top_generators_text += f"{i}. {user_name} - {count} codes\n"
    
    stats_message = (
        "📊 **Redeem Code Statistics**\n\n"
        f"**Total Codes:** {stats['total_codes']}\n"
        f"**Claimed Codes:** {stats['claimed_codes']}\n"
        f"**Unclaimed Codes:** {stats['unclaimed_codes']}\n"
        f"**Expired Codes:** {stats['expired_codes']}\n\n"
        f"**Recent Activity (24h)**\n"
        f"**New Codes:** {stats['recent_codes']}\n"
        f"**New Claims:** {stats['recent_claims']}\n\n"
        f"**Top Code Generators**\n{top_generators_text}"
    )
    
    await message.reply_text(stats_message)

@app.on_message(Command("clearexpiredcodes") & admin_filter)
async def clear_expired_codes_command(client, message):
    deleted_count = await clear_expired_redeem_codes()
    
    await message.reply_text(
        f"🗑️ **Expired Codes Cleanup**\n\n"
        f"Successfully deleted {deleted_count} expired redeem codes."
    ) 