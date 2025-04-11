import os
import logging
import yt_dlp

def get_thumbnail_url(video_url):
    try:
        with yt_dlp.YoutubeDL() as ydl:
            info = ydl.extract_info(video_url, download=False)
            return info.get('thumbnail', '')
    except Exception as e:
        logging.error(f"Error getting thumbnail URL: {str(e)}")
        return ''

def check_video_availability(video_url):
    try:
        with yt_dlp.YoutubeDL() as ydl:
            info = ydl.extract_info(video_url, download=False)
            return True, None
    except Exception as e:
        logging.error(f"Error checking video availability: {str(e)}")
        return False, str(e)

def download_youtube_video(video_url, output_path):
    ydl_opts = {
        'format': 'bestvideo+bestaudio/best',
        'outtmpl': output_path,
        'merge_output_format': 'mp4',
        'quiet': True,
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([video_url])
        if os.path.exists(output_path):
            return True, None
        else:
            return False, "Downloaded video file not found"
    except Exception as e:
        logging.error(f"Error downloading video: {str(e)}")
        return False, str(e)