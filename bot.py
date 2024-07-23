import os
import subprocess
from pyrogram import Client, filters
from pyrogram.types import Message
import config
from flask import Flask, send_file

app = Client("audio_extractor_bot", api_id=config.API_ID, api_hash=config.API_HASH, bot_token=config.BOT_TOKEN)
flask_app = Flask(__name__)

DOWNLOAD_DIR = "downloads"
OUTPUT_DIR = "output"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

def extract_audio(video_path: str):
    """Extract multiple audio tracks from a video using FFmpeg."""
    # Get the number of audio streams
    command = [
        'ffmpeg',
        '-i', video_path,
        '-map', 'a',  # Select all audio streams
        '-c:a', 'mp3',  # Use MP3 codec
        '-f', 'segment',
        '-segment_list', 'audio_list.m3u8',  # Create a playlist of audio files
        '-segment_time', '10',  # Segment duration (adjust as needed)
        os.path.join(OUTPUT_DIR, 'audio_%03d.mp3')  # Output file pattern
    ]
    subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    
    # Rename audio files according to the segment list
    with open('audio_list.m3u8', 'r') as f:
        lines = f.readlines()
    
    for line in lines:
        if line.strip().endswith('.mp3'):
            old_name = line.strip()
            new_name = os.path.join(OUTPUT_DIR, f"{old_name}")
            os.rename(old_name, new_name)
    
    os.remove('audio_list.m3u8')

@app.on_message(filters.video)
async def handle_video(client: Client, message: Message):
    """Handle incoming video messages."""
    video_file = await message.download(file_name=os.path.join(DOWNLOAD_DIR, message.video.file_name))
    
    extract_audio(video_file)
    
    # Reply with all audio files
    for file_name in os.listdir(OUTPUT_DIR):
        if file_name.endswith('.mp3'):
            await message.reply_document(os.path.join(OUTPUT_DIR, file_name))
    
    os.remove(video_file)
    for file_name in os.listdir(OUTPUT_DIR):
        os.remove(os.path.join(OUTPUT_DIR, file_name))

@flask_app.route('/status')
def status():
    return "Bot is running"

@flask_app.route('/download_audio/<filename>', methods=['GET'])
def download_audio(filename):
    file_path = os.path.join(OUTPUT_DIR, filename)
    if os.path.exists(file_path):
        return send_file(file_path)
    return "File not found", 404

if __name__ == "__main__":
    app.run()
