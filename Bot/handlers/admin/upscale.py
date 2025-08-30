import os
from Bot import app , Command
from Bot.utils import getFile, UpscaleImages , admin_filter

@app.on_message(Command("upscale") & admin_filter)
async def upscaleImages(_, message):
    # Get the image file from the reply
    file = await getFile(message)
    if file is None:
        return await message.reply_text("Reply to an image to upscale it.")
    
    # Notify the user that the upscaling is in progress
    msg = await message.reply("Upscaling your image...")

    # Read the image bytes and remove the temporary file
    with open(file, "rb") as f:
        imageBytes = f.read()
    os.remove(file)
    
    # Perform the upscaling
    try:
        upscaledImage = await UpscaleImages(imageBytes)
        # Send the upscaled image to the user
        await message.reply_document(open(upscaledImage, "rb"), caption=f"ɪᴍᴀɢᴇ ᴜᴘꜱᴄᴀʟᴇᴅ ꜱᴜᴄᴄᴇꜱꜰᴜʟʟʏ")
        await msg.delete()
        # Remove the upscaled image file after sending
        os.remove(upscaledImage)
    except Exception as e:
        # Notify the user in case of an error
        await msg.edit(f"Failed to upscale the image: {e}")
