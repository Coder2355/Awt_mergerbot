import os
import ffmpeg
from flask import Flask
from pyrogram import Client, filters
from pyrogram.types import Message
from datetime import datetime
import pytz
import asyncio

# Configuration
from config import API_ID, API_HASH, BOT_TOKEN

app = Flask(__name__)
bot = Client("my_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# Define paths to store video and audio files temporarily
VIDEO_FILE = "video.mp4"
AUDIO_FILE = "audio.mp3"
EXTRACTED_AUDIO_FILE = "extracted_audio.mp3"
SUBTITLES_FILE = "subtitles.srt"
OUTPUT_FILE = "output.mp4"

@bot.on_message(filters.command("start"))
async def start(client, message: Message):
    await message.reply_text(
        'Hi! Use the following commands:\n'
        '/merge - Send a video and then an audio file to merge them.\n'
        '/extract_audio - Send a video to extract its audio.\n'
        '/extract_subtitles - Send a video to extract subtitles.'
    )

@bot.on_message(filters.command("merge"))
async def merge_command(client, message: Message):
    await message.reply_text('Send me a video file and then an audio file to merge them.')

@bot.on_message(filters.command("extract_audio"))
async def extract_audio_command(client, message: Message):
    await message.reply_text('Send me a video file to extract audio.')

@bot.on_message(filters.command("extract_subtitles"))
async def extract_subtitles_command(client, message: Message):
    await message.reply_text('Send me a video file to extract subtitles.')

@bot.on_message(filters.video)
async def handle_video(client, message: Message):
    await message.download(file_name=VIDEO_FILE)
    await message.reply_text('Video received! Now send me an audio file to merge or use /extract_audio or /extract_subtitles.')

@bot.on_message(filters.audio)
async def handle_audio(client, message: Message):
    await message.download(file_name=AUDIO_FILE)
    await message.reply_text('Audio received! Merging now...')
    await merge_video_audio()

@bot.on_message(filters.document)
async def handle_document(client, message: Message):
    mime_type = message.document.mime_type
    if mime_type.startswith("video/"):
        await message.download(file_name=VIDEO_FILE)
        await message.reply_text('Video received! Now send me an audio file to merge or use /extract_audio or /extract_subtitles.')
    elif mime_type.startswith("audio/"):
        await message.download(file_name=AUDIO_FILE)
        await message.reply_text('Audio received! Merging now...')
        await merge_video_audio()

async def merge_video_audio():
    try:
        ffmpeg.input(VIDEO_FILE).output(AUDIO_FILE, OUTPUT_FILE, vcodec='copy', acodec='aac', strict='experimental').run()
        
        current_time = datetime.now(pytz.timezone('UTC')).strftime('%Y-%m-%d %H:%M:%S %Z')
        await message.reply_text(f'Merging complete! Sending the merged file... ({current_time})')
        
        await message.reply_document(OUTPUT_FILE)
    except ffmpeg.Error as e:
        await message.reply_text(f'An error occurred: {e.stderr.decode()}')
    finally:
        cleanup_files()

async def extract_audio_from_video():
    try:
        ffmpeg.input(VIDEO_FILE).output(EXTRACTED_AUDIO_FILE).run()
        
        await message.reply_text('Audio extraction complete! Sending the audio file...')
        
        await message.reply_document(EXTRACTED_AUDIO_FILE)
    except ffmpeg.Error as e:
        await message.reply_text(f'An error occurred: {e.stderr.decode()}')
    finally:
        cleanup_files()

async def extract_subtitles_from_video():
    try:
        ffmpeg.input(VIDEO_FILE).output(SUBTITLES_FILE).run()
        
        await message.reply_text('Subtitles extraction complete! Sending the subtitles file...')
        
        await message.reply_document(SUBTITLES_FILE)
    except ffmpeg.Error as e:
        await message.reply_text(f'An error occurred: {e.stderr.decode()}')
    finally:
        cleanup_files()

def cleanup_files():
    for file in [VIDEO_FILE, AUDIO_FILE, EXTRACTED_AUDIO_FILE, SUBTITLES_FILE, OUTPUT_FILE]:
        if os.path.exists(file):
            os.remove(file)

if __name__ == '__main__':
    bot.start()
    asyncio.get_event_loop().run_forever()
