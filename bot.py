import os
import asyncio
import time
import subprocess
from pyrogram import Client, filters
from pyrogram.errors import MessageNotModified
from pyrogram.types import CallbackQuery, Message
from config import Config
from helpers.display_progress import Progress
from helpers.ffmpeg_helper import take_screen_shot
from helpers.rclone_upload import rclone_driver
from helpers.uploader import uploadVideo
from helpers.utils import UserSettings
from PIL import Image
from hachoir.metadata import extractMetadata
from hachoir.parser import createParser
import ffmpeg

# MergeAudio function
def MergeAudio(videoPath: str, files_list: list, user_id):
    LOGGER.info("Generating Mux Command")
    muxcmd = ["ffmpeg", "-hide_banner"]
    videoData = ffmpeg.probe(filename=videoPath)
    videoStreamsData = videoData.get("streams")
    audioTracks = 0

    for file in files_list:
        muxcmd.append("-i")
        muxcmd.append(file)
    
    muxcmd.extend(["-map", "0:v:0", "-map", "0:a:?"])
    
    for i in range(len(videoStreamsData)):
        if videoStreamsData[i]["codec_type"] == "audio":
            muxcmd.extend([f"-disposition:a:{audioTracks}", "0"])
            audioTracks += 1
    
    fAudio = audioTracks
    
    for j in range(1, len(files_list)):
        muxcmd.extend(["-map", f"{j}:a", f"-metadata:s:a:{audioTracks}", f"title=Track {audioTracks + 1} - tg@Anime_warrior_tamil"])
        audioTracks += 1

    muxcmd.extend([f"-disposition:s:a:{fAudio}", "default", "-map", "0:s:?", "-c:v", "copy", "-c:a", "copy", "-c:s", "copy", f"downloads/{str(user_id)}/[@Anime_warrior_tamil]_export.mkv"])

    LOGGER.info(muxcmd)
    process = subprocess.call(muxcmd)
    LOGGER.info(process)
    return f"downloads/{str(user_id)}/[@Anime_warrior_tamil]_export.mkv"

# Pyrogram bot setup
app = Client("my_bot", api_id=Config.API_ID, api_hash=Config.API_HASH, bot_token=Config.BOT_TOKEN)

