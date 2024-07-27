import ffmpeg

def take_screen_shot(video_file, output_dir, time):
    output = f"{output_dir}/thumb.jpg"
    try:
        (
            ffmpeg
            .input(video_file, ss=time)
            .output(output, vframes=1)
            .run()
        )
        return output
    except ffmpeg.Error as e:
        print(e.stderr)
        return None
