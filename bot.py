import os
import subprocess
import time
import threading
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from tqdm import tqdm
from flask import Flask, jsonify
import asyncio
from config import API_ID, API_HASH, BOT_TOKEN

# Initialize the bot with your credentials from config
app = Client("merge_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)
flask_app = Flask(__name__)

# Temporary directories to store files
VIDEO_DIR = "videos/"
AUDIO_DIR = "audios/"
OUTPUT_DIR = "output/"

# Create directories if they don't exist
os.makedirs(VIDEO_DIR, exist_ok=True)
os.makedirs(AUDIO_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

# In-memory storage for user data
user_data = {}

async def download_with_progress(message, file_name, file_size, desc):
    with tqdm(total=file_size, unit="B", unit_scale=True, desc=desc) as pbar:
        await message.download(file_name=file_name, progress=pbar.update)

@app.on_message(filters.video & filters.private)
async def receive_video(client, message):
    video_path = VIDEO_DIR + message.video.file_name
    await message.reply_text("Downloading video...")
    
    await download_with_progress(message, video_path, message.video.file_size, "Video Download")
    user_data[message.from_user.id] = {"video": video_path}
    
    if "audio" in user_data.get(message.from_user.id, {}):
        await message.reply_text("Both video and audio files are ready. Use the /video_audio command to start merging.")
    else:
        await message.reply_text("Video received. Please send the audio file.")

@app.on_message(filters.audio & filters.private)
async def receive_audio(client, message):
    audio_path = AUDIO_DIR + message.audio.file_name
    await message.reply_text("Downloading audio...")
    
    await download_with_progress(message, audio_path, message.audio.file_size, "Audio Download")
    user_data[message.from_user.id]["audio"] = audio_path
    
    if "video" in user_data.get(message.from_user.id, {}):
        await message.reply_text("Both video and audio files are ready. Use the /video_audio command to start merging.")
    else:
        await message.reply_text("Audio received. Please send the video file.")

@app.on_message(filters.command("video_audio") & filters.private)
async def merge_command(client, message):
    user_id = message.from_user.id
    
    if user_id not in user_data or "video" not in user_data[user_id] or "audio" not in user_data[user_id]:
        await message.reply_text("You need to send both a video and an audio file before using this command.")
        return
    
    await message.reply_text("Please select the start time for the audio in the video.",
                             reply_markup=InlineKeyboardMarkup([
                                 [InlineKeyboardButton("Start at 0:00", callback_data="start_0")],
                                 [InlineKeyboardButton("Start at 0:30", callback_data="start_30")],
                                 [InlineKeyboardButton("Start at 1:00", callback_data="start_60")],
                                 [InlineKeyboardButton("Start at 1:30", callback_data="start_90")]
                             ]))

@app.on_callback_query()
async def handle_callback_query(client, callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    start_time = int(callback_query.data.split("_")[1])
    
    if user_id not in user_data or "video" not in user_data[user_id] or "audio" not in user_data[user_id]:
        await callback_query.answer("Please send the video and audio files first.")
        return

    video_path = user_data[user_id]["video"]
    audio_path = user_data[user_id]["audio"]
    output_path = OUTPUT_DIR + f"merged_{os.path.basename(video_path)}"
    
    await callback_query.message.edit_text("Merging video and audio...")

    # Run FFmpeg command and check for errors
    merge_result = merge_video_audio(video_path, audio_path, output_path, start_time)
    
    if merge_result:
        await callback_query.message.edit_text("Uploading merged video...")
        with tqdm(total=os.path.getsize(output_path), unit="B", unit_scale=True, desc="Video Upload") as pbar:
            await client.send_video(callback_query.message.chat.id, video=output_path, caption="Here is your merged file.",
                                    progress=pbar.update)

        # Clean up
        os.remove(video_path)
        os.remove(audio_path)
        os.remove(output_path)
        user_data.pop(user_id, None)
    else:
        await callback_query.message.edit_text("Error merging video and audio.")

def merge_video_audio(video_path, audio_path, output_path, start_time):
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())
    command = [
        "ffmpeg",
        "-i", video_path,
        "-itsoffset", str(start_time),
        "-i", audio_path,
        "-vf", f"drawtext=text='{timestamp}':x=10:y=10:fontsize=24:fontcolor=white",
        "-map", "0:v",
        "-map", "1:a",
        "-c:v", "copy",
        "-c:a", "aac",
        "-strict", "experimental",
        output_path
    ]
    
    try:
        result = subprocess.run(command, check=True, capture_output=True)
        if result.returncode == 0:
            return True
        else:
            print("FFmpeg Error:", result.stderr.decode())
            return False
    except subprocess.CalledProcessError as e:
        print("FFmpeg Error:", e.stderr.decode())
        return False

@flask_app.route('/status', methods=['GET'])
def status():
    return jsonify({"status": "Bot is running"})

if __name__ == "__main__":
    app.run()
