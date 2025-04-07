import os
import subprocess
import re
import shutil
import logging
import platform
from PyQt6.QtCore import QThread, pyqtSignal

# Set up logging
logging.basicConfig(level=logging.DEBUG, filename='appcutshort.log', filemode='a',
                    format='%(asctime)s - %(levelname)s - %(message)s')

class ProcessThread(QThread):
    progress = pyqtSignal(int)
    finished = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(self, input_path, output_path, aspect_ratio, font, color, subtitles, language, duration,
                 font_size=24, template='Default', caption_effect='None', volume=1.0, audio_effect='None',
                 background_music=None, color_filter='None', icons=None):
        super().__init__()
        self.input_path = input_path
        self.output_path = output_path
        self.aspect_ratio = aspect_ratio
        self.font = font
        self.color = color
        self.subtitles = subtitles
        self.language = language
        self.duration = duration
        self.font_size = font_size
        self.template = template
        self.caption_effect = caption_effect
        self.volume = volume
        self.audio_effect = audio_effect
        self.background_music = background_music
        self.color_filter = color_filter
        self.icons = icons if icons else []

    def get_font_path(self):
        # Determine font path based on OS
        if os.name == 'nt':  # Windows
            return f'C:\\Windows\\Fonts\\{self.font}.ttf'
        elif platform.system() == 'Darwin':  # macOS
            return f'/Library/Fonts/{self.font}.ttf'
        else:  # Linux
            return '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'

    def time_to_seconds(self, time_str):
        # Convert time string (HH:MM:SS) to seconds
        try:
            h, m, s = map(float, time_str.split(':'))
            return h * 3600 + m * 60 + s
        except ValueError:
            logging.error(f"Invalid time format: {time_str}")
            return 0

    def run(self):
        try:
            if not shutil.which('ffmpeg'):
                self.error.emit("FFmpeg not found. Please install FFmpeg and add it to PATH.")
                return

            if not os.path.exists('temp'):
                os.makedirs('temp')

            # Only check if input_path is a local file; skip for URLs
            if not self.input_path.startswith('http') and not os.path.exists(self.input_path):
                self.error.emit(f"Input file not found: {self.input_path}")
                return

            logging.info(f"Processing input: {self.input_path}")
            logging.info(f"Output path: {self.output_path}")
            logging.info(f"Aspect ratio: {self.aspect_ratio}")
            logging.info(f"Font: {self.font}")
            logging.info(f"Subtitles: {self.subtitles}")
            logging.info(f"Volume: {self.volume}")
            logging.info(f"Audio effect: {self.audio_effect}")
            logging.info(f"Background music: {self.background_music}")
            logging.info(f"Color filter: {self.color_filter}")
            logging.info(f"Icons: {self.icons}")

            # Define resolution based on aspect ratio
            resolution_map = {
                '9:16': '1080:1920',
                '16:9': '1920:1080',
                '1:1': '1080:1080'
            }
            scale = resolution_map.get(self.aspect_ratio, '1920:1080')

            # Convert color to FFmpeg format
            color = self.color.lstrip('#')
            if not all(c in '0123456789ABCDEFabcdef' for c in color):
                logging.warning(f"Invalid color format: {self.color}. Using white as fallback.")
                color = 'FFFFFF'
            color = f"0x{color}"

            # Map duration to seconds
            duration_map = {'Auto': '60', '<30s': '30', '30s - 60s': '60', '60s - 90s': '90', '90s - 3min': '180'}
            max_duration = duration_map.get(self.duration, '60')

            # Apply template styles
            template_styles = {
                'Default': 'y=main_h-text_h-50:box=0',
                'Modern': 'y=main_h-text_h-50:box=1:boxcolor=black@0.5:boxborderw=5',
                'Classic': 'y=50:box=1:boxcolor=white@0.3:boxborderw=3',
                'Minimal': 'y=main_h-text_h-50:box=0:shadowx=2:shadowy=2'
            }
            template_style = template_styles.get(self.template, 'y=main_h-text_h-50:box=0')

            # Apply caption effects
            effect_styles = {
                'None': '',
                'Fade': ':alpha=\'if(lt(t,0.5),0,if(lt(t,1),t-0.5,1))\'',
                'Move': ':x=(w-text_w)/2+t*50',
                'Shadow': ':shadowx=2:shadowy=2'
            }
            effect_style = effect_styles.get(self.caption_effect, '')

            # Get font path
            font_path = self.get_font_path()
            if not os.path.exists(font_path):
                logging.warning(f"Font file not found at {font_path}. Falling back to Arial.")
                font_path = 'C:\\Windows\\Fonts\\arial.ttf'
                if not os.path.exists(font_path):
                    self.error.emit(f"Font file not found at {font_path}. Please ensure Arial is installed.")
                    return

            # Create drawtext filters for subtitles
            drawtext_filters = []
            for start, end, text in self.subtitles:
                # Parse start and end times
                start_sec = self.time_to_seconds(start.split(',')[0])
                end_sec = self.time_to_seconds(end.split(',')[0])

                # Escape special characters in the subtitle text
                text = text.replace("'", "\\'").replace('"', '\\"').replace(':', '\\:').replace(',', '\\,').replace('!', '\\!')

                # Construct the drawtext filter
                drawtext = (
                    f"drawtext=fontfile='{font_path}':"
                    f"text='{text}':"
                    f"fontcolor={color}:"
                    f"fontsize={self.font_size}:"
                    f"x=(w-text_w)/2:"
                    f"{template_style}"
                    f"{effect_style}:"
                    f"enable='between(t,{start_sec},{end_sec})'"
                )
                drawtext_filters.append(drawtext)

            # Apply color filters
            color_filters = {
                'None': '',
                'Bright': 'eq=brightness=0.1',
                'Contrast': 'eq=contrast=1.5',
                'Vintage': 'hue=s=0.5',
                'Cinematic': 'eq=contrast=1.2:saturation=1.3'
            }
            color_filter = color_filters.get(self.color_filter, '')

            # Combine video filters
            video_filters = [f"scale={scale}:force_original_aspect_ratio=decrease,pad={scale}:(ow-iw)/2:(oh-ih)/2"]
            if drawtext_filters:
                video_filters.extend(drawtext_filters)
            if color_filter:
                video_filters.append(color_filter)

            # Add icons/stickers as overlays
            for i, icon in enumerate(self.icons):
                if os.path.exists(icon['path']):
                    video_filters.append(
                        f"movie='{icon['path']}' [watermark{i}]; [in][watermark{i}] overlay={icon['x']}:{icon['y']}:format=auto:enable='between(t,0,{max_duration})' [out]"
                    )
                else:
                    logging.warning(f"Icon file not found: {icon['path']}. Skipping.")

            video_filter = ','.join(video_filters) if video_filters else "scale=1920:1080"
            logging.info(f"Video filter: {video_filter}")

            # Handle audio processing
            audio_filters = [f"volume={self.volume}"]
            if self.audio_effect == 'Echo':
                audio_filters.append("aecho=0.8:0.9:1000:0.3")
            elif self.audio_effect == 'Reverb':
                audio_filters.append("areverb=wet=0.3")
            audio_filter = ','.join(audio_filters) if audio_filters else "volume=1.0"
            logging.info(f"Audio filter: {audio_filter}")

            # Build FFmpeg command
            cmd = ['ffmpeg', '-i', self.input_path]
            if self.background_music and os.path.exists(self.background_music):
                cmd.extend(['-i', self.background_music])
                cmd.extend(['-filter_complex', f"[0:a][1:a]amix=inputs=2:duration=first:dropout_transition=2[aout]"])
                cmd.extend(['-map', '[aout]', '-map', '0:v'])

            cmd.extend([
                '-vf', video_filter,
                '-af', audio_filter,
                '-t', max_duration,
                '-b:a', '96k',
                '-y', self.output_path
            ])

            logging.info(f"FFmpeg command: {' '.join(cmd)}")

            # Run FFmpeg
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                encoding='utf-8',
                errors='replace'
            )

            duration = None
            ffmpeg_output = []
            for line in process.stdout:
                ffmpeg_output.append(line)
                if 'Duration' in line and duration is None:
                    match = re.search(r'Duration: (\d+):(\d+):(\d+\.\d+)', line)
                    if match:
                        hours, minutes, seconds = map(float, match.groups())
                        duration = hours * 3600 + minutes * 60 + seconds
                if 'time=' in line and duration:
                    match = re.search(r'time=(\d+):(\d+):(\d+\.\d+)', line)
                    if match:
                        hours, minutes, seconds = map(float, match.groups())
                        current_time = hours * 3600 + minutes * 60 + seconds
                        percent = int((current_time / duration) * 100) if duration > 0 else 0
                        self.progress.emit(min(percent, 100))

            process.wait()
            if process.returncode != 0:
                error_message = "Error processing video. FFmpeg failed.\n" + "\n".join(ffmpeg_output[-10:])
                logging.error(error_message)
                self.error.emit(error_message)
                return

            self.finished.emit(self.output_path)

        except Exception as e:
            error_message = f"Unexpected error: {str(e)}"
            logging.error(error_message)
            self.error.emit(error_message)