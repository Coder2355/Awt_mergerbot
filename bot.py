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

def process_videos(video1_path, video2_path, output_path):
    try:
        ffmpeg_util.merge_videos(video1_path, video2_path, output_path)
        return output_path
    except RuntimeError as e:
        logging.error(f"Error during video merging: {e}")
        return None

def process_video_audio(video_path, audio_path, output_path):
    try:
        ffmpeg_util.merge_video_audio(video_path, audio_path, output_path)
        return output_path
    except RuntimeError as e:
        logging.error(f"Error during video-audio merging: {e}")
        return None

@app.on_message(filters.command("merge_video") & filters.private)
async def merge_videos(client, message):
    if message.reply_to_message and message.reply_to_message.video:
        video1_path = await message.reply_to_message.download(file_name=os.path.join(VIDEO_DIR, "video1.mp4"))
        
        await message.reply("Send the second video now.")
        video2_message = await client.listen(message.chat.id, filters.video)
        video2_path = await video2_message.download(file_name=os.path.join(VIDEO_DIR, "video2.mp4"))
        
        output_path = os.path.join(VIDEO_DIR, "merged_video.mp4")
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(process_videos, video1_path, video2_path, output_path)
            output_path = future.result()
        
        if output_path:
            await message.reply_document(output_path)
        else:
            await message.reply("An error occurred while merging the videos.")
        os.remove(video1_path)
        os.remove(video2_path)
        os.remove(output_path)
    else:
        await message.reply("Please reply to the first video and send the second video as well.")

@app.on_message(filters.command("merge_audio") & filters.private)
async def merge_video_audio(client, message):
    if message.reply_to_message and message.reply_to_message.video:
        video_path = await message.reply_to_message.download(file_name=os.path.join(VIDEO_DIR, "video.mp4"))
        
        await message.reply("Send the audio file now.")
        audio_message = await client.listen(message.chat.id, filters.audio)
        audio_path = await audio_message.download(file_name=os.path.join(AUDIO_DIR, "audio.mp3"))
        
        output_path = os.path.join(VIDEO_DIR, "video_with_audio.mp4")
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(process_video_audio, video_path, audio_path, output_path)
            output_path = future.result()
        
        if output_path:
            await message.reply_document(output_path)
        else:
            await message.reply("An error occurred while merging the video with audio.")
        os.remove(video_path)
        os.remove(audio_path)
        os.remove(output_path)
    else:
        await message.reply("Please reply to the video and send the audio file as well.")

@flask_app.route('/status', methods=['GET'])
def status():
    return jsonify({"status": "Bot and Flask server are running."})

if __name__ == '__main__':
    app.run()
