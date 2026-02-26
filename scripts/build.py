"""Build script for Whisper Transcriber.

Compiles the Go backend binary and packages the Python UI with PyInstaller.
"""
import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CORE_DIR = PROJECT_ROOT / "core"
UI_DIR = PROJECT_ROOT / "ui"
DIST_DIR = PROJECT_ROOT / "dist"


def build_go_binary() -> Path:
    """Compile the Go backend binary for the current platform."""
    bin_dir = CORE_DIR / "bin"
    bin_dir.mkdir(exist_ok=True)

    binary_name = "wt-core"
    if platform.system() == "Windows":
        binary_name += ".exe"

    output_path = bin_dir / binary_name

    cmd = [
        "go", "build",
        "-ldflags=-s -w",
        "-o", str(output_path),
        "./cmd/wt-core/",
    ]

    result = subprocess.run(cmd, cwd=str(CORE_DIR), capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Go build failed:\n{result.stderr}", file=sys.stderr)
        sys.exit(1)

    print(f"Go binary built: {output_path}")
    return output_path


def copy_binary_to_ui(binary_path: Path) -> None:
    """Copy the Go binary into the UI package for PyInstaller bundling."""
    ui_bin = UI_DIR / "app" / "bin"
    ui_bin.mkdir(parents=True, exist_ok=True)
    dest = ui_bin / binary_path.name
    shutil.copy2(binary_path, dest)
    print(f"Binary copied to: {dest}")


def build_pyinstaller() -> None:
    """Bundle the Python UI with PyInstaller."""
    if DIST_DIR.exists():
        shutil.rmtree(DIST_DIR)

    icon_path = PROJECT_ROOT / "assets" / "icon.ico"
    icon_arg = ["--icon", str(icon_path)] if icon_path.exists() else []

    binary_name = "wt-core.exe" if platform.system() == "Windows" else "wt-core"
    bin_path = UI_DIR / "app" / "bin" / binary_name

    add_data_sep = ";" if platform.system() == "Windows" else ":"
    data_args = []
    if bin_path.exists():
        data_args = ["--add-data", f"{bin_path}{add_data_sep}app/bin"]

    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--noconfirm",
        "--clean",
        "--name", "WhisperTranscriber",
        "--noconsole",
        "--windowed",
        "--hidden-import", "faster_whisper",
        "--hidden-import", "customtkinter",
        "--hidden-import", "soundfile",
    ] + icon_arg + data_args + [
        str(UI_DIR / "app" / "main.py"),
    ]

    result = subprocess.run(cmd, cwd=str(PROJECT_ROOT))
    if result.returncode != 0:
        print("PyInstaller build failed", file=sys.stderr)
        sys.exit(1)

    print(f"Distribution built: {DIST_DIR / 'WhisperTranscriber'}")


def main() -> None:
    """Run the full build pipeline."""
    print("=== Building Whisper Transcriber ===")

    print("\n--- Step 1: Building Go binary ---")
    binary_path = build_go_binary()

    print("\n--- Step 2: Copying binary to UI ---")
    copy_binary_to_ui(binary_path)

    print("\n--- Step 3: Building PyInstaller bundle ---")
    build_pyinstaller()

    print("\n=== Build complete ===")


if __name__ == "__main__":
    main()
