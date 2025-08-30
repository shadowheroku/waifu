from Bot import app , Command
from Bot.database import teamdb, smashdb, characterdb , grabtokendb
from pyrogram.types import Message
from pyrogram.enums import ParseMode
from Bot.errors import capture_and_handle_error
from Bot.utils import warned_user_filter
import asyncio
from cachetools import TTLCache
from texts import WAIFU , ANIME

# Cache to store file IDs with a TTL of 1 minute
cache = TTLCache(maxsize=1000000, ttl=60)

MAX_PLAYERS = 10  # Maximum players in a team (excluding captain)
BACKGROUND_URL = "https://ibb.co/njvgXnH"
OUTPUT_DIR = "Bot"  # Directory to save generated images


@app.on_message(Command("maketeam"))
@capture_and_handle_error
@warned_user_filter
async def make_team(client, message: Message):
    args = message.command
    if len(args) < 3:
        await message.reply_text(
            "**Usage:**\n/maketeam <captain_id> <team_name>", parse_mode=ParseMode.MARKDOWN
        )
        return

    # Deduct Grabtoken for renaming
    if not await grabtokendb.decrease_grab_token(user_id, 100000):
        await message.reply_text(
            "⚠️ You need **100,000 Grabtokens** to make your team.", parse_mode=ParseMode.MARKDOWN
        )
        return

    captain_id = str(args[1])  # Ensure captain_id is a string
    team_name = " ".join(args[2:])
    user_id = message.from_user.id

    # Verify if the captain ID is in the user's collection
    user_collection = await smashdb.get_user_collection(user_id)
    if not user_collection or not any(img["image_id"] == captain_id for img in user_collection.get("images", [])):
        await message.reply_text(
            "⚠️ The specified **captain ID** is not in your collection.", parse_mode=ParseMode.MARKDOWN
        )
        return

    # Check if the user already has a team
    existing_team = await teamdb.get_team_by_user(user_id)
    if existing_team:
        await message.reply_text(
            f"⚠️ You already have a team: **{existing_team['team_name']}**.", parse_mode=ParseMode.MARKDOWN
        )
        return

    # Create the team
    await teamdb.create_or_update_team(user_id, team_name=team_name, captain_id=captain_id, players_ids=[])
    await message.reply_text(
        f"✅ Team **'{team_name}'** created successfully with captain ID **{captain_id}**!",
        parse_mode=ParseMode.MARKDOWN,
    )


@app.on_message(Command("add"))
@warned_user_filter
@capture_and_handle_error
async def add_player(client, message: Message):
    args = message.command
    if len(args) < 2:
        await message.reply_text("**Usage:**\n/add {player_id}", parse_mode=ParseMode.MARKDOWN)
        return

    player_id = str(args[1])  # Ensure player_id is a string
    user_id = message.from_user.id

    # Verify if the player ID is in the user's collection
    user_collection = await smashdb.get_user_collection(user_id)
    if not user_collection or not any(img["image_id"] == player_id for img in user_collection.get("images", [])):
        await message.reply_text(
            f"⚠️ The specified **{WAIFU} ID** is not in your collection.", parse_mode=ParseMode.MARKDOWN
        )
        return

    # Fetch the user's team
    team = await teamdb.get_team_by_user(user_id)
    if not team:
        await message.reply_text(
            "⚠️ You don't have a team. Use **/maketeam** to create one first.", parse_mode=ParseMode.MARKDOWN
        )
        return

    # Check if the player is already in the team
    if player_id in team["players_ids"]:
        await message.reply_text(
            f"⚠️ The specified **{WAIFU} ID** is already in your team.", parse_mode=ParseMode.MARKDOWN
        )
        return

    # Check team size
    if len(team["players_ids"]) >= MAX_PLAYERS:
        await message.reply_text(
            f"⚠️ Your team already has the maximum **{MAX_PLAYERS}** {WAIFU}s.", parse_mode=ParseMode.MARKDOWN
        )
        return

    # Add the player to the team
    await teamdb.add_player_to_team(user_id, player_id)

    # Get player details
    player_details = await characterdb.get_character_details(player_id)
    if player_details:
        formatted_details = (
            f"✅ **{WAIFU} Added Successfully!**\n\n"
            f"**Name:** {player_details['name']}\n"
            f"**{ANIME} : {player_details['anime']}\n"
            f"**Rarity:** {player_details.get('rarity', 'Unknown')}"
        )
        await message.reply_text(formatted_details, parse_mode=ParseMode.MARKDOWN)
    else:
        await message.reply_text(f"✅ {WAIFU} ID **{player_id}** added to your team!", parse_mode=ParseMode.MARKDOWN)



