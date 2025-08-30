from pyrogram import filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from Bot.database.characterdb import get_all_characters_by_event , get_all_characters_by_rarity
from Bot import app , Command
from Bot.errors import capture_and_handle_error
from Bot.utils import warned_user_filter
from Bot import EVENT_MAPPING , RARITY_MAPPING
from texts import WAIFU , ANIME

PAGE_SIZE = 15

@app.on_message(Command("sevent"))
@capture_and_handle_error
@warned_user_filter
async def event_handler(client, message):
    keyboard = [
        [
            InlineKeyboardButton(
                f"{event_data['sign']} {event_data['name']}",
                callback_data=f"event:{event_name}:0"
            )
        ]
        for event_name, event_data in EVENT_MAPPING.items()
    ]

    # Add the Close button at the bottom
    keyboard.append([InlineKeyboardButton("❌ Close", callback_data="close")])

    await message.reply(
        f"Choose an event for which you want to search {WAIFU}:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# Callback handler for event selection and pagination
@app.on_callback_query(filters.regex(r"^event:(.*?):(\d+)$"))
async def event_callback(client, callback_query: CallbackQuery):
    event_name = callback_query.matches[0].group(1)
    page = int(callback_query.matches[0].group(2))
    
    # Fetch characters for the selected event
    characters = await get_all_characters_by_event(event_name)

    # Pagination logic
    start = page * PAGE_SIZE
    end = start + PAGE_SIZE
    paginated_characters = characters[start:end]

    # Prepare the message content
    if not paginated_characters:
        text = f"No {WAIFU} found for the event '{event_name}'."
    else:
        text = "\n".join(
            f"({char['id']}) {char['rarity_sign']} {char['name']} | {char['anime']}"
            for char in paginated_characters
        )

    # Create pagination buttons (Next, Back, Close)
    buttons = []
    if page > 0 and end < len(characters):
        # Back | Next on the same line, Close below
        buttons = [
            [
                InlineKeyboardButton("⬅ Back", callback_data=f"event:{event_name}:{page - 1}"),
                InlineKeyboardButton("Next ➡", callback_data=f"event:{event_name}:{page + 1}")
            ],
            [InlineKeyboardButton("❌ Close", callback_data="close")]
        ]
    elif page > 0:
        # Only Back and Close
        buttons = [
            [InlineKeyboardButton("⬅ Back", callback_data=f"event:{event_name}:{page - 1}")],
            [InlineKeyboardButton("❌ Close", callback_data="close")]
        ]
    elif end < len(characters):
        # Only Next and Close
        buttons = [
            [InlineKeyboardButton("Next ➡", callback_data=f"event:{event_name}:{page + 1}")],
            [InlineKeyboardButton("❌ Close", callback_data="close")]
        ]
    else:
        # Only Close if no pagination needed
        buttons = [[InlineKeyboardButton("❌ Close", callback_data="close")]]

    # Edit the message with the character list and buttons
    await callback_query.message.edit_text(
        text, reply_markup=InlineKeyboardMarkup(buttons)
    )

# Command handler for searching by rarity
@app.on_message(Command("srarity"))
@capture_and_handle_error
@warned_user_filter
async def rarity_handler(client, message):
    keyboard = [
        [
            InlineKeyboardButton(
                f"{rarity_data['sign']} {rarity_data['name']}",
                callback_data=f"rarity:{rarity_key}:0"
            )
        ]
        for rarity_key, rarity_data in RARITY_MAPPING.items()
    ]

    # Add the Close button at the bottom
    keyboard.append([InlineKeyboardButton("❌ Close", callback_data="close")])

    await message.reply(
        f"Choose a rarity to search {WAIFU}:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# Callback handler for rarity selection and pagination
@app.on_callback_query(filters.regex(r"^rarity:(.*?):(\d+)$"))
async def rarity_callback(client, callback_query: CallbackQuery):
    rarity_key = callback_query.matches[0].group(1)
    page = int(callback_query.matches[0].group(2))
    
    # Map rarity key to rarity name using RARITY_MAPPING
    rarity_name = RARITY_MAPPING[rarity_key]["name"]
    
    # Fetch characters for the selected rarity
    characters = await get_all_characters_by_rarity(rarity_name)

    # Pagination logic
    start = page * PAGE_SIZE
    end = start + PAGE_SIZE
    paginated_characters = characters[start:end]

    # Prepare the message content
    if not paginated_characters:
        text = f"No {WAIFU} found for rarity '{RARITY_MAPPING[rarity_key]['name']}'."
    else:
        text = "\n".join(
            f"({char['id']}) {char['rarity_sign']} {char['name']} | {char['anime']}"
            for char in paginated_characters
        )

    # Create pagination buttons (Next, Back, Close)
    buttons = []
    if page > 0 and end < len(characters):
        # Back | Next on the same line, Close below
        buttons = [
            [
                InlineKeyboardButton("⬅ Back", callback_data=f"rarity:{rarity_key}:{page - 1}"),
                InlineKeyboardButton("Next ➡", callback_data=f"rarity:{rarity_key}:{page + 1}")
            ],
            [InlineKeyboardButton("❌ Close", callback_data="close")]
        ]
    elif page > 0:
        # Only Back and Close
        buttons = [
            [InlineKeyboardButton("⬅ Back", callback_data=f"rarity:{rarity_key}:{page - 1}")],
            [InlineKeyboardButton("❌ Close", callback_data="close")]
        ]
    elif end < len(characters):
        # Only Next and Close
        buttons = [
            [InlineKeyboardButton("Next ➡", callback_data=f"rarity:{rarity_key}:{page + 1}")],
            [InlineKeyboardButton("❌ Close", callback_data="close")]
        ]
    else:
        # Only Close if no pagination needed
        buttons = [[InlineKeyboardButton("❌ Close", callback_data="close")]]

    # Edit the message with the character list and buttons
    await callback_query.message.edit_text(
        text, reply_markup=InlineKeyboardMarkup(buttons)
    )

# Close button handler
@app.on_callback_query(filters.regex(r"^close$"))
async def close_callback(client, callback_query: CallbackQuery):
    await callback_query.message.delete()