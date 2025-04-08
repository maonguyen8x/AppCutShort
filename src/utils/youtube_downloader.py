import os
import logging
from yt_dlp import YoutubeDL

# Set up logging
logging.basicConfig(level=logging.DEBUG, filename='appcutshort.log', filemode='a',
                    format='%(asctime)s - %(levelname)s - %(message)s')

def get_thumbnail_url(video_url):
    """
    Extract the thumbnail URL from a YouTube video URL using yt-dlp.

    Args:
        video_url (str): The YouTube video URL.

    Returns:
        str: The URL of the video's thumbnail, or None if extraction fails.
    """
    try:
        logging.info(f"Extracting thumbnail URL for: {video_url}")
        ydl_opts = {
            'skip_download': True,  # Do not download the video
            'quiet': True,         # Suppress yt-dlp output
        }
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=False)
            thumbnail_url = info.get('thumbnail')
            if thumbnail_url:
                logging.info(f"Thumbnail URL extracted: {thumbnail_url}")
                return thumbnail_url
            else:
                logging.error("No thumbnail URL found in video info")
                return None
    except Exception as e:
        logging.error(f"Error extracting thumbnail URL: {str(e)}")
        return None

def download_youtube_video(video_url, output_path):
    """
    Download a YouTube video using yt-dlp.

    Args:
        video_url (str): The YouTube video URL.
        output_path (str): The path to save the downloaded video.

    Returns:
        bool: True if download is successful, False otherwise.
    """
    try:
        logging.info(f"Downloading video from: {video_url}")
        ydl_opts = {
            'format': 'bestvideo[height<=720]+bestaudio/best[height<=720]',
            'outtmpl': output_path,
            'merge_output_format': 'mp4',
            'quiet': True,
        }
        with YoutubeDL(ydl_opts) as ydl:
            ydl.download([video_url])
        if os.path.exists(output_path):
            logging.info(f"Video downloaded successfully to: {output_path}")
            return True
        else:
            logging.error("Downloaded video file not found after download")
            return False
    except Exception as e:
        logging.error(f"Error downloading video: {str(e)}")
        return False