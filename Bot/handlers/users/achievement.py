from pyrogram import filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from Bot import app , Command
from Bot.database.characterdb import get_random_character 
from Bot.database.smashdb import get_smash_count_data , update_smashed_image 
from Bot.database.userdb import get_claimed_achievements , update_claimed_achievements
from Bot.errors import capture_and_handle_error
from Bot.utils import warned_user_filter


smash_milestones = [1, 10, 50, 100, 250, 500, 1000, 2500, 5000 , 10000]

active_claims = set()

@app.on_message(Command("achievement"))
@capture_and_handle_error
@warned_user_filter
async def achievement_list(client, message):
    user_id = message.from_user.id

    # Display the achievement list
    buttons = [
        [InlineKeyboardButton("ᴄᴏʟʟᴇᴄᴛɪᴏɴ ᴄᴏᴜɴᴛ", callback_data=f"show_achievements|{user_id}")]
    ]
    await message.reply_text("ʜᴇʀᴇ ɪs ʏᴏᴜʀ ᴀᴄʜɪᴇᴠᴇᴍᴇɴᴛ ʟɪsᴛ!\nɢᴇᴛ ʀᴇᴡᴀʀᴅs ғᴏʀ ʏᴏᴜʀ ᴀᴄʜɪᴇᴠᴇᴍᴇɴᴛs ʙʏ ᴄʟɪᴄᴋɪɴɢ ᴛʜᴇ ʙᴜᴛᴛᴏɴs ʙᴇʟᴏᴡ!!", reply_markup=InlineKeyboardMarkup(buttons))


@app.on_callback_query(filters.regex(r"^show_achievements\|(\d+)"))
@capture_and_handle_error
async def show_achievements(client, query):
    user_id = int(query.data.split('|')[1])


    if query.from_user.id != user_id:
        await query.answer("ᴛʜɪs ɪs ɴᴏᴛ ʏᴏᴜʀ ᴀᴄʜɪᴇᴠᴇᴍᴇɴᴛ ʟɪsᴛ!", show_alert=True)
        return

    first_name = query.from_user.first_name


    user_smash_data = await get_smash_count_data(user_id)
    smash_count = user_smash_data["smash_count"] if user_smash_data else 0


    user_achievements = await get_claimed_achievements(user_id)
    claimed_rewards = user_achievements["claimed"] if user_achievements else []


    buttons = []
    for milestone in smash_milestones:
        smashes_button = InlineKeyboardButton(f"🏆 {milestone} ᴄᴏʟʟᴇᴄᴛɪᴏɴꜱ", callback_data="no_action")
        if smash_count >= milestone:
            if milestone in claimed_rewards:
                claim_button = InlineKeyboardButton("✅", callback_data=f"claimed|{milestone}")
            else:
                claim_button = InlineKeyboardButton("ᴄʟᴀɪᴍ", callback_data=f"claim_reward|{milestone}|{user_id}")
        else:
            claim_button = InlineKeyboardButton("ᴄʟᴀɪᴍ", callback_data="no_claim")

        buttons.append([smashes_button, claim_button])

    await query.message.edit_text(f"{first_name}, ʜᴇʀᴇ ɪs ʏᴏᴜʀ ᴀᴄʜɪᴇᴠᴇᴍᴇɴᴛ ʟɪsᴛ!!", reply_markup=InlineKeyboardMarkup(buttons))


@app.on_callback_query(filters.regex(r"^claim_reward\|(\d+)\|(\d+)"))
@capture_and_handle_error
async def claim_reward(client, query):
    milestone = int(query.data.split('|')[1])
    user_id = int(query.data.split('|')[2])
    first_name = query.from_user.first_name

    # Prevent others from claiming rewards for the original user
    if query.from_user.id != user_id:
        await query.answer("ᴛʜɪs ɪs ɴᴏᴛ ʏᴏᴜ ǫᴜᴇʀʏ!!", show_alert=True)
        return

    # Check if the user is already claiming a reward
    if user_id in active_claims:
        await query.answer("ʏᴏᴜ ᴀʀᴇ ᴀʟʀᴇᴀᴅʏ ᴄʟᴀɪᴍɪɴɢ ᴀ ʀᴇᴡᴀʀᴅ. ᴘʟᴇᴀsᴇ ᴡᴀɪᴛ!", show_alert=True)
        return

    # Add the user to the active claims set to lock the process
    active_claims.add(user_id)

    try:
        # Fetch user's smash count
        user_smash_data = await get_smash_count_data(user_id)
        smash_count = user_smash_data["smash_count"] if user_smash_data else 0

        if smash_count < milestone:
            await query.answer("ʏᴏᴜ ʜᴀᴠᴇɴ'ᴛ ʀᴇᴀᴄʜᴇᴅ ᴛʜɪs ᴍɪʟᴇsᴛᴏɴᴇ ʏᴇᴛ!", show_alert=True)
            return

        # Check if already claimed
        user_achievements = await get_claimed_achievements(user_id)
        claimed_rewards = user_achievements["claimed"] if user_achievements else []

        if milestone in claimed_rewards:
            await query.answer("ʏᴏᴜ ᴀʟʀᴇᴀᴅʏ ᴄʟᴀɪᴍᴇᴅ ᴛʜɪs ʀᴇᴡᴀʀᴅ!", show_alert=True)
            return

        # Claim reward logic
        num_characters = get_reward_character_count(milestone)
        character_ids = []
        for _ in range(num_characters):
            character = await get_random_character()
            character_ids.append(character["id"])
            await update_smashed_image(user_id, character["id"], query.from_user.first_name)

        # Update claimed achievements
        claimed_rewards.append(milestone)
        await update_claimed_achievements(user_id, claimed_rewards)

        # Fetch the current inline keyboard
        current_keyboard = query.message.reply_markup.inline_keyboard

        # Update only the "Claim" button for this specific milestone to "✅"
        for button_row in current_keyboard:
            if button_row[1].callback_data == f"claim_reward|{milestone}|{user_id}":
                button_row[1] = InlineKeyboardButton("✅", callback_data=f"claimed|{milestone}")

        # Update the entire keyboard with the updated "Claim" button
        await query.message.edit_reply_markup(reply_markup=InlineKeyboardMarkup(current_keyboard))

        # Send a message to the user with the character details
        character_message = f"**{first_name} ɢᴏᴛ ᴡᴀɪғᴜ ᴡɪᴛʜ ɪᴅ : {' '.join(map(str, character_ids))}**"
        await query.message.reply_text(character_message)

        await query.answer(f"sᴜᴄᴄᴇssғᴜʟʟʏ ᴄʟᴀɪᴍᴇᴅ {milestone} ᴄᴏʟʟᴇᴄᴛɪᴏɴꜱ ʀᴇᴡᴀʀᴅ!", show_alert=True)

    finally:
        active_claims.discard(user_id)

def get_reward_character_count(milestone):
    reward_table = {
        1: 1,
        10: 1,
        50: 2,
        100: 3,
        250: 4,
        500: 5,
        1000: 7,
        2500: 8,
        5000: 10
    }
    return reward_table.get(milestone, 1)
