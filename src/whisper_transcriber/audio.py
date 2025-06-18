import subprocess
import os
import librosa
import numpy as np
from tkinter import Tk, filedialog
import subprocess
import sys

_original_popen = subprocess.Popen

def _silent_popen(*args, **kwargs):
    if 'creationflags' not in kwargs and sys.platform == 'win32':
        kwargs['creationflags'] = 0x08000000  # CREATE_NO_WINDOW
    return _original_popen(*args, **kwargs)

subprocess.Popen = _silent_popen

def select_video():
    root = Tk()
    root.withdraw()
    video_path = filedialog.askopenfilename(
        title="Select a video file",
        filetypes=[("Video files", "*.mp4 *.avi *.mov *.mkv *.flv *.wmv *.webm"), ("All files", "*.*")]
    )
    return video_path

def extract_audio_with_ffmpeg(video_path, output_path):
    from imageio_ffmpeg import get_ffmpeg_exe
    ffmpeg_path = get_ffmpeg_exe()
    
    print(f"Using ffmpeg: {ffmpeg_path}")
    print(f"Extracting audio from: {video_path}")
    print(f"Saving audio to: {output_path}")
    
    cmd = [
        ffmpeg_path,
        "-i", video_path,
        "-vn",
        "-acodec", "pcm_s16le",
        "-ar", "16000",
        "-ac", "1",
        "-y",
        output_path
    ]
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print("Audio extracted successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error extracting audio: {e}")
        print(f"STDERR: {e.stderr}")
        return False

def load_audio_manually(audio_path):
    try:
        print(f"Loading audio from: {audio_path}")
        audio_array, sampling_rate = librosa.load(audio_path, sr=16000)
        print(f"Audio loaded successfully: {len(audio_array)} samples")
        return audio_array, sampling_rate
    except Exception as e:
        print(f"Error loading audio: {e}")
        return None, None