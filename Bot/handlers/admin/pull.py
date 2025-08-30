import os
import subprocess
import sys
from pyrogram import filters
from Bot import app , Command
from Bot.config import ADI  
from Bot.errors import capture_and_handle_error
from Bot.on_start import save_restart_data



@app.on_message(Command("pull") & filters.user(ADI))
@capture_and_handle_error
async def git_pull_command(client, message):
    try:
        # Stash local changes to prevent merge conflicts
        subprocess.run(["git", "stash"], check=True)

        result = subprocess.run(
            ["git", "pull", "https://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@github.com/john-wick00/Collect-Football-Player.git", "main"],
            capture_output=True, text=True, check=True
        )
        if "Already up to date" in result.stdout:
            await message.reply("Rᴇᴘᴏ ɪs ᴀʟʀᴇᴀᴅʏ ᴜᴘ ᴛᴏ ᴅᴀᴛᴇ")
        elif result.returncode == 0:
            await message.reply(f"Gɪᴛ ᴘᴜʟʟ sᴜᴄᴄᴇssғᴜʟ. Bᴏᴛ ᴜᴘᴅᴀᴛᴇᴅ.\n\n`{result.stdout}`")
            await restart_bot(message)
        else:
            await message.reply("Gɪᴛ ᴘᴜʟʟ ғᴀɪʟᴇᴅ. Pʟᴇᴀsᴇ ᴄʜᴇᴄᴋ ᴛʜᴇ ʟᴏɢs.")
    except subprocess.CalledProcessError as e:
        await message.reply(f"Gɪᴛ ᴘᴜʟʟ ғᴀɪʟᴇᴅ ᴡɪᴛʜ ᴇʀʀᴏʀ: {e.stderr}")

async def restart_bot(message):
    await message.reply("`Rᴇsᴛᴀʀᴛɪɴɢ... 🤯🤯`")
    args = [sys.executable, "-m", "Bot"]  # Adjust this line as needed
    os.execle(sys.executable, *args, os.environ)
    sys.exit()

@app.on_message(filters.command("restart") & filters.user(ADI))
async def restart_command(client, message):
    try:
        restart_message = await message.reply("**Bot ɪꜱ ʙᴇɪɴɢ ʀᴇꜱᴛᴀʀᴛᴇᴅ !!**")
        save_restart_data(restart_message.chat.id, restart_message.id)
        os.execvp(sys.executable, [sys.executable, "-m", "Bot"])
    except Exception as e:
        await message.reply(f"Rᴇsᴛᴀʀᴛ ғᴀɪʟᴇᴅ ᴡɪᴛʜ ᴇʀʀᴏʀ: {str(e)}")