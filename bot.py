import os
import ffmpeg
from flask import Flask
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
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

# Define the inline keyboard
start_keyboard = InlineKeyboardMarkup(
    [
        [InlineKeyboardButton("Merge Video and Audio", callback_data="merge")],
        [InlineKeyboardButton("Extract Audio", callback_data="extract_audio")],
        [InlineKeyboardButton("Extract Subtitles", callback_data="extract_subtitles")],
    ]
)

@bot.on_message(filters.command("start"))
async def start(client, message: Message):
    await message.reply_text('Hi! Choose an action:', reply_markup=start_keyboard)

@bot.on_callback_query()
async def handle_callback_query(client, callback_query):
    if callback_query.data == "merge":
        await callback_query.message.reply_text('Send me a video file to start merging with an audio file.')
    elif callback_query.data == "extract_audio":
        await callback_query.message.reply_text('Send me a video file to extract audio.')
    elif callback_query.data == "extract_subtitles":
        await callback_query.message.reply_text('Send me a video file to extract subtitles.')
    await callback_query.answer()

@bot.on_message(filters.video)
async def handle_video(client, message: Message):
    await message.download(file_name=VIDEO_FILE)
    await message.reply_text('Video received! Now send me an audio file or use the buttons to perform other actions.', reply_markup=start_keyboard)

@bot.on_message(filters.document)
async def handle_document(client, message: Message):
    if message.document.mime_type.startswith("video/"):
        await message.download(file_name=VIDEO_FILE)
        await message.reply_text('Video received! Now send me an audio file or use the buttons to perform other actions.', reply_markup=start_keyboard)
    elif message.document.mime_type.startswith("audio/"):
        await message.download(file_name=AUDIO_FILE)
        await message.reply_text('Audio received! Merging now...')
        await merge_video_audio(message)

@bot.on_message(filters.audio)
async def handle_audio(client, message: Message):
    await message.download(file_name=AUDIO_FILE)
    await message.reply_text('Audio received! Merging now...')
    await merge_video_audio(message)

async def merge_video_audio(message: Message):
    try:
        input_video = ffmpeg.input(VIDEO_FILE)
        input_audio = ffmpeg.input(AUDIO_FILE)
        ffmpeg.output(input_video, input_audio, OUTPUT_FILE, vcodec='copy', acodec='aac', strict='experimental').run()
        
        current_time = datetime.now(pytz.timezone('UTC')).strftime('%Y-%m-%d %H:%M:%S %Z')
        await message.reply_text(f'Merging complete! Sending the merged file... ({current_time})')
        
        await message.reply_document(OUTPUT_FILE)
    except ffmpeg.Error as e:
        await message.reply_text(f'An error occurred: {e.stderr.decode()}')
    finally:
        cleanup_files()

async def extract_audio_from_video(message: Message):
    try:
        ffmpeg.input(VIDEO_FILE).output(EXTRACTED_AUDIO_FILE).run()
        
        await message.reply_text('Audio extraction complete! Sending the audio file...')
        
        await message.reply_document(EXTRACTED_AUDIO_FILE)
    except ffmpeg.Error as e:
        await message.reply_text(f'An error occurred: {e.stderr.decode()}')
    finally:
        cleanup_files()

async def extract_subtitles_from_video(message: Message):
    try:
        ffmpeg.input(VIDEO_FILE).output(SUBTITLES_FILE).run()
        
        await message.reply_text('Subtitles extraction complete! Sending the subtitles file...')
        
        await message.reply_document(SUBTITLES_FILE)
    except ffmpeg.Error as e:
        await message.reply_text(f'An error occurred: {e.stderr.decode()}')
    finally:
        cleanup_files()

def cleanup_files():
    if os.path.exists(VIDEO_FILE):
        os.remove(VIDEO_FILE)
    if os.path.exists(AUDIO_FILE):
        os.remove(AUDIO_FILE)
    if os.path.exists(EXTRACTED_AUDIO_FILE):
        os.remove(EXTRACTED_AUDIO_FILE)
    if os.path.exists(SUBTITLES_FILE):
        os.remove(SUBTITLES_FILE)
    if os.path.exists(OUTPUT_FILE):
        os.remove(OUTPUT_FILE)

if __name__ == '__main__':
    bot.start()
    asyncio.get_event_loop().run_forever()
