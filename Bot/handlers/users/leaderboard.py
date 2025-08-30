from pyrogram import Client, filters
from pyrogram.types import Message
from datetime import datetime
from pytz import timezone
from Bot import app , Command
from Bot.utils import command_filter, warned_user_filter
from Bot.errors import capture_and_handle_error
from Bot.config import SUPPORT_CHAT_ID , GLOG
from Bot.database.userdb import get_user_name
from Bot.utils import og_filter
from Bot.database.leaderboarddb import *
from Bot.database.grabtokendb import add_grab_token


async def generate_leaderboard_text(title, leaderboard, emoji):
    title_border = f"{'-' * 4} {emoji} **{title}** {emoji} {'-' * 14}\n"
    
    text = f"{title_border}\n"
    medals = ["🥇", "🥈", "🥉"]
    
    for index, entry in enumerate(leaderboard, start=1):
        rank = medals[index - 1] if index <= 3 else f"**{index}**"  # Use bold for ranks beyond 3rd place
        
        # Add padding and a border between ranks for cleaner appearance
        text += f"**{rank}** {entry['mention']} ➣ **{entry['total_characters']}** | " \
                f"**({entry['total_unique_characters']}**)\n"
        if index == 3:
            text += "\n"  # Add space after top 3
    
    
    return text


@app.on_message(Command("top") & filters.group & command_filter)
@warned_user_filter
@capture_and_handle_error
async def cmd_top(client: Client, message: Message):
    fetching_msg = await message.reply("🔄 **ғᴇᴛᴄʜɪɴɢ ʟᴇᴀᴅᴇʀʙᴏᴀʀᴅ ᴅᴇᴛᴀɪʟs...**")

    # Fetch all member IDs in the group chat
    members = client.get_chat_members(message.chat.id)
    member_ids = [member.user.id async for member in members]

    # Fetch leaderboard data
    leaderboard_data = await fetch_leaderboard_data(member_ids)

    # Update leaderboard with user names from the database with validation
    leaderboard = []
    for entry in leaderboard_data:
        if not entry.get("user_name"):
            continue
            
        user_id = entry["_id"]
        # Validate user ID to prevent invalid peer ID errors
        try:
            # Check if user ID is valid (not too large)
            if not isinstance(user_id, int) or user_id > 9999999999:
                # Use plain text instead of mention for invalid IDs
                mention = f"{entry['user_name']}"
            else:
                mention = f"[{entry['user_name']}](tg://user?id={user_id})"
                
            leaderboard.append({
                "user_id": user_id,
                "mention": mention,
                "total_characters": entry["total_characters"],
                "total_unique_characters": entry["total_unique_characters"],
            })
        except Exception as e:
            print(f"Error processing user {user_id}: {e}")
            # Still include the user but without a clickable mention
            leaderboard.append({
                "user_id": user_id,
                "mention": f"{entry['user_name']}",
                "total_characters": entry["total_characters"],
                "total_unique_characters": entry["total_unique_characters"],
            })

    # Generate the leaderboard text
    group_name = message.chat.title if message.chat.title else "Group"
    leaderboard_text = await generate_leaderboard_text(f"{group_name}'s Top 10 Collectors", leaderboard, "⛩️")

    await fetching_msg.delete()
    await message.reply(leaderboard_text)

@app.on_message(Command("gtop") & command_filter)
@warned_user_filter
@capture_and_handle_error
async def cmd_gtop(client: Client, message: Message):
    fetching_msg = await message.reply("🔄 **ғᴇᴛᴄʜɪɴɢ ɢʟᴏʙᴀʟ ʟᴇᴀᴅᴇʀʙᴏᴀʀᴅ ᴅᴇᴛᴀɪʟs...**")

    # Fetch leaderboard data
    leaderboard_data = await fetch_leaderboard_data()

    # Update leaderboard with user names from the database with validation
    leaderboard = []
    for entry in leaderboard_data:
        if not entry.get("user_name"):
            continue
            
        user_id = entry["_id"]
        # Validate user ID to prevent invalid peer ID errors
        try:
            # Check if user ID is valid (not too large)
            if not isinstance(user_id, int) or user_id > 9999999999:
                # Use plain text instead of mention for invalid IDs
                mention = f"{entry['user_name']}"
            else:
                mention = f"[{entry['user_name']}](tg://user?id={user_id})"
                
            leaderboard.append({
                "user_id": user_id,
                "mention": mention,
                "total_characters": entry["total_characters"],
                "total_unique_characters": entry["total_unique_characters"],
            })
        except Exception as e:
            print(f"Error processing user {user_id}: {e}")
            # Still include the user but without a clickable mention
            leaderboard.append({
                "user_id": user_id,
                "mention": f"{entry['user_name']}",
                "total_characters": entry["total_characters"],
                "total_unique_characters": entry["total_unique_characters"],
            })

    # Generate the leaderboard text
    leaderboard_text = await generate_leaderboard_text("Global Top 10 Collectors", leaderboard, "🌍")

    await fetching_msg.delete()
    await message.reply(leaderboard_text)


@app.on_message(Command("ctop") & command_filter)
@warned_user_filter
@capture_and_handle_error
async def cmd_ctop(client: Client, message: Message):
    fetching_msg = await message.reply("🔄 **ғᴇᴛᴄʜɪɴɢ ᴛᴏᴘ ᴄʜᴀᴛs ᴡɪᴛʜ Collect ᴄᴏᴜɴᴛs...**")

    # Fetch the top 10 chats with the highest smash counts
    groups = await fetch_top_chats()

    # Enhanced header and borders
    text = f"{'-' * 14} 🏆 **Top 10 Collectors Chats** 🏆 {'-' * 4}\n\n"
    medals = ["🥇", "🥈", "🥉"]

    for index, group in enumerate(groups, start=1):
        chat_name = group.get("chat_name")
        if not chat_name:
            continue

        rank = medals[index - 1] if index <= 3 else f"**{index}**"

        if "username" in group and group["username"]:
            chat_link = f"[{chat_name}](https://t.me/{group['username']})"
        else:
            chat_link = chat_name

        smash_count = group["smash_count"]
        text += f"**{rank}** {chat_link} —> **{smash_count}** ʜᴜɴᴛᴇᴅ\n"
    

    await fetching_msg.delete()
    await message.reply(text, disable_web_page_preview=True)


@app.on_message(Command("tdtop") & command_filter)
@warned_user_filter
@capture_and_handle_error
async def cmd_tdtop(client: Client, message: Message):
    fetching_msg = await message.reply("🔄 **ғᴇᴛᴄʜɪɴɢ ᴛᴏᴅᴀʏ's ʟᴇᴀᴅᴇʀʙᴏᴀʀᴅ ᴅᴇᴛᴀɪʟs...**")

    td_smashes = await fetch_today_top_collectors()


    leaderboard_text = "🌟 **Today's Top 10 Collectors** 🌟\n\n"
    for index, entry in enumerate(td_smashes, start=1):
        first_name = entry.get("first_name")  
        if not first_name:
            continue  
            
        user_id = entry["user_id"]
        

        try:

            if not isinstance(user_id, int) or user_id > 9999999999:

                mention = f"{first_name}"
            else:
                mention = f"[{first_name}](tg://user?id={user_id})"
        except Exception as e:
            print(f"Error creating mention for user {user_id}: {e}")
            mention = f"{first_name}"

        leaderboard_text += f"**{index}.** {mention} —> **{entry['smash_count']} Collected**\n"

    await fetching_msg.delete()
    await message.reply(leaderboard_text)


@app.on_message(Command("rtop") & filters.group & command_filter)
@warned_user_filter
@capture_and_handle_error
async def cmd_rtop(client: Client, message: Message):
    fetching_msg = await message.reply("🔄 **ғᴇᴛᴄʜɪɴɢ ɢʀᴀʙᴛᴏᴋᴇɴ ʟᴇᴀᴅᴇʀʙᴏᴀʀᴅ...**")

    # Fetch all member IDs in the group chat
    members = client.get_chat_members(message.chat.id)
    member_ids = [member.user.id async for member in members]

    # Fetch grabtoken leaderboard data from db2
    leaderboard_data = await fetch_grabtoken_leaderboard(member_ids)

    # Update leaderboard with user names from the database with validation
    leaderboard = []
    for entry in leaderboard_data:
        if not entry.get("user_name"):
            continue
            
        user_id = entry["_id"]
        # Validate user ID to prevent invalid peer ID errors
        try:
            # Check if user ID is valid (not too large)
            if not isinstance(user_id, int) or user_id > 9999999999:
                # Use plain text instead of mention for invalid IDs
                mention = f"{entry['user_name']}"
            else:
                mention = f"[{entry['user_name']}](tg://user?id={user_id})"
                
            leaderboard.append({
                "user_id": user_id,
                "mention": mention,
                "total_grabtokens": entry["total_grabtokens"],
            })
        except Exception as e:
            print(f"Error processing user {user_id}: {e}")
            # Still include the user but without a clickable mention
            leaderboard.append({
                "user_id": user_id,
                "mention": f"{entry['user_name']}",
                "total_grabtokens": entry["total_grabtokens"],
            })

    # Generate the leaderboard text for grabtokens
    group_name = message.chat.title if message.chat.title else "Group"
    leaderboard_text = f"{'-' * 4} 💸 **{group_name}'s Top 10 Collectors** 💸 {'-' * 14}\n\n"
    
    medals = ["🥇", "🥈", "🥉"]

    for index, entry in enumerate(leaderboard, start=1):
        rank = medals[index - 1] if index <= 3 else f"**{index}**"  # Use bold for ranks beyond 3rd place
        
        # Add each user's rank, mention, and total grabtokens
        leaderboard_text += f"**{rank}** {entry['mention']} ➣ **{entry['total_grabtokens']}** grabtokens\n"
        if index == 3:
            leaderboard_text += "\n"  # Add space after top 3

    await fetching_msg.delete()
    await message.reply(leaderboard_text)

