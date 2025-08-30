import random
from typing import Dict, Optional, Any
import aiohttp
import io
from PIL import Image

# shared.py
pending_gifts: Dict[int, bool] = {}
pending_trades: Dict[int, str] = {}
message_counts: Dict[str, Dict[str, int]] = {}
pending_mass_gifts: Dict[int, Dict[str, Any]] = {}
drop_details: Dict[str, Dict[str, Any]] = {}
lang_code: Dict[int, str] = {}
chat_lang_code: Dict[str, str] = {}

async def update_drop(
    group_id: str, 
    image_id: str, 
    image_name: str, 
    image_url: str, 
    dropped_image_link: Optional[str] = None, 
    smashed_by: Optional[str] = None
) -> None:
    """Update drop details for a specific group."""
    drop_details[group_id] = {
        "image_id": image_id,
        "image_name": image_name,
        "image_url": image_url,
        "dropped_image_link": dropped_image_link,
        "smashed_by": smashed_by
    }

async def get_drop(group_id: str) -> Optional[Dict[str, Any]]:
    """Get drop details for a specific group."""
    return drop_details.get(group_id)

async def update_message_count(group_id: str, msg_count: int, current_count: int) -> None:
    """Update message count for a specific group."""
    message_counts[group_id] = {
        "msg_count": msg_count,
        "current_count": current_count
    }

async def get_message_count(group_id: str) -> Optional[Dict[str, int]]:
    """Get message count for a specific group."""
    return message_counts.get(group_id)



def clear_pending_operations(user_id: int) -> None:
    """Clear all pending operations for a user."""
    if user_id in pending_gifts:
        del pending_gifts[user_id]
    if user_id in pending_trades:
        del pending_trades[user_id]
    if user_id in pending_mass_gifts:
        del pending_mass_gifts[user_id]

import aiohttp
import io
import random
from typing import Optional
from PIL import Image

async def modify_image_for_unique_id(image_url: str) -> Optional[io.BytesIO]:

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36"
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(image_url, headers=headers) as response:
                if response.status == 200:
                    image_data = await response.read()
                    image = Image.open(io.BytesIO(image_data))
                    
                    # Make a tiny, imperceptible modification to the image
                    width, height = image.size
                    x = random.randint(0, width - 1)
                    y = random.randint(0, height - 1)
                    pixel = list(image.getpixel((x, y)))
                    
                    # Change one color channel slightly
                    channel = random.randint(0, len(pixel) - 1)
                    pixel[channel] = max(0, min(255, pixel[channel] + random.choice([-1, 1])))
                    
                    image.putpixel((x, y), tuple(pixel))
                    
                    # Save to bytes
                    img_byte_arr = io.BytesIO()
                    image.save(img_byte_arr, format=image.format or 'PNG')
                    img_byte_arr.seek(0)
                    
                    return img_byte_arr
                else:
                    print(f"Failed to download image: {response.status}")
                    return None
    except Exception as e:
        print(f"Error modifying image: {e}")
        return None
