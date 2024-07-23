import os
import subprocess
from pyrogram import Client, filters
from pyrogram.types import Message
from threading import Thread
import config
from flask import Flask, send_file

app = Client("audio_extractor_bot", api_id=config.API_ID, api_hash=config.API_HASH, bot_token=config.BOT_TOKEN)
flask_app = Flask(__name__)

DOWNLOAD_DIR = "downloads"
OUTPUT_DIR = "output"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

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

@app.on_message(filters.video)
async def handle_video(client: Client, message: Message):
    """Handle incoming video messages."""
    video_file = await message.download(file_name=os.path.join(config.DOWNLOAD_DIR, message.video.file_name))
    audio_file = os.path.join(config.OUTPUT_DIR, f"{os.path.splitext(message.video.file_name)[0]}.mp3")
    
    extract_audio(video_file, audio_file)
    
    await message.reply_document(audio_file)
    
    os.remove(video_file)
    os.remove(audio_file)

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
