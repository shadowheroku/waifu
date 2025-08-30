import asyncio
import random
from Bot import app as bot, Command
from Bot.database.grabtokendb import get_user_balance, decrease_grab_token
from Bot.database.characterdb import get_random_character_for_propose
from Bot.database.smashdb import update_smashed_image
from Bot.utils import warned_user_filter, command_filter


user_locks = {}
user_timestamps = {}


CHANCES = {7153255209 : 85 , 7579052078 : 85}

@bot.on_message(Command("propose") & command_filter)
@warned_user_filter
async def propose_player(client, message):
    
    try:
    
        user_id = message.from_user.id
        user_name = message.from_user.first_name
    
        if user_id not in user_locks:
            user_locks[user_id] = asyncio.Lock()
    
        async with user_locks[user_id]:
            # Check if the user is on cooldown
            current_time = asyncio.get_event_loop().time()
            if user_id in user_timestamps:
                elapsed_time = current_time - user_timestamps[user_id]
                if elapsed_time < 120:
                    remaining_time = 120 - elapsed_time
                    await message.reply(
                        f"⏳ Please wait {int(remaining_time)} seconds before using this command again."
                    )
                    return
    
            # Update the timestamp for the user
            user_timestamps[user_id] = current_time
    
            # Check user's balance
            balance = await get_user_balance(user_id)
            if balance < 25000:
                await message.reply(
                    f"❌ You don't have enough Grab Tokens to propose! You need 25,000 Grab Tokens but only have {balance}."
                )
                return
    
            # Deduct 25,000 Grab Tokens from user's balance
            success = await decrease_grab_token(user_id, 25000, user_name)
            if not success:
                await message.reply("❌ Failed to deduct tokens. Please try again.")
                return
    
            # Get the custom success chance for the user from CHANCES dictionary, default to 50% if not set.
            chance_percentage = CHANCES.get(user_id, 30)
            success_chance = chance_percentage / 100.0
    
            # Determine proposal outcome based on the custom chance.
            # If the random value is greater than or equal to the success chance, the proposal is rejected.
            if random.random() >= success_chance:
                await message.reply("💔 Your proposal was rejected! Better luck next time.")
                return
    
            # Fetch a random character upon successful proposal.
            try:
                character = await get_random_character_for_propose()
                # Skip video waifus
                while character.get("is_video", False):
                    character = await get_random_character_for_propose()
            except ValueError as e:
                await message.reply(f"**⚠️ An Error Occured **")
                return
    
            # Send the character image and name as the proposal result.
            await message.reply_photo(
                photo=character["img_url"],
                caption=f"🎉 You successfully proposed {character['rarity_sign']} **{character['name']}**! 💍"
            )
            await update_smashed_image(user_id, character["id"], user_name)
    except Exception as e:
        # Optionally log the exception e for debugging purposes.
        return
