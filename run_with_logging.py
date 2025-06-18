#!/usr/bin/env python3
"""
Main entry point for Whisper Transcriber with enhanced logging and model management
"""
import os
import sys
import traceback
import tempfile
import shutil
import tkinter as tk
from tkinter import messagebox
from pathlib import Path

log_file = os.path.join(tempfile.gettempdir(), "whisper_transcriber_log.txt")
print(f"Logging to: {log_file}")

with open(log_file, 'w', encoding='utf-8') as f:
    f.write(f"=== Whisper Transcriber Log ===\n")
    f.write(f"Started at: {__import__('datetime').datetime.now()}\n")
    f.write(f"Python version: {sys.version}\n")
    f.write(f"Current directory: {os.getcwd()}\n\n")

sys.stdout = open(log_file, 'a', encoding='utf-8')
sys.stderr = sys.stdout

try:
    project_root = os.path.dirname(os.path.abspath(sys.argv[0]))
    sys.path.insert(0, project_root)
    print(f"Added {project_root} to sys.path")
    
    app_data_dir = os.path.join(os.getenv('APPDATA', '.'), 'WhisperTranscriber')
    os.makedirs(app_data_dir, exist_ok=True)
    print(f"Using app data directory: {app_data_dir}")
    
    os.environ["PYTHONPATH"] = os.pathsep.join([project_root] + sys.path)
    os.environ["XDG_CACHE_HOME"] = app_data_dir
    os.environ["WHISPER_CACHE_DIR"] = os.path.join(app_data_dir, 'models')
    os.makedirs(os.environ["WHISPER_CACHE_DIR"], exist_ok=True)
    print(f"Whisper cache directory: {os.environ['WHISPER_CACHE_DIR']}")
    
    bundled_models = os.path.join(project_root, 'models')
    if os.path.exists(bundled_models):
        print(f"Found bundled models at {bundled_models}")
        for model_file in os.listdir(bundled_models):
            src = os.path.join(bundled_models, model_file)
            dst = os.path.join(os.environ["WHISPER_CACHE_DIR"], model_file)
            if not os.path.exists(dst):
                print(f"Copying model: {model_file}")
                shutil.copy2(src, dst)
    
    print("Testing whisper import...")
    import whisper
    print(f"Whisper version: {whisper.__version__}")
    
    print("Checking if models are available...")
    try:
        print(f"Using model directory: {os.environ['WHISPER_CACHE_DIR']}")
        available_models = [f.name for f in Path(os.environ["WHISPER_CACHE_DIR"]).glob("*.pt")]
        print(f"Available models: {available_models}")
        
        if not available_models:
            print("No models found. Attempting to download tiny model...")
            model = whisper.load_model("tiny", download_root=os.environ["WHISPER_CACHE_DIR"])
            print("Successfully downloaded tiny model")
    except Exception as e:
        print(f"Warning: Model check failed: {e}")
    
    print("Importing dependencies...")
    import numpy
    import torch
    print(f"NumPy version: {numpy.__version__}")
    print(f"PyTorch version: {torch.__version__}")
    print(f"CUDA available: {torch.cuda.is_available()}")
    
    print("Importing application...")
    from src.whisper_transcriber.app import main
    
    print("Starting application...")
    
    import src.whisper_transcriber.transcription
    original_transcribe = src.whisper_transcriber.transcription.transcribe_with_whisper
    
    def transcribe_with_logging(*args, **kwargs):
        try:
            print(f"Transcribing with args: {args}")
            print(f"Kwargs: {kwargs}")
            result = original_transcribe(*args, **kwargs)
            print(f"Transcription completed successfully")
            return result
        except Exception as e:
            print(f"ERROR in transcription: {e}")
            print(traceback.format_exc())
            raise
    
    src.whisper_transcriber.transcription.transcribe_with_whisper = transcribe_with_logging
    
    if __name__ == "__main__":
        main()
        
except Exception as e:
    print(f"CRITICAL ERROR: {e}")
    print(traceback.format_exc())
    
    try:
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror(
            "Whisper Transcriber Error", 
            f"An error occurred:\n{str(e)}\n\nSee log at:\n{log_file}"
        )
    except:
        pass
    
    sys.exit(1)