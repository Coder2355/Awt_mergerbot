import ffmpeg

def merge_videos(video1_path: str, video2_path: str, output_path: str):
    """
    Merge two videos into one.
    """
    try:
        # Use `concat` filter for better performance in video merging
        ffmpeg.concat(ffmpeg.input(video1_path), ffmpeg.input(video2_path), v=1, a=0).output(output_path).run()
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
