import os
import subprocess
from flask import Flask, request, jsonify
from pyrogram import Client, filters
from pyrogram.types import Message
import config
import asyncio
import threading

# Initialize the bot with configuration from config.py
app = Client("audio_extractor_bot", api_id=config.API_ID, api_hash=config.API_HASH, bot_token=config.BOT_TOKEN)

# Initialize Flask web server
web_app = Flask(__name__)

# Ensure the download directory exists
os.makedirs(config.DOWNLOAD_PATH, exist_ok=True)

# Progress tracking callback
async def progress(current, total, message_id, bot, chat_id):
    percent = (current / total) * 100
    await bot.edit_message_text(chat_id, message_id, f"Download Progress: {percent:.2f}%")

@app.on_message(filters.command("start") & filters.private)
async def start(client, message: Message):
    await message.reply_text("Hi! Send me a video file and I'll extract the audio for you. If you want to remove subtitles as well, use the /remove_subs command followed by the video file.")

@app.on_message(filters.video & filters.private & ~filters.command("remove_subs"))
async def extract_audio(client, message: Message):
    video = message.video
    video_file_path = os.path.join(config.DOWNLOAD_PATH, "video.mp4")
    audio_file_path = os.path.splitext(video_file_path)[0] + ".mp3"

    # Download video asynchronously
    await client.download_media(message, video_file_path, progress=progress)

    # Extract audio using FFmpeg
    command = f"ffmpeg -i {video_file_path} -q:a 0 -map a -y {audio_file_path}"
    subprocess.run(command, shell=True, check=True)

    # Send the audio file with progress
    async def progress_upload(current, total):
        percent = (current / total) * 100
        await client.send_message(message.chat.id, f"Upload Progress: {percent:.2f}%")

    await client.send_audio(message.chat.id, audio_file_path, progress=progress_upload)

    # Clean up
    os.remove(video_file_path)
    os.remove(audio_file_path)

@app.on_message(filters.video & filters.private & filters.command("remove_subs"))
async def remove_subs_and_extract_audio(client, message: Message):
    video = message.video
    video_file_path = os.path.join(config.DOWNLOAD_PATH, "video.mp4")
    video_no_subs_file_path = os.path.splitext(video_file_path)[0] + "_nosubs.mp4"
    audio_file_path = os.path.splitext(video_file_path)[0] + ".mp3"

    # Download video asynchronously
    await client.download_media(message, video_file_path, progress=progress)

    # Remove subtitles using FFmpeg
    command_remove_subs = f"ffmpeg -i {video_file_path} -map 0:v -map 0:a -c copy -an -y {video_no_subs_file_path}"
    subprocess.run(command_remove_subs, shell=True, check=True)

    # Extract audio from the video without subtitles
    command_extract_audio = f"ffmpeg -i {video_no_subs_file_path} -q:a 0 -map a -y {audio_file_path}"
    subprocess.run(command_extract_audio, shell=True, check=True)

    # Send the audio file with progress
    async def progress_upload(current, total):
        percent = (current / total) * 100
        await client.send_message(message.chat.id, f"Upload Progress: {percent:.2f}%")

    await client.send_audio(message.chat.id, audio_file_path, progress=progress_upload)

    # Clean up
    os.remove(video_file_path)
    os.remove(video_no_subs_file_path)
    os.remove(audio_file_path)

# Web server routes
@web_app.route('/')
def index():
    return 'Audio Extractor Bot is running!'

@web_app.route('/status', methods=['GET'])
def status():
    return jsonify({'status': 'running'})

if __name__ == "__main__":
    app.run()
