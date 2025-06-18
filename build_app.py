# build_app.py - Builds the app while ensuring models are properly included
import os
import shutil
import subprocess
import sys
from pathlib import Path

def build_app():
    print("Building Whisper Transcriber...")
    
    for path in ["build", "dist/whisper-transcriber"]:
        if os.path.exists(path):
            print(f"Removing {path}")
            shutil.rmtree(path)
    
    home = Path.home()
    whisper_cache = home / ".cache" / "whisper"
    
    data_files = []
    data_files.append(("icon.ico", "."))
    
    if whisper_cache.exists():
        print(f"Found whisper models at {whisper_cache}")
        for model_file in whisper_cache.glob("*.pt"):
            print(f"Including model: {model_file.name}")
            data_files.append((str(model_file), "./models"))
    else:
        print("Warning: No whisper models found in cache")
    
    data_args = []
    for src, dst in data_files:
        data_args.extend(["--add-data", f"{src};{dst}"])
    
    with open("main_entry.py", "w") as f:
        f.write("""
import os
import sys
import tempfile

log_file = os.path.join(tempfile.gettempdir(), "whisper_log.txt")
with open(log_file, "w") as f:
    f.write(f"App started at {__import__('datetime').datetime.now()}\\n")
    f.write(f"Working directory: {os.getcwd()}\\n")
    
    models_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "models")
    if os.path.exists(models_dir):
        f.write(f"Models directory found at {models_dir}\\n")
        f.write(f"Models: {os.listdir(models_dir)}\\n")
    else:
        f.write("No models directory found!\\n")
    
    from src.whisper_transcriber.app import main
    
    if __name__ == "__main__":
        main()
""")
    
    cmd = [
        "pyinstaller",
        "--noconfirm",
        "--clean",
        "--name", "whisper-transcriber",
        "--icon", "icon.ico",
        "--noconsole",
        "--windowed",
        "--hidden-import", "whisper",
        "--hidden-import", "ffmpeg",
        "--hidden-import", "librosa",
    ] + data_args + ["main_entry.py"]
    
    print("Running PyInstaller...")
    print(f"Command: {' '.join(cmd)}")
    result = subprocess.run(cmd)
    
    dist_models = os.path.join("dist", "whisper-transcriber", "models")
    os.makedirs(dist_models, exist_ok=True)
    
    if whisper_cache.exists():
        for model_file in whisper_cache.glob("*.pt"):
            dest_path = os.path.join(dist_models, model_file.name)
            print(f"Copying {model_file} to {dest_path}")
            shutil.copy2(model_file, dest_path)
    
    return result.returncode

if __name__ == "__main__":
    exit_code = build_app()
    if exit_code == 0:
        print("Build successful!")
    else:
        print(f"Build failed with code {exit_code}")
    
    input("Press Enter to exit...")