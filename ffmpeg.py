import ffmpeg
import os

def merge_videos(video1_path: str, video2_path: str, output_path: str):
    """
    Merge two videos into one.
    """
    try:
        ffmpeg.input(video1_path).input(video2_path).output(output_path, vcodec='libx264', acodec='aac', strict='experimental').run()
    except ffmpeg.Error as e:
        raise RuntimeError(f"FFmpeg error during merging videos: {e}")

def merge_video_audio(video_path: str, audio_path: str, output_path: str):
    """
    Merge a video with an audio track.
    """
    try:
        ffmpeg.input(video_path).input(audio_path).output(output_path, vcodec='copy', acodec='aac').run()
    except ffmpeg.Error as e:
        raise RuntimeError(f"FFmpeg error during merging video with audio: {e}")