@app.on_message(Command("rgtop") & command_filter)
@warned_user_filter
@capture_and_handle_error
async def cmd_rgtop(client: Client, message: Message):
    fetching_msg = await message.reply("🔄 **ғᴇᴛᴄʜɪɴɢ ɢʟᴏʙᴀʟ ɢʀᴀʙᴛᴏᴋᴇɴ ʟᴇᴀᴅᴇʀʙᴏᴀʀᴅ...**")

    # Fetch global grabtoken leaderboard data from db2 (no member filtering for global)
    leaderboard_data = await fetch_grabtoken_leaderboard()

    # Update leaderboard with user names from the database with validation
    leaderboard = []
    for entry in leaderboard_data:
        if not entry.get("user_name"):
            continue
            
        user_id = entry["_id"]
        # Validate user ID to prevent invalid peer ID errors
        try:
            # Check if user ID is valid (not too large)
            if not isinstance(user_id, int) or user_id > 9999999999:
                # Use plain text instead of mention for invalid IDs
                mention = f"{entry['user_name']}"
            else:
                mention = f"[{entry['user_name']}](tg://user?id={user_id})"
                
            leaderboard.append({
                "user_id": user_id,
                "mention": mention,
                "total_grabtokens": entry["total_grabtokens"],
            })
        except Exception as e:
            print(f"Error processing user {user_id}: {e}")
            # Still include the user but without a clickable mention
            leaderboard.append({
                "user_id": user_id,
                "mention": f"{entry['user_name']}",
                "total_grabtokens": entry["total_grabtokens"],
            })

    # Generate the leaderboard text for global grabtoken leaderboard
    leaderboard_text = f"{'-' * 4} 🌍 **Global Top 10 Collectors** 🌍 {'-' * 14}\n\n"
    
    medals = ["🥇", "🥈", "🥉"]

    for index, entry in enumerate(leaderboard, start=1):
        rank = medals[index - 1] if index <= 3 else f"**{index}**"  # Use bold for ranks beyond 3rd place
        
        # Add each user's rank, mention, and total grabtokens
        leaderboard_text += f"**{rank}** {entry['mention']} ➣ **{entry['total_grabtokens']}** grabtokens\n"
        if index == 3:
            leaderboard_text += "\n"  # Add space after top 3

    await fetching_msg.delete()
    await message.reply(leaderboard_text)


@app.on_message(Command("btop") & command_filter & og_filter)
@warned_user_filter
@capture_and_handle_error
async def cmd_btop(client: Client, message: Message):
    fetching_msg = await message.reply("🔄 **Fetching global bank leaderboard...**")

    # Fetch global bank leaderboard data
    leaderboard_data = await fetch_bank_leaderboard()

    # Prepare leaderboard entries with validation for user IDs
    leaderboard = []
    for entry in leaderboard_data:
        if not entry.get("user_name"):
            continue
            
        user_id = entry["user_id"]
        # Validate user ID to prevent invalid peer ID errors
        try:
            # Check if user ID is valid (not too large)
            if not isinstance(user_id, int) or user_id > 9999999999:
                # Use plain text instead of mention for invalid IDs
                mention = f"{entry['user_name']}"
            else:
                mention = f"[{entry['user_name']}](tg://user?id={user_id})"
                
            leaderboard.append({
                "user_id": user_id,
                "mention": mention,
                "bank_balance": entry["bank_balance"],
            })
        except Exception as e:
            print(f"Error processing user {user_id}: {e}")
            # Still include the user but without a clickable mention
            leaderboard.append({
                "user_id": user_id,
                "mention": f"{entry['user_name']}",
                "bank_balance": entry["bank_balance"],
            })

    # Generate the leaderboard text
    leaderboard_text = (
        f"{'-' * 4} 🏦 **Global Top 25 Bank Balances** 🏦 {'-' * 10}\n\n"
    )
    
    medals = ["🥇", "🥈", "🥉"]

    for index, entry in enumerate(leaderboard, start=1):
        rank = medals[index - 1] if index <= 3 else f"**{index}**"
        leaderboard_text += f"{rank}) {entry['mention']} ➣ **{entry['bank_balance']}**\n"
        
        # Add a separator after the top 3
        if index == 3:
            leaderboard_text += "\n"

    await fetching_msg.delete()
    await message.reply(leaderboard_text)
    

