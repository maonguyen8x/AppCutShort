import os
from yt_dlp import YoutubeDL

def download_youtube_video(url, thumbnail_only=False):
    output_path = os.path.join('temp', 'downloaded_video.mp4')
    thumbnail_path = os.path.join('temp', 'thumbnail.jpg')
    ydl_opts = {
        'format': '18',  # Sử dụng định dạng MP4 360p để tránh lỗi nsig
        'outtmpl': output_path,
        'merge_output_format': 'mp4',
        'writethumbnail': True,
        'skip_download': thumbnail_only,
    }
    try:
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=not thumbnail_only)
            if thumbnail_only:
                return thumbnail_path if os.path.exists(thumbnail_path) else None
            return output_path if os.path.exists(output_path) else None
    except Exception as e:
        print(f"Error downloading: {e}")
        return None