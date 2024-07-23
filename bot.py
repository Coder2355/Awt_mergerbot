import os
import asyncio
import aiofiles
from tqdm import tqdm
from concurrent.futures import ProcessPoolExecutor
from flask import Flask, request, jsonify
from pyrogram import Client, filters
from pyrogram.types import Message
from config import config  # Import the config module

app = Client("audio_subtitle_bot", api_id=config.API_ID, api_hash=config.API_HASH, bot_token=config.BOT_TOKEN)

# Initialize Flask web server
web_app = Flask(__name__)

# Initialize executor for async FFmpeg processing
executor = ProcessPoolExecutor()

def run_ffmpeg_command(command):
    os.system(command)

async def async_run_ffmpeg_command(command):
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(executor, run_ffmpeg_command, command)

async def download_file_with_progress(client, message: Message, file_path: str):
    total_size = message.video.file_size
    progress = tqdm(total=total_size, unit='B', unit_scale=True, unit_divisor=1024, desc="Downloading")

    async def progress_callback(update, total_size):
        progress.update(update)

    await client.download_media(message, file_path, progress_callback=progress_callback)
    progress.close()

@app.on_message(filters.video)
async def handle_video(client, message: Message):
    file_id = message.video.file_id
    file_path = os.path.join(config.TEMP_DIR, f'{file_id}.mp4')
    
    # Download the file with progress reporting
    await download_file_with_progress(client, message, file_path)

    # Prepare FFmpeg commands
    audio_path = file_path.replace('.mp4', '.mp3')
    video_no_subs_path = file_path.replace('.mp4', '_nosub.mp4')
    remove_subs_command = f'{config.FFMPEG_COMMAND} -i {file_path} -vf "subtitles={file_path}" -c:v libx264 -c:a aac {video_no_subs_path}'
    extract_audio_command = f'{config.FFMPEG_COMMAND} -i {file_path} -q:a 0 -map a {audio_path}'

    # Run FFmpeg commands asynchronously
    await asyncio.gather(
        async_run_ffmpeg_command(extract_audio_command),
        async_run_ffmpeg_command(remove_subs_command)
    )

    # Send processed files with progress reporting
    await client.send_document(message.chat.id, audio_path)
    await client.send_document(message.chat.id, video_no_subs_path)

    # Clean up local files
    os.remove(file_path)
    os.remove(audio_path)
    os.remove(video_no_subs_path)

@web_app.route('/send_file', methods=['POST'])
async def send_file():
    file = request.files['file']
    file_path = os.path.join(config.TEMP_DIR, file.filename)
    total_size = len(file.read())
    file.seek(0)
    
    # Save the file with progress reporting
    progress = tqdm(total=total_size, unit='B', unit_scale=True, unit_divisor=1024, desc="Saving file")

    async def save_file():
        async with aiofiles.open(file_path, 'wb') as out_file:
            chunk_size = 8192
            while True:
                chunk = file.read(chunk_size)
                if not chunk:
                    break
                await out_file.write(chunk)
                progress.update(len(chunk))
    
    await save_file()
    progress.close()

    # Prepare FFmpeg commands
    audio_path = file_path.replace('.mp4', '.mp3')
    video_no_subs_path = file_path.replace('.mp4', '_nosub.mp4')
    remove_subs_command = f'{config.FFMPEG_COMMAND} -i {file_path} -vf "subtitles={file_path}" -c:v libx264 -c:a aac {video_no_subs_path}'
    extract_audio_command = f'{config.FFMPEG_COMMAND} -i {file_path} -q:a 0 -map a {audio_path}'

    # Run FFmpeg commands asynchronously
    await asyncio.gather(
        async_run_ffmpeg_command(extract_audio_command),
        async_run_ffmpeg_command(remove_subs_command)
    )

    # Return processed file paths
    return jsonify({
        'audio': audio_path,
        'video_no_subs': video_no_subs_path
    })

if __name__ == "__main__":
    app.run()