@app.on_message(Command("rm"))
@capture_and_handle_error
@warned_user_filter
async def remove_player(client, message: Message):
    args = message.command
    if len(args) < 2:
        await message.reply_text("**Usage:**\n/rm {player_id}", parse_mode=ParseMode.MARKDOWN)
        return

    player_id = str(args[1])  # Ensure player_id is a string
    user_id = message.from_user.id

    # Fetch the user's team
    team = await teamdb.get_team_by_user(user_id)
    if not team:
        await message.reply_text(
            "⚠️ You don't have a team. Use **/maketeam** to create one first.", parse_mode=ParseMode.MARKDOWN
        )
        return

    # Check if the player is in the team
    if player_id not in team["players_ids"]:
        await message.reply_text(
            f"⚠️ The specified **{WAIFU}** is not in your team.", parse_mode=ParseMode.MARKDOWN
        )
        return

    # Remove the player from the team
    await teamdb.remove_player_from_team(user_id, player_id)
    await message.reply_text(
        f"✅ {WAIFU} ID **{player_id}** removed from your team.", parse_mode=ParseMode.MARKDOWN
    )

@app.on_message(Command("myteam"))
@warned_user_filter
@capture_and_handle_error
async def view_team(client, message: Message):
    user_id = message.from_user.id

    # Check cache for existing team details
    if user_id in cache:
        cached_message = cache[user_id]
        await message.reply_text(cached_message, parse_mode=ParseMode.MARKDOWN)
        return

    status_msg = await message.reply_text("**Fetching Your Team Details...**")

    # Fetch the user's team
    team = await teamdb.get_team_by_user(user_id)
    if not team:
        await status_msg.edit(
            "⚠️ You don't have a team. Use **/maketeam** to create one first.",
            parse_mode=ParseMode.MARKDOWN,
        )
        return

    # Fetch team details
    captain_id = team["captain_id"]
    players_ids = team["players_ids"]

    captain_details = await characterdb.get_character_details(captain_id)
    players_details = await asyncio.gather(
        *(characterdb.get_character_details(pid) for pid in players_ids)
    )

    # Create caption
    caption = (
        f"🏆 **Team:** {team['team_name']}\n"
        f"👑 **Captain:** {captain_details['name']} ({captain_details['anime']})\n"
        f"🌟 **Rarity:** {captain_details.get('rarity', 'Unknown')}\n\n"
        f"📋 **{WAIFU}:**\n"
    )
    for idx, player in enumerate(players_details, start=1):
        if player:
            caption += (
                f"**{idx}.** {player['name']} ({player['anime']})\n"
                f"{player.get('rarity_sign', 'Unknown')} **Rarity:** {player.get('rarity', 'Unknown')}\n"
            )

    # Send the result
    sent_message = await message.reply_text(caption, parse_mode=ParseMode.MARKDOWN)

    # Cache the team details
    cache[user_id] = caption

    # Delete the status message
    await status_msg.delete()




@app.on_message(Command("renameteam"))
@warned_user_filter
@capture_and_handle_error
async def rename_team(client, message: Message):
    args = message.command
    if len(args) < 2:
        await message.reply_text("**Usage:**\n/rename <new_team_name>", parse_mode=ParseMode.MARKDOWN)
        return

    new_team_name = " ".join(args[1:])
    user_id = message.from_user.id

    # Deduct Grabtoken for renaming
    if not await grabtokendb.decrease_grab_token(user_id, 50000):
        await message.reply_text(
            "⚠️ You need **50,000 Grabtokens** to rename your team.", parse_mode=ParseMode.MARKDOWN
        )
        return

    # Fetch the user's team
    team = await teamdb.get_team_by_user(user_id)
    if not team:
        await message.reply_text(
            "⚠️ You don't have a team. Use **/maketeam** to create one first.", parse_mode=ParseMode.MARKDOWN
        )
        return

    # Rename the team
    await teamdb.rename_team(user_id, new_team_name)
    await message.reply_text(
        f"✅ Team successfully renamed to **'{new_team_name}'**!", parse_mode=ParseMode.MARKDOWN
    )


@app.on_message(Command("changecaptain"))
@warned_user_filter
@capture_and_handle_error
async def change_captain(client, message: Message):
    args = message.command
    if len(args) < 2:
        await message.reply_text("**Usage:**\n/changecaptain <new_captain_id>", parse_mode=ParseMode.MARKDOWN)
        return

    new_captain_id = str(args[1])  # Ensure new_captain_id is a string
    user_id = message.from_user.id

    # Deduct Grabtoken for changing captain
    if not await grabtokendb.decrease_grab_token(user_id, 30000):
        await message.reply_text(
            "⚠️ You need **30,000 Grabtokens** to change your team captain.", parse_mode=ParseMode.MARKDOWN
        )
        return

    # Fetch the user's team
    team = await teamdb.get_team_by_user(user_id)
    if not team:
        await message.reply_text(
            "⚠️ You don't have a team. Use **/maketeam** to create one first.", parse_mode=ParseMode.MARKDOWN
        )
        return

    # Check if the new captain is in the team
    if new_captain_id not in team["players_ids"]:
        await message.reply_text(
            "⚠️ The specified **captain ID** is not part of your team.", parse_mode=ParseMode.MARKDOWN
        )
        return

    # Change the captain
    await teamdb.change_team_captain(user_id, new_captain_id)
    await message.reply_text(
        f"✅ Team captain successfully changed to **{new_captain_id}**!", parse_mode=ParseMode.MARKDOWN
    )

