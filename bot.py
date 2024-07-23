import os
import subprocess
import re
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup
from flask import Flask, send_file
import config  # Import your config module
import asyncio

app = Client("audio_extractor_bot", api_id=config.API_ID, api_hash=config.API_HASH, bot_token=config.BOT_TOKEN)
flask_app = Flask(__name__)

os.makedirs(config.DOWNLOAD_DIR, exist_ok=True)
os.makedirs(config.OUTPUT_DIR, exist_ok=True)

@app.on_message(filters.command("start"))
async def start_command(client: Client, message: Message):
    """Handle /start command."""
    await message.reply("Welcome! Send me a video, and I'll extract the audio for you.")

def extract_audio(video_path: str, output_dir: str) -> dict:
    """Extract all audio tracks from video using FFmpeg and return a dictionary of tracks."""
    # Get the list of audio streams
    command_list = [
        'ffmpeg',
        '-i', video_path,
        '-map', 'a',  # Select all audio streams
        '-f', 'ffmetadata',  # Output metadata
        '-'
    ]
    
    result = subprocess.run(command_list, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    metadata = result.stderr

    # Extract audio streams based on metadata
    audio_streams = re.findall(r'Stream #(\d+:\d+).*Audio', metadata)
    track_info = {}
    for i, stream_index in enumerate(audio_streams):
        output_audio_path = os.path.join(output_dir, f'audio_{stream_index}.mp3')
        extract_command = [
            'ffmpeg',
            '-i', video_path,
            '-map', f'{stream_index}',  # Select specific audio stream
            '-acodec', 'mp3',  # Use MP3 codec
            '-q:a', '2',  # Variable bitrate quality level
            '-y',  # Overwrite existing files without asking
            output_audio_path
        ]
        subprocess.run(extract_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        track_info[f'audio_{stream_index}.mp3'] = stream_index

    return track_info

def get_audio_duration(audio_path: str) -> str:
    """Get the duration of an audio file in hh:mm:ss format."""
    command = [
        'ffprobe',
        '-v', 'error',
        '-show_entries', 'format=duration',
        '-of', 'default=noprint_wrappers=1:nokey=1',
        audio_path
    ]
    result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    duration_seconds = float(result.stdout.strip())
    hours, remainder = divmod(int(duration_seconds), 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{hours:02}:{minutes:02}:{seconds:02}"

@app.on_message(filters.video)
async def handle_video(client: Client, message: Message):
    """Handle incoming video messages and show audio track selection."""
    await message.reply("Downloading your video...")

    # Download video
    video_file = await message.download(file_name=os.path.join(config.DOWNLOAD_DIR, message.video.file_name))
    await message.reply("Extracting audio...")

    # Prepare output directory for audio files
    audio_output_dir = os.path.join(config.OUTPUT_DIR, os.path.splitext(message.video.file_name)[0])
    os.makedirs(audio_output_dir, exist_ok=True)

    # Extract all audio streams
    track_info = extract_audio(video_file, audio_output_dir)

    # Create inline keyboard for audio track selection
    buttons = []
    for track_name, stream_index in track_info.items():
        duration = get_audio_duration(os.path.join(audio_output_dir, track_name))
        buttons.append([InlineKeyboardButton(f"{track_name} ({duration})", callback_data=track_name)])

    reply_markup = InlineKeyboardMarkup(buttons)
    reply_message = await message.reply("Select an audio track to download:", reply_markup=reply_markup)

    # Store the track info and reply message ID in user data
    app.user_data[message.from_user.id] = {
        'video_file': video_file,
        'audio_output_dir': audio_output_dir,
        'track_info': track_info,
        'reply_message': reply_message  # Store the whole message object
    }

@app.on_callback_query()
async def handle_callback_query(client: Client, query):
    """Handle the callback query from the inline keyboard."""
    user_id = query.from_user.id
    track_name = query.data

    if user_id in app.user_data:
        user_data = app.user_data[user_id]
        audio_path = os.path.join(user_data['audio_output_dir'], track_name)
        
        if os.path.exists(audio_path):
            # Send the audio file
            await query.message.reply_document(audio_path, caption=f"Audio: {track_name}\nDuration: {get_audio_duration(audio_path)} seconds")
            
            # Delete the original reply message
            if user_data.get('reply_message'):
                try:
                    await user_data['reply_message'].delete()
                except Exception as e:
                    print(f"Failed to delete message: {e}")

            # Clean up temporary files
            os.remove(user_data['video_file'])
            for file in os.listdir(user_data['audio_output_dir']):
                os.remove(os.path.join(user_data['audio_output_dir'], file))
            os.rmdir(user_data['audio_output_dir'])
            del app.user_data[user_id]
        else:
            await query.message.reply("The selected audio track is no longer available.")
    else:
        await query.message.reply("No video file found for this session.")

@flask_app.route('/status')
def status():
    return "Bot is running"

@flask_app.route('/download_audio/<filename>', methods=['GET'])
def download_audio(filename):
    file_path = os.path.join(config.OUTPUT_DIR, filename)
    if os.path.exists(file_path):
        return send_file(file_path)
    return "File not found", 404

if __name__ == "__main__":
    app.user_data = {}  # Initialize user data storage
    app.run()
