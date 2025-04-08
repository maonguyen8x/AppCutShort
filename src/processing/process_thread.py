import os
import subprocess
import logging
from PyQt6.QtCore import QThread, pyqtSignal

class ProcessThread(QThread):
    progress = pyqtSignal(int)
    finished = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(self, video_path, output_path, subtitles, ratio, duration, font, font_size, color, template, volume, audio_effect, background_music, caption_effect, color_filter, resolution=None, fps=None):
        super().__init__()
        self.video_path = video_path
        self.output_path = output_path
        self.subtitles = subtitles
        self.ratio = ratio
        self.duration = duration
        self.font = font
        self.font_size = font_size
        self.color = color
        self.template = template
        self.volume = volume
        self.audio_effect = audio_effect
        self.background_music = background_music
        self.caption_effect = caption_effect
        self.color_filter = color_filter
        self.resolution = resolution  # New parameter for resolution
        self.fps = fps  # New parameter for FPS

    def clean_subtitle_text(self, text):
        """
        Clean subtitle text to avoid syntax errors in FFmpeg.
        - Remove invalid special characters.
        - Replace single quotes to prevent syntax issues.
        - Trim extra whitespace from the start and end.
        """
        if not text:
            return ""
        # Replace single quotes with escaped quotes to avoid syntax errors
        text = text.replace("'", "\\'")
        # Remove extra whitespace
        text = text.strip()
        # Remove non-printable characters if necessary
        text = "".join(c for c in text if c.isprintable())
        return text

    def generate_ffmpeg_command(self):
        """
        Generate FFmpeg command to process the video with effects, subtitles, resolution, and FPS.
        """
        try:
            # Ensure FFmpeg is available
            ffmpeg_path = "ffmpeg"  # Assumes FFmpeg is installed and added to PATH
            command = [ffmpeg_path, "-i", self.video_path]

            # Add background music if provided
            if self.background_music:
                command.extend(["-i", self.background_music])
                command.extend(["-filter_complex", "[0:a][1:a]amix=inputs=2:duration=first:dropout_transition=2"])

            # Handle aspect ratio and resolution
            if self.ratio == "9:16":
                scale = "scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2"
            elif self.ratio == "1:1":
                scale = "scale=1080:1080:force_original_aspect_ratio=decrease,pad=1080:1080:(ow-iw)/2:(oh-ih)/2"
            else:  # 16:9
                scale = "scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2"

            # Override scale if resolution is specified
            if self.resolution:
                if self.resolution == "480p":
                    width, height = 854, 480
                elif self.resolution == "720p":
                    width, height = 1280, 720
                elif self.resolution == "1080p":
                    width, height = 1920, 1080
                elif self.resolution == "2K":
                    width, height = 2560, 1440
                elif self.resolution == "4K":
                    width, height = 3840, 2160
                else:
                    width, height = 1920, 1080  # Fallback to 1080p
                scale = f"scale={width}:{height}:force_original_aspect_ratio=decrease,pad={width}:{height}:(ow-iw)/2:(oh-ih)/2"

            # Handle color filter
            color_filter = ""
            if self.color_filter == "Bright":
                color_filter = "eq=brightness=0.1"
            elif self.color_filter == "Contrast":
                color_filter = "eq=contrast=1.5"
            elif self.color_filter == "Vintage":
                color_filter = "curves=vintage"
            elif self.color_filter == "Cinematic":
                color_filter = "colorbalance=rs=0.1:bs=-0.1"

            # Combine scale and color filter
            video_filters = [scale]
            if color_filter:
                video_filters.append(color_filter)

            # Process subtitles with drawtext
            if self.subtitles:
                drawtext_filters = []
                for subtitle in self.subtitles:
                    try:
                        start = float(subtitle.get("start", 0))
                        end = float(subtitle.get("end", 0))
                        text = self.clean_subtitle_text(subtitle.get("text", ""))
                        if not text:
                            continue

                        # Format drawtext filter
                        drawtext = (
                            f"drawtext=fontfile='{self.font}':"
                            f"text='{text}':"
                            f"fontcolor={self.color}:"
                            f"fontsize={self.font_size}:"
                            f"x=(w-text_w)/2:"
                            f"y=h-text_h-50:"
                            f"box=1:"
                            f"boxcolor=black@0.5:"
                            f"boxborderw=5:"
                            f"enable='between(t,{start},{end})'"
                        )
                        drawtext_filters.append(drawtext)
                    except (ValueError, KeyError) as e:
                        logging.error(f"Invalid subtitle format: {subtitle}. Error: {str(e)}")
                        continue

                if drawtext_filters:
                    video_filters.extend(drawtext_filters)

            # Combine all video filters
            if video_filters:
                command.extend(["-vf", ",".join(video_filters)])

            # Handle FPS if specified
            if self.fps:
                command.extend(["-r", str(self.fps)])

            # Handle volume
            if self.volume != 1.0:
                command.extend(["-af", f"volume={self.volume}"])

            # Handle audio effect
            if self.audio_effect == "Echo":
                command.extend(["-af", "aecho=0.8:0.9:1000:0.3"])
            elif self.audio_effect == "Reverb":
                command.extend(["-af", "reverb=50:0.5:0.5:0.5:0.5:0.5:0.5"])

            # Handle duration
            if self.duration != "Auto":
                if self.duration == "<30s":
                    duration = 30
                elif self.duration == "30s - 60s":
                    duration = 60
                elif self.duration == "60s - 90s":
                    duration = 90
                else:  # 90s - 3min
                    duration = 180
                command.extend(["-t", str(duration)])

            # Output
            command.extend(["-y", self.output_path])
            return command

        except Exception as e:
            logging.error(f"Error generating FFmpeg command: {str(e)}")
            return None

    def run(self):
        try:
            # Check if FFmpeg is installed
            ffmpeg_check = subprocess.run(["ffmpeg", "-version"], capture_output=True, text=True)
            if ffmpeg_check.returncode != 0:
                error_message = "FFmpeg is not installed or not found in PATH."
                logging.error(error_message)
                self.error.emit(error_message)
                return

            # Check if input file exists
            if not os.path.exists(self.video_path):
                error_message = f"Input video file not found: {self.video_path}"
                logging.error(error_message)
                self.error.emit(error_message)
                return

            # Check if output directory is writable
            output_dir = os.path.dirname(self.output_path)
            if not os.path.exists(output_dir):
                os.makedirs(output_dir, exist_ok=True)
            if not os.access(output_dir, os.W_OK):
                error_message = f"Output directory is not writable: {output_dir}"
                logging.error(error_message)
                self.error.emit(error_message)
                return

            # Check if font file exists
            if self.font and not os.path.exists(self.font):
                error_message = f"Font file not found: {self.font}"
                logging.error(error_message)
                self.error.emit(error_message)
                return

            command = self.generate_ffmpeg_command()
            if not command:
                self.error.emit("Failed to generate FFmpeg command")
                return

            logging.info(f"FFmpeg command: {' '.join(command)}")

            process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True
            )

            # Collect stderr output for detailed error reporting
            stderr_output = []
            duration = 0
            while True:
                line = process.stderr.readline()
                if not line:
                    break
                stderr_output.append(line)
                if "Duration" in line:
                    parts = line.split(",")
                    for part in parts:
                        if "Duration" in part:
                            time = part.split("Duration: ")[1].split(".")[0]
                            h, m, s = map(int, time.split(":"))
                            duration = h * 3600 + m * 60 + s
                            break
                if "time=" in line and duration:
                    time = line.split("time=")[1].split(" ")[0]
                    h, m, s = map(float, time.split(":"))
                    current = h * 3600 + m * 60 + s
                    progress = int((current / duration) * 100)
                    self.progress.emit(progress)

            process.wait()

            if process.returncode == 0:
                self.finished.emit(self.output_path)
            else:
                error_message = "".join(stderr_output)
                logging.error(f"FFmpeg error: {error_message}")
                self.error.emit(f"Error processing video. FFmpeg failed.\n{error_message}")

        except Exception as e:
            logging.error(f"Error in ProcessThread: {str(e)}")
            self.error.emit(f"Error processing video: {str(e)}")