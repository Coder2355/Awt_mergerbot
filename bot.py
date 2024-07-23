import os
import subprocess
from pyrogram import Client, filters
from pyrogram.types import Message
from threading import Thread
from flask import Flask, send_file
import config  # Import your config module
import asyncio

app = Client("audio_extractor_bot", api_id=config.API_ID, api_hash=config.API_HASH, bot_token=config.BOT_TOKEN)
flask_app = Flask(__name__)

os.makedirs(config.DOWNLOAD_DIR, exist_ok=True)
os.makedirs(config.OUTPUT_DIR, exist_ok=True)

def extract_audio(video_path: str, audio_path: str):
    """Extract audio from video using FFmpeg."""
    command = [
        'ffmpeg',
        '-i', video_path,
        '-vn',  # No video
        '-acodec', 'mp3',  # Use MP3 codec
        '-q:a', '2',  # Variable bitrate quality level
        audio_path
    ]
    subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

@app.on_message(filters.command("start"))
async def start_command(client: Client, message: Message):
    """Handle /start command."""
    await message.reply("Welcome! Send me a video, and I'll extract the audio for you.")

@app.on_message(filters.command("help"))
async def help_command(client: Client, message: Message):
    """Handle /help command."""
    await message.reply("Send me a video file, and I'll extract the audio. Use /start to begin.")

@app.on_message(filters.video)
async def handle_video(client: Client, message: Message):
    """Handle incoming video messages with progress reporting."""
    await message.reply("Downloading your video...")

    # Download video
    video_file = await message.download(file_name=os.path.join(config.DOWNLOAD_DIR, message.video.file_name))
    await message.reply("Extracting audio...")

    audio_file = os.path.join(config.OUTPUT_DIR, f"{os.path.splitext(message.video.file_name)[0]}.mp3")
    
    # Extract audio with progress reporting
    await extract_audio_with_progress(video_file, audio_file)
    
    await message.reply_document(audio_file)
    
    os.remove(video_file)
    os.remove(audio_file)

async def extract_audio_with_progress(video_path: str, audio_path: str):
    """Extract audio from video with progress reporting."""
    # Notify about progress
    process = subprocess.Popen(
        ['ffmpeg', '-i', video_path, '-vn', '-acodec', 'mp3', '-q:a', '2', audio_path],
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
