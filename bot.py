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

@app.on_message(filters.command("start"))
async def start_command(client: Client, message: Message):
    """Handle /start command."""
    await message.reply("Welcome! Send me a video, and I'll extract the audio for you.")

def extract_audio(video_path: str, output_dir: str):
    """Extract all audio tracks from video using FFmpeg."""
    # Get the list of audio streams
    command_list = [
        'ffmpeg',
        '-i', video_path,
        '-map', 'a',  # Select all audio streams
        '-f', 'ffmetadata',  # Output metadata
        os.path.join(output_dir, 'metadata.txt')
    ]
    subprocess.run(command_list, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    # Read metadata to get stream info
    with open(os.path.join(output_dir, 'metadata.txt'), 'r') as metadata_file:
        lines = metadata_file.readlines()

    # Extract audio based on stream info
    for line in lines:
        if 'Stream' in line and 'Audio' in line:
            parts = line.split(' ')
            stream_index = parts[1].split(':')[1]
            output_audio_path = os.path.join(output_dir, f'audio_{stream_index}.mp3')
            extract_command = [
                'ffmpeg',
                '-i', video_path,
                '-map', f'a:{stream_index}',  # Select specific audio stream
                '-acodec', 'mp3',  # Use MP3 codec
                '-q:a', '2',  # Variable bitrate quality level
                output_audio_path
            ]
            subprocess.run(extract_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

@app.on_message(filters.video)
async def handle_video(client: Client, message: Message):
    """Handle incoming video messages with progress reporting."""
    await message.reply("Downloading your video...")

    # Download video
    video_file = await message.download(file_name=os.path.join(config.DOWNLOAD_DIR, message.video.file_name))
    await message.reply("Extracting audio...")

    # Prepare output directory for audio files
    audio_output_dir = os.path.join(config.OUTPUT_DIR, os.path.splitext(message.video.file_name)[0])
    os.makedirs(audio_output_dir, exist_ok=True)

    # Extract all audio streams
    extract_audio(video_file, audio_output_dir)

    # Send all extracted audio files
    audio_files = [os.path.join(audio_output_dir, f) for f in os.listdir(audio_output_dir) if f.endswith('.mp3')]
    for audio_file in audio_files:
        await message.reply_document(audio_file)
    
    # Clean up temporary files
    os.remove(video_file)
    for audio_file in audio_files:
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