async def daily_rewards_handler():
    # Get IST timezone
    ist = timezone("Asia/Kolkata")
    today_ist = datetime.now(ist).date().isoformat()
    
    # Fetch top 10 collectors for IST date
    top_collectors = await fetch_today_top_collectors()

    if not top_collectors:
        return

    # Reward amounts for top 10 collectors
    rewards = [300000, 275000, 250000, 225000, 200000, 175000, 150000, 125000, 100000, 75000]
    winners = []
    
    for idx, collector in enumerate(top_collectors):
        user_id = collector["user_id"]
        first_name = await get_user_name(user_id) or "Anonymous"
        
        # Award grab tokens using the corresponding reward for the rank
        await add_grab_token(user_id, rewards[idx], first_name)
        
        # Create mention markup for the announcement with validation
        try:
            # Check if user ID is valid (not too large)
            if not isinstance(user_id, int) or user_id > 9999999999:
                # Use plain text instead of mention for invalid IDs
                mention = f"{first_name}"
            else:
                mention = f"[{first_name}](tg://user?id={user_id})"
        except Exception as e:
            print(f"Error creating mention for user {user_id}: {e}")
            mention = f"{first_name}"
            
        winners.append({
            "rank": idx + 1,
            "mention": mention,
            "amount": rewards[idx]
        })

    # Prepare announcement message
    announcement = "🎉 **Daily Leaderboard Results** 🎉\n\n"
    announcement += "**Top Collectors of the Day:**\n\n"
    
    for winner in winners:
        ordinal = {1: "st", 2: "nd", 3: "rd"}.get(winner["rank"], "th")
        announcement += f"🏅 **{winner['rank']}{ordinal} Place:** {winner['mention']} - {winner['amount']:,} Grab Tokens\n"
    
    announcement += "\nCongratulations to the winners! 🎊\nYour rewards have been added to your balances!"

    # Send and pin announcement in the support chat
    support_chat_id = SUPPORT_CHAT_ID
    try:
        msg = await app.send_message(support_chat_id, announcement)
        await msg.pin(disable_notification=False)
    except Exception as e:
        print(f"Error sending announcement: {e}")

async def daily_grab_token_inspection():
    """Send daily Grab Token collection report for inspection"""
    # Get IST timezone
    ist = timezone("Asia/Kolkata")
    today_ist = datetime.now(ist).date().isoformat()
    
    # Fetch all today's collectors sorted by daily tokens
    collectors = await fetch_top_grabtoken_users_today(today_ist)

    if not collectors:
        report = "📊 **Daily Grab Token Report** 📊\n\nNo collections recorded today."
    else:
        report = f"📊 **Daily Grab Token Report - {today_ist}** 📊\n\n"
        report += "**Top Collectors Today:**\n\n"
        
        for idx, collector in enumerate(collectors[:25]):  # Show top 25
            user_name = collector.get("user_name", "Anonymous")
            user_id = collector["user_id"]
            tokens = collector["daily_tokens"]
            
            # Create mention with validation
            try:
                # Check if user ID is valid (not too large)
                if not isinstance(user_id, int) or user_id > 9999999999:
                    # Use plain text instead of mention for invalid IDs
                    user_mention = f"{user_name}"
                else:
                    user_mention = f"[{user_name}](tg://user?id={user_id})"
            except Exception as e:
                print(f"Error creating mention for user {user_id}: {e}")
                user_mention = f"{user_name}"
            
            report += (
                f"🔹 `#{idx+1:02d}` {user_mention}\n"
                f"   ➔ Collected: {tokens:,} Grab Tokens\n\n"
            )

        report += "🔍 _This is an automated daily inspection report_"

    # Send and pin in inspection channel
    try:
        msg = await app.send_message(GLOG, report)
        await msg.pin(disable_notification=True)
    except Exception as e:
        print(f"Failed to send inspection report: {e}")