@app.on_callback_query()
async def merge_audio(c: Client, cb: CallbackQuery):
    omess = cb.message.reply_to_message
    files_list = []
    await cb.message.edit("⭕ Processing...")
    duration = 0
    video_mess = queueDB.get(cb.from_user.id)["videos"][0]
    list_message_ids: list = queueDB.get(cb.from_user.id)["audios"]
    list_message_ids.insert(0, video_mess)
    list_message_ids.sort()

    if list_message_ids is None:
        await cb.answer("Queue Empty", show_alert=True)
        await cb.message.delete(True)
        return

    if not os.path.exists(f"downloads/{str(cb.from_user.id)}/"):
        os.makedirs(f"downloads/{str(cb.from_user.id)}/")

    all_files = len(list_message_ids)
    n = 1
    msgs: list[Message] = await c.get_messages(chat_id=cb.from_user.id, message_ids=list_message_ids)
    
    for i in msgs:
        media = i.video or i.document or i.audio
        await cb.message.edit(f"📥 Starting Download of ... `{media.file_name}`")
        LOGGER.info(f"📥 Starting Download of ... {media.file_name}")
        currentFileNameExt = media.file_name.rsplit(sep=".")[-1].lower()
        tmpFileName = "vid.mkv" if currentFileNameExt in VIDEO_EXTENSIONS else "audio." + currentFileNameExt

        await asyncio.sleep(5)
        file_dl_path = None

        try:
            c_time = time.time()
            prog = Progress(cb.from_user.id, c, cb.message)
            file_dl_path = await c.download_media(
                message=media,
                file_name=f"downloads/{str(cb.from_user.id)}/{str(i.id)}/{tmpFileName}",
                progress=prog.progress_for_pyrogram,
                progress_args=(f"🚀 Downloading: `{media.file_name}`", c_time, f"\n**Downloading: {n}/{all_files}**"),
            )
            n += 1
            if gDict[cb.message.chat.id] and cb.message.id in gDict[cb.message.chat.id]:
                return
            await cb.message.edit(f"Downloaded Successfully ... `{media.file_name}`")
            LOGGER.info(f"Downloaded Successfully ... {media.file_name}")
            await asyncio.sleep(4)
        except Exception as downloadErr:
            LOGGER.warning(f"Failed to download Error: {downloadErr}")
            queueDB.get(cb.from_user.id)["audios"].remove(i.id)
            await cb.message.edit("❗File Skipped!")
            await asyncio.sleep(4)
            await cb.message.delete(True)
            continue
        files_list.append(f"{file_dl_path}")

    muxed_video = MergeAudio(files_list[0], files_list, cb.from_user.id)
    if muxed_video is None:
        await cb.message.edit("❌ Failed to add audio to video!")
        await delete_all(root=f"downloads/{str(cb.from_user.id)}")
        queueDB.update({cb.from_user.id: {"videos": [], "subtitles": [], "audios": []}})
        formatDB.update({cb.from_user.id: None})
        return
    
    try:
        await cb.message.edit("✅ Successfully Muxed Video!")
    except MessageNotModified:
        await cb.message.edit("Successfully Muxed Video! ✅")
    
    LOGGER.info(f"Video muxed for: {cb.from_user.first_name}")
    await asyncio.sleep(3)
    file_size = os.path.getsize(muxed_video)
    new_file_name = f"downloads/{str(cb.from_user.id)}/merged_video.mkv"
    os.rename(muxed_video, new_file_name)
    await cb.message.edit(f"🔄 Renaming Video to\n **{new_file_name.rsplit('/',1)[-1]}**")
    await asyncio.sleep(4)
    merged_video_path = new_file_name

    if UPLOAD_TO_DRIVE.get(f"{cb.from_user.id}"):
        await rclone_driver(omess, cb, merged_video_path)
        await delete_all(root=f"downloads/{str(cb.from_user.id)}")
        queueDB.update({cb.from_user.id: {"videos": [], "subtitles": [], "audios": []}})
        formatDB.update({cb.from_user.id: None})
        return

    if file_size > 2044723200 and not Config.IS_PREMIUM:
        await cb.message.edit(f"Video is Larger than 2GB, Can't Upload. Tell {Config.OWNER_USERNAME} to add premium account to get 4GB TG uploads.")
        await delete_all(root=f"downloads/{str(cb.from_user.id)}")
        queueDB.update({cb.from_user.id: {"videos": [], "subtitles": [], "audios": []}})
        formatDB.update({cb.from_user.id: None})
        return

    if Config.IS_PREMIUM and file_size > 4241280205:
        await cb.message.edit(f"Video is Larger than 4GB, Can't Upload. Tell {Config.OWNER_USERNAME} to die with premium account.")
        await delete_all(root=f"downloads/{str(cb.from_user.id)}")
        queueDB.update({cb.from_user.id: {"videos": [], "subtitles": [], "audios": []}})
        formatDB.update({cb.from_user.id: None})
        return

    await cb.message.edit("🎥 Extracting Video Data...")
    duration = 1

    try:
        metadata = extractMetadata(createParser(merged_video_path))
        if metadata.has("duration"):
            duration = metadata.get("duration").seconds
    except Exception as er:
        await delete_all(root=f"downloads/{str(cb.from_user.id)}")
        queueDB.update({cb.from_user.id: {"videos": [], "subtitles": [], "audios": []}})
        formatDB.update({cb.from_user.id: None})
        await cb.message.edit("⭕ Merged Video is corrupted")
        return

    try:
        user = UserSettings(cb.from_user.id, cb.from_user.first_name)
        thumb_id = user.thumbnail
        if thumb_id is None:
            raise Exception
        video_thumbnail = f"downloads/{str(cb.from_user.id)}_thumb.jpg"
        await c.download_media(message=str(thumb_id), file_name=video_thumbnail)
    except Exception as err:
        LOGGER.info("Generating thumbnail")
        video_thumbnail = await take_screen_shot(merged_video_path, f"downloads/{str(cb.from_user.id)}", (duration / 2))

    width, height = 1280, 720

    try:
        thumb = extractMetadata(createParser(video_thumbnail))
        height = thumb.get("height")
        width = thumb.get("width")
        img = Image.open(video_thumbnail)
        if width > height:
            img.resize((320, height))
        elif height > width:
            img.resize((width, 320))
        img.save(video_thumbnail)
        Image.open(video_thumbnail).convert("RGB").save(video_thumbnail, "JPEG")
   except:
