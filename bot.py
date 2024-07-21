import os
import subprocess
from aioflask import Flask, request, jsonify, send_file
import aiofiles
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import asyncio
from concurrent.futures import ThreadPoolExecutor
from config import API_ID, API_HASH, BOT_TOKEN

# Flask setup
app = Flask(__name__)

# Pyrogram setup
app_pyrogram = Client("bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

executor = ThreadPoolExecutor(max_workers=4)

async def run_ffmpeg_command(command):
    process = await asyncio.create_subprocess_exec(*command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = await process.communicate()
    return process.returncode, stdout, stderr

@app.route('/')
def index():
    return 'Welcome to the Video+Audio Merger and Audio Extractor bot!'

@app.route('/merge', methods=['POST'])
async def merge():
    video_file = request.files.get('video')
    audio_file = request.files.get('audio')

    if not video_file or not audio_file:
        return jsonify({'error': 'Please provide both video and audio files'}), 400

    video_filename = 'input_video.mp4'
    audio_filename = 'input_audio.mp3'
    output_filename = 'output_merged.mp4'

    try:
        async with aiofiles.open(video_filename, 'wb') as v_out, aiofiles.open(audio_filename, 'wb') as a_out:
            await v_out.write(await video_file.read())
            await a_out.write(await audio_file.read())

        command = [
            'ffmpeg',
            '-i', video_filename,
            '-i', audio_filename,
            '-c:v', 'copy',
            '-c:a', 'aac',
            '-strict', 'experimental',
            output_filename
        ]

        loop = asyncio.get_event_loop()
        returncode, stdout, stderr = await loop.run_in_executor(executor, run_ffmpeg_command, command)

        if returncode == 0:
            return await send_file(output_filename, as_attachment=True)
        else:
            return jsonify({'error': stderr.decode()}), 500
    finally:
        os.remove(video_filename)
        os.remove(audio_filename)
        if os.path.exists(output_filename):
            os.remove(output_filename)

@app.route('/extract', methods=['POST'])
async def extract():
    video_file = request.files.get('video')

    if not video_file:
        return jsonify({'error': 'Please provide a video file'}), 400

    video_filename = 'input_video.mp4'
    output_audio_filename = 'output_audio.mp3'

    try:
        async with aiofiles.open(video_filename, 'wb') as v_out:
            await v_out.write(await video_file.read())

        command = [
            'ffmpeg',
            '-i', video_filename,
            '-q:a', '0',
            '-map', 'a',
            output_audio_filename
        ]

        loop = asyncio.get_event_loop()
        returncode, stdout, stderr = await loop.run_in_executor(executor, run_ffmpeg_command, command)

        if returncode == 0:
            return await send_file(output_audio_filename, as_attachment=True)
        else:
            return jsonify({'error': stderr.decode()}), 500
    finally:
        os.remove(video_filename)
        if os.path.exists(output_audio_filename):
            os.remove(output_audio_filename)

@app.route('/send_video', methods=['POST'])
async def send_video():
    chat_id = request.form.get('chat_id')
    video_file = request.files.get('video')

    if not chat_id or not video_file:
        return jsonify({'error': 'Please provide both chat_id and video file'}), 400

    video_filename = 'input_video.mp4'
    async with aiofiles.open(video_filename, 'wb') as v_out:
        await v_out.write(await video_file.read())

    async with app_pyrogram:
        await app_pyrogram.send_video(chat_id, video_filename)

    os.remove(video_filename)
    return jsonify({'status': 'Video sent successfully!'})

@app.route('/send_audio', methods=['POST'])
async def send_audio():
    chat_id = request.form.get('chat_id')
    audio_file = request.files.get('audio')

    if not chat_id or not audio_file:
        return jsonify({'error': 'Please provide both chat_id and audio file'}), 400

    audio_filename = 'input_audio.mp3'
    async with aiofiles.open(audio_filename, 'wb') as a_out:
        await a_out.write(await audio_file.read())

    async with app_pyrogram:
        await app_pyrogram.send_audio(chat_id, audio_filename)

    os.remove(audio_filename)
    return jsonify({'status': 'Audio sent successfully!'})

@app.route('/replace_audio', methods=['POST'])
async def replace_audio():
    video_file = request.files.get('video')
    audio_file = request.files.get('audio')

    if not video_file or not audio_file:
        return jsonify({'error': 'Please provide both video and audio files'}), 400

    video_filename = 'input_video.mp4'
    audio_filename = 'input_audio.mp3'
    output_filename = 'output_video_with_new_audio.mp4'

    try:
        async with aiofiles.open(video_filename, 'wb') as v_out, aiofiles.open(audio_filename, 'wb') as a_out:
            await v_out.write(await video_file.read())
            await a_out.write(await audio_file.read())

        command = [
            'ffmpeg',
            '-i', video_filename,
            '-i', audio_filename,
            '-c:v', 'copy',
            '-c:a', 'aac',
            '-map', '0:v:0',
            '-map', '1:a:0',
            output_filename
        ]

        loop = asyncio.get_event_loop()
        returncode, stdout, stderr = await loop.run_in_executor(executor, run_ffmpeg_command, command)

        if returncode == 0:
            return await send_file(output_filename, as_attachment=True)
        else:
            return jsonify({'error': stderr.decode()}), 500
    finally:
        os.remove(video_filename)
        os.remove(audio_filename)
        if os.path.exists(output_filename):
            os.remove(output_filename)

@app_pyrogram.on_message(filters.command(['start']))
async def start(client, message):
    keyboard = InlineKeyboardMarkup(
        [[InlineKeyboardButton("Replace Audio", callback_data="replace_audio")]]
    )
    await message.reply("Welcome to the Video+Audio Merger and Audio Extractor bot!", reply_markup=keyboard)

@app_pyrogram.on_callback_query(filters.regex("replace_audio"))
async def on_callback_query(client, callback_query):
    await callback_query.message.reply("Please send me a video file and an audio file to replace the video's audio track.")

@app_pyrogram.on_message(filters.video)
async def handle_video(client, message):
    await message.reply("Video received! Please send the audio file to replace the existing audio track.")

@app_pyrogram.on_message(filters.audio)
async def handle_audio(client, message):
    await message.reply("Audio received! Replacing the video's audio track...")

    video_message = await client.get_chat_history(message.chat.id, limit=2)
    video_file_id = video_message[1].video.file_id

    video_filename = 'input_video.mp4'
    audio_filename = 'input_audio.mp3'
    output_filename = 'output_video_with_new_audio.mp4'

    await client.download_media(video_file_id, file_name=video_filename)
    await client.download_media(message.audio.file_id, file_name=audio_filename)

    command = [
        'ffmpeg',
        '-i', video_filename,
        '-i', audio_filename,
        '-c:v', 'copy',
        '-c:a', 'aac',
        '-map', '0:v:0',
        '-map', '1:a:0',
        output_filename
    ]

    loop = asyncio.get_event_loop()
    returncode, stdout, stderr = await loop.run_in_executor(executor, run_ffmpeg_command, command)

    if returncode == 0:
        await client.send_video(message.chat.id, output_filename)
    else:
        await message.reply(f"Error: {stderr.decode()}")

    os.remove(video_filename)
    os.remove(audio_filename)
    if os.path.exists(output_filename):
        os.remove(output_filename)

if __name__ == '__main__':
    app_pyrogram.start()
    app.run()
