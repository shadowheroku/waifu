from pyrogram import filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from Bot.database.characterdb import get_all_images
from collections import defaultdict
from Bot import app , Command
from Bot.config import OWNERS
from Bot.errors import capture_and_handle_error
from texts import WAIFU

CHARACTERS_PER_PAGE = 15

def generate_character_list_message(characters, page):
    """Generate the character list message for the given page."""
    start_index = page * CHARACTERS_PER_PAGE
    end_index = start_index + CHARACTERS_PER_PAGE
    characters_on_page = characters[start_index:end_index]

    message = "\n".join(
        [f"({char['id']}) {char['rarity_sign']} {char['name']} | {char['anime']}" 
         for char in characters_on_page]
    )

    if not message:
        message = f"No {WAIFU} found on this page."

    return message

def generate_pagination_buttons(page, total_pages):
    """Generate inline buttons for pagination."""
    buttons = [
        [
            InlineKeyboardButton("⬅️ Back", callback_data=f"chara_page_{page - 1}") if page > 0 else None,
            InlineKeyboardButton("➡️ Next", callback_data=f"chara_page_{page + 1}") if page < total_pages - 1 else None,
        ],
        [InlineKeyboardButton("❌ Close", callback_data="chara_close")]
    ]

    # Remove None values (for the first or last page cases)
    buttons = [[button for button in row if button] for row in buttons]

    return InlineKeyboardMarkup(buttons)

@app.on_message(Command("allplayers") & filters.private & filters.user(OWNERS))  # Replace YOUR_USER_ID
@capture_and_handle_error
async def send_character_list(client, message):
    """Command to send the first page of characters."""
    characters = await get_all_images()
    total_pages = (len(characters) + CHARACTERS_PER_PAGE - 1) // CHARACTERS_PER_PAGE

    text = generate_character_list_message(characters, page=0)
    buttons = generate_pagination_buttons(page=0, total_pages=total_pages)

    await message.reply_text(text, reply_markup=buttons)

@app.on_callback_query(filters.regex(r"^chara_page_(\d+)$"))
@capture_and_handle_error
async def handle_pagination(client, query: CallbackQuery):
    """Handle pagination through callback queries."""
    page = int(query.data.split("_")[2])

    characters = await get_all_images()
    total_pages = (len(characters) + CHARACTERS_PER_PAGE - 1) // CHARACTERS_PER_PAGE

    if 0 <= page < total_pages:
        text = generate_character_list_message(characters, page)
        buttons = generate_pagination_buttons(page, total_pages)

        await query.message.edit_text(text, reply_markup=buttons)
    else:
        await query.answer("Invalid page number.", show_alert=True)

@app.on_callback_query(filters.regex("^chara_close$"))
@capture_and_handle_error
async def close_character_list(client, query: CallbackQuery):
    """Close the character list message."""
    await query.message.delete()

@app.on_message(Command("dupecheck") & filters.user(OWNERS))  # Replace YOUR_USER_ID
@capture_and_handle_error
async def find_duplicate_images(client, message):
    """Command to find characters with duplicate img_urls."""
    characters = await get_all_images()

    # Group characters by img_url
    url_to_characters = defaultdict(list)
    for char in characters:
        url_to_characters[char["img_url"]].append(char)

    # Find duplicates (more than one character with the same img_url)
    duplicates = {url: chars for url, chars in url_to_characters.items() if len(chars) > 1}

    if not duplicates:
        await message.reply_text(f"No duplicate {WAIFU} found.")
        return

    # Generate the result message
    result = f"Duplicate {WAIFU} Found:\n\n"
    for url, chars in duplicates.items():
        result += f"Image URL: {url}\n"
        for char in chars:
            result += f"({char['id']}) {char['rarity_sign']} {char['name']} | {char['anime']}\n"
        result += "\n"

    # Send the result as a message (split if too long)
    if len(result) > 4096:  # Telegram's message length limit
        for chunk in [result[i:i + 4096] for i in range(0, len(result), 4096)]:
            await message.reply_text(chunk)
    else:
        await message.reply_text(result)


