from pyrogram import Client, filters
from flask import Flask, request, jsonify
import os
import threading
import logging
import concurrent.futures
import config
import ffmpeg as ffmpeg_util

app = Client("video_merger_bot", api_id=config.API_ID, api_hash=config.API_HASH, bot_token=config.BOT_TOKEN)

VIDEO_DIR = config.VIDEO_DIR
AUDIO_DIR = config.AUDIO_DIR

# Flask app setup
flask_app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.INFO)

# Define states
GET_VIDEO1 = 1
GET_VIDEO2 = 2
GET_AUDIO = 3

# Conversations storage
conversations = {}

@app.on_message(filters.command("merge_video") & filters.private)
async def start_video_merge(client, message):
    user_id = message.from_user.id
    conversations[user_id] = {"step": GET_VIDEO1}
    await message.reply("Please send the first video.")

@app.on_message(filters.video & filters.private)
async def handle_video(client, message):
    user_id = message.from_user.id
    if user_id in conversations:
        state = conversations[user_id].get("step")
        if state == GET_VIDEO1:
            video1_path = await message.download(file_name=os.path.join(VIDEO_DIR, "video1.mp4"))
            conversations[user_id]["video1"] = video1_path
            conversations[user_id]["step"] = GET_VIDEO2
            await message.reply("Send the second video now.")
        elif state == GET_VIDEO2:
            video2_path = await message.download(file_name=os.path.join(VIDEO_DIR, "video2.mp4"))
            video1_path = conversations[user_id].get("video1")
            output_path = os.path.join(VIDEO_DIR, "merged_video.mp4")
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(ffmpeg_util.merge_videos, video1_path, video2_path, output_path)
                result = future.result()
            if result:
                await message.reply_document(output_path)
            else:
                await message.reply("An error occurred while merging the videos.")
            os.remove(video1_path)
            os.remove(video2_path)
            os.remove(output_path)
            del conversations[user_id]
        else:
            await message.reply("Unexpected state. Please start the merge process again.")
    else:
        await message.reply("Please start the merge process using /merge_video command.")

@app.on_message(filters.command("merge_audio") & filters.private)
async def start_audio_merge(client, message):
    user_id = message.from_user.id
    conversations[user_id] = {"step": GET_AUDIO}
    await message.reply("Please send the video file first.")

@app.on_message(filters.video & filters.private)
async def handle_audio_video(client, message):
    user_id = message.from_user.id
    if user_id in conversations and conversations[user_id]["step"] == GET_AUDIO:
        video_path = await message.download(file_name=os.path.join(VIDEO_DIR, "video.mp4"))
        conversations[user_id]["video"] = video_path
        await message.reply("Send the audio file now.")
        conversations[user_id]["step"] = GET_AUDIO + 1

@app.on_message(filters.audio & filters.private)
async def handle_audio(client, message):
    user_id = message.from_user.id
    if user_id in conversations and conversations[user_id]["step"] == (GET_AUDIO + 1):
        audio_path = await message.download(file_name=os.path.join(AUDIO_DIR, "audio.mp3"))
        video_path = conversations[user_id].get("video")
        output_path = os.path.join(VIDEO_DIR, "video_with_audio.mp4")
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(ffmpeg_util.merge_video_audio, video_path, audio_path, output_path)
            result = future.result()
        if result:
            await message.reply_document(output_path)
        else:
            await message.reply("An error occurred while merging the video with audio.")
        os.remove(video_path)
        os.remove(audio_path)
        os.remove(output_path)
        del conversations[user_id]
    else:
        await message.reply("Unexpected state. Please start the merge process again.")

@flask_app.route('/status', methods=['GET'])
def status():
    return jsonify({"status": "Bot and Flask server are running."})

if __name__ == '__main__':
    app.run()
