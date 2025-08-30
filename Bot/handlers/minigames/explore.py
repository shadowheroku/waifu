from pyrogram import filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
import random
from asyncio import Lock
from datetime import datetime
from Bot.database.grabtokendb import add_grab_token
from Bot import app as bot, COUNTRY_MAPPING , Command
from Bot.utils import warned_user_filter , command_filter

# Existing cooldown configuration
cooldown_time = 300  # 5 minutes in seconds
last_explore_time = {}
last_explore_callback_time = {}
explore_lock = {}
btn_lock = {}

# Daily exploration limit storage
user_daily_explores = {}  # Format: {user_id: {'date': 'YYYY-MM-DD', 'count': int}}

@bot.on_message(Command("explore") & command_filter)
@warned_user_filter
async def explore_country(client, message):
    try:
        user_id = message.from_user.id
        current_time = datetime.now()

        if user_id not in explore_lock:
            explore_lock[user_id] = Lock()

        if user_id in last_explore_time:
            time_diff = (current_time - last_explore_time[user_id]).total_seconds()
            if time_diff < cooldown_time:
                remaining_time = int(cooldown_time - time_diff)
                await message.reply(f"⏳ You can explore again in {remaining_time} seconds. Please wait!")
                return

        async with explore_lock[user_id]:
            last_explore_time[user_id] = current_time
            buttons = [
                [InlineKeyboardButton(f"{data['sign']} {data['name']}", callback_data=f"explore_{country_id}")]
                for country_id, data in COUNTRY_MAPPING.items()
            ]
            await message.reply(
                "🌍 Where do you want to explore?",
                reply_markup=InlineKeyboardMarkup(buttons),
            )
    except:
        return

@bot.on_callback_query(filters.regex(r"^explore_(.+)"))
async def handle_explore_callback(client, callback_query: CallbackQuery):
    if callback_query.from_user.id != callback_query.message.reply_to_message.from_user.id:
        await callback_query.answer("This Button Is Not For You!!", show_alert=True)
        return
    
    try:
        await callback_query.message.delete()
        user_id = callback_query.from_user.id
        current_time = datetime.now()
        
        if user_id not in btn_lock:
            btn_lock[user_id] = Lock()

        async with btn_lock[user_id]:
            # Daily limit check
            current_date = current_time.strftime("%Y-%m-%d")
            if user_id in user_daily_explores:
                user_data = user_daily_explores[user_id]
                if user_data['date'] == current_date and user_data['count'] >= 20:
                    await callback_query.answer(
                        "**❌ Daily limit reached! You can explore 20 times per day. Come back tomorrow !**",
                        show_alert=True
                    )
                    return

            # Cooldown check
            if user_id in last_explore_callback_time:
                time_diff = (current_time - last_explore_callback_time[user_id]).total_seconds()
                if time_diff < cooldown_time:
                    remaining_time = int(cooldown_time - time_diff)
                    await callback_query.answer(
                        f"⏳ Please wait! You can explore again in {remaining_time} seconds.",
                        show_alert=True
                    )
                    return

            # Update exploration count
            current_date = current_time.strftime("%Y-%m-%d")
            if user_id not in user_daily_explores:
                user_daily_explores[user_id] = {'date': current_date, 'count': 1}
            else:
                user_data = user_daily_explores[user_id]
                if user_data['date'] != current_date:
                    user_daily_explores[user_id] = {'date': current_date, 'count': 1}
                else:
                    user_daily_explores[user_id]['count'] += 1

            # Update cooldown
            last_explore_callback_time[user_id] = current_time

            # Exploration logic
            country_id = callback_query.data.split("_", 1)[1]
            user_name = callback_query.from_user.first_name

            if country_id not in COUNTRY_MAPPING:
                await callback_query.answer("❌ Invalid country selection!", show_alert=True)
                return

            country_info = COUNTRY_MAPPING[country_id]
            country_name = country_info["name"]
            country_sign = country_info["sign"]

            if random.random() > 0.8:
                await bot.send_message(
                    chat_id=callback_query.message.chat.id,
                    text=f"🌍 {callback_query.from_user.mention} explored {country_sign} {country_name} but found nothing. Better luck next time!"
                )
                return

            # Reward calculation
            reward_chance = random.random()
            if reward_chance <= 0.78:
                reward = random.randint(100, 599)
            elif reward_chance <= 0.88:
                reward = random.randint(600, 2999)
            elif reward_chance <= 0.98:
                reward = random.randint(2999, 5999)
            else:
                reward = random.randint(5999, 8000)

            await bot.send_message(
                chat_id=callback_query.message.chat.id,
                text=f"🎉 {callback_query.from_user.mention} explored {country_sign} {country_name} and found 💰 {reward} Grabtokens! Keep exploring!"
            )
            await add_grab_token(user_id, reward, user_name)
    except:
        return