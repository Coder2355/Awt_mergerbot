import os
import subprocess
from pyrogram import Client, filters
from pyrogram.types import Message
from flask import Flask, send_file, abort
import config
from threading import Thread

app = Client("media_extractor_bot", api_id=config.API_ID, api_hash=config.API_HASH, bot_token=config.BOT_TOKEN)
flask_app = Flask(__name__)

DOWNLOAD_DIR = "downloads"
OUTPUT_DIR = "output"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

def get_audio_stream_count(video_path: str) -> int:
    """Get the number of audio streams in a video."""
    command = [
        'ffprobe',
        '-v', 'error',
        '-select_streams', 'a',
        '-show_entries', 'stream=index',
        '-of', 'csv=p=0',
        video_path
    ]
    result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return len(result.stdout.decode().strip().split('\n'))

def extract_audio(video_path: str, audio_path_template: str):
    """Extract all audio streams from video using FFmpeg."""
    stream_count = get_audio_stream_count(video_path)
    for i in range(stream_count):
        audio_path = audio_path_template.format(i)
        command = [
            'ffmpeg',
            '-i', video_path,
            '-map', f'0:a:{i}',  # Map audio stream i
            '-acodec', 'mp3',
            '-q:a', '2',
            audio_path
        ]
        try:
            subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        except subprocess.CalledProcessError as e:
            print(f"FFmpeg error: {e.stderr.decode()}")
            raise

@app.on_message(filters.video)
async def handle_video(client: Client, message: Message):
    """Handle incoming video messages."""
    file_name = message.video.file_name
    video_path = os.path.join(DOWNLOAD_DIR, file_name)
    audio_path_template = os.path.join(OUTPUT_DIR, f"{os.path.splitext(file_name)[0]}_audio_{{}}.mp3")
    
    try:
        await message.download(file_name=video_path)
        extract_audio(video_path, audio_path_template)
        
        # Send all extracted audio files
        for file in os.listdir(OUTPUT_DIR):
            if file.startswith(os.path.splitext(file_name)[0]) and file.endswith('.mp3'):
                await message.reply_document(os.path.join(OUTPUT_DIR, file))
    except Exception as e:
        print(f"Error processing video: {e}")
        await message.reply("An error occurred while processing your video.")
    finally:
        if os.path.exists(video_path):
            os.remove(video_path)
        for file in os.listdir(OUTPUT_DIR):
            if file.startswith(os.path.splitext(file_name)[0]) and file.endswith('.mp3'):
                os.remove(os.path.join(OUTPUT_DIR, file))

@flask_app.route('/status')
def status():
    return "Bot is running"

@flask_app.route('/download_audio/<filename>', methods=['GET'])
def download_audio(filename):
    file_path = os.path.join(OUTPUT_DIR, filename)
    if os.path.exists(file_path):
        return send_file(file_path)
    abort(404, "File not found")

if __name__ == "__main__":
    app.run()
