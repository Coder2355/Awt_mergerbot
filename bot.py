import os
import subprocess
from pyrogram import Client, filters
from pyrogram.types import Message
from flask import Flask, send_file
import config  # Import your config module
import asyncio
from threading import Thread

app = Client("audio_extractor_bot", api_id=config.API_ID, api_hash=config.API_HASH, bot_token=config.BOT_TOKEN)
flask_app = Flask(__name__)

os.makedirs(config.DOWNLOAD_DIR, exist_ok=True)
os.makedirs(config.OUTPUT_DIR, exist_ok=True)

@app.on_message(filters.command("start"))
async def start_command(client: Client, message: Message):
    """Handle /start command."""
    await message.reply("Welcome! Use /extract_audio and reply to a video, file, or document to extract audio.")

@app.on_message(filters.command("extract_audio") & (filters.video | filters.document | filters.audio))
async def extract_audio_command(client: Client, message: Message):
    """Handle /extract_audio command."""
    reply_message = message.reply_to_message

    if not reply_message:
        await message.reply("Please reply to a video, file, or document with the /extract_audio command.")
        return

    if reply_message.video or reply_message.document or reply_message.audio:
        await message.reply("Downloading your file...")

        # Determine the file type and download the file
        file_type = 'video' if reply_message.video else 'document' if reply_message.document else 'audio'
        file_name = getattr(reply_message, file_type).file_name
        file_path = await reply_message.download(file_name=os.path.join(config.DOWNLOAD_DIR, file_name))
        
        await message.reply("Extracting audio...")

        audio_path = os.path.join(config.OUTPUT_DIR, f"{os.path.splitext(file_name)[0]}.mp3")
        
        # Extract audio with progress reporting
        await extract_audio_with_progress(file_path, audio_path)
        
        await message.reply_document(audio_path)
        
        os.remove(file_path)
        os.remove(audio_path)
    else:
        await message.reply("Please reply to a video, file, or document with the /extract_audio command.")

async def extract_audio_with_progress(file_path: str, audio_path: str):
    """Extract audio from video, file, or document with progress reporting."""
    # Notify about progress
    process = subprocess.Popen(
        ['ffmpeg', '-i', file_path, '-vn', '-acodec', 'mp3', '-q:a', '2', audio_path],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )
    for line in process.stderr:
        if b'Duration' in line:
            await asyncio.sleep(1)  # Simulate progress reporting

@flask_app.route('/status')
def status():
    return "Bot is running"

@flask_app.route('/download_audio/<filename>', methods=['GET'])
def download_audio(filename):
    file_path = os.path.join(config.OUTPUT_DIR, filename)
    if os.path.exists(file_path):
        return send_file(file_path)
    return "File not found", 404

if __name__ == "__main__":
    app.run()
