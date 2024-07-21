from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
import config
import subprocess
import os

@app.on_message(filters.command("start"))
async def start(client, message):
    keyboard = InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("Send Video", callback_data="send_video")],
            [InlineKeyboardButton("Extract Audio", callback_data="extract_audio")]
        ]
    )
    await message.reply("Welcome! Choose an option below.", reply_markup=keyboard)

@app.on_callback_query(filters.regex("send_video"))
async def send_video(client, callback_query):
    await callback_query.message.reply("Please send the video file.")

@app.on_callback_query(filters.regex("extract_audio"))
async def extract_audio(client, callback_query):
    await callback_query.message.reply("Please send the video file to extract audio.")

@app.on_message(filters.video & filters.private)
async def receive_video(client, message):
    video_file = await message.download()

    # Save the video file path in the bot's context
    app.video_file = video_file
    
    if 'extract_audio' in message.text:
        # Extract audio from video
        output_audio_file = "extracted_audio.mp3"
        cmd = [
            'ffmpeg',
            '-i', video_file,
            '-q:a', '0',
            '-map', 'a',
            output_audio_file
        ]
        
        # Run ffmpeg command
        await subprocess.run(cmd, check=True)
        
        # Send the extracted audio back to the user
        await message.reply_document(output_audio_file)

        # Clean up files
        os.remove(video_file)
        os.remove(output_audio_file)

    else:
        # Notify user to send audio if needed (already handled)
        await message.reply("Video received! If you need to extract audio, use the Extract Audio option.")

@app.on_message(filters.audio & filters.private)
async def receive_audio(client, message):
    audio_file = await message.download()

    # Retrieve video file from bot context
    video_file = getattr(app, 'video_file', None)
    if not video_file:
        await message.reply("Please send the video file first.")
        return

    # Define output file path
    output_file = "merged_output.mp4"

    # Merge video and audio
    cmd = [
        'ffmpeg',
        '-i', video_file,
        '-i', audio_file,
        '-c:v', 'copy',
        '-c:a', 'aac',
        '-strict', 'experimental',
        output_file
    ]

    # Run ffmpeg command
    await subprocess.run(cmd, check=True)

    # Send the merged file back to the user
    await message.reply_document(output_file)

    # Clean up files
    os.remove(video_file)
    os.remove(audio_file)
    os.remove(output_file)

app.run()
