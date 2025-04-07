import os
import logging
from yt_dlp import YoutubeDL

# Set up logging
logging.basicConfig(level=logging.DEBUG, filename='appcutshort.log', filemode='a',
                    format='%(asctime)s - %(levelname)s - %(message)s')

def get_youtube_stream_url(url):
    # Get the direct streaming URL from YouTube without downloading
    ydl_opts = {
        'format': 'bestvideo[height<=720]+bestaudio/best[height<=720]',  # Try 720p first
        'noplaylist': True,
        'quiet': True,
    }
    try:
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            if 'url' not in info:
                # Fallback to best available format
                ydl_opts['format'] = 'best'
                with YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=False)
            video_url = info.get('url')
            if video_url:
                logging.info(f"Retrieved streaming URL: {video_url}")
                return video_url
            else:
                logging.error("No stream URL found in video info")
                return None
    except Exception as e:
        logging.error(f"Error getting YouTube stream URL: {str(e)}")
        return None

def download_youtube_video(url, thumbnail_only=False):
    # Download video or thumbnail to local storage (used for export)
    output_path = os.path.join('temp', 'downloaded_video.mp4')
    thumbnail_path = os.path.join('temp', 'thumbnail.jpg')
    ydl_opts = {
        'format': 'bestvideo[height<=720]+bestaudio/best[height<=720]',
        'outtmpl': output_path,
        'merge_output_format': 'mp4',
        'writethumbnail': True,
        'skip_download': thumbnail_only,
    }
    try:
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=not thumbnail_only)
            if thumbnail_only:
                thumbnail_url = info.get('thumbnail')
                if thumbnail_url:
                    with YoutubeDL({'outtmpl': thumbnail_path}) as ydl_thumb:
                        ydl_thumb.download([thumbnail_url])
                return thumbnail_path if os.path.exists(thumbnail_path) else None
            return output_path if os.path.exists(output_path) else None
    except Exception as e:
        logging.error(f"Error downloading video: {e}")
        return None