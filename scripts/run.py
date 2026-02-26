"""Development launcher for Whisper Transcriber.

Builds the Go binary if missing or outdated, then starts the Python UI.
"""
import os
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CORE_DIR = PROJECT_ROOT / "core"


def needs_rebuild() -> bool:
    """Check if the Go binary needs to be rebuilt."""
    import platform as plat
    binary_name = "wt-core.exe" if plat.system() == "Windows" else "wt-core"
    binary_path = CORE_DIR / "bin" / binary_name

    if not binary_path.exists():
        return True

    # Check if any .go files are newer than the binary
    binary_mtime = binary_path.stat().st_mtime
    for go_file in CORE_DIR.rglob("*.go"):
        if go_file.stat().st_mtime > binary_mtime:
            return True

    return False


def build_go() -> bool:
    """Build the Go backend binary."""
    print("Building Go backend...")
    result = subprocess.run(
        ["go", "build", "-o", str(CORE_DIR / "bin" / "wt-core"), "./cmd/wt-core/"],
        cwd=str(CORE_DIR),
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print(f"Go build failed:\n{result.stderr}", file=sys.stderr)
        return False
    print("Go binary built successfully")
    return True


def main() -> None:
    """Launch the application in development mode."""
    if needs_rebuild():
        if not build_go():
            print("Continuing without Go core (standalone mode)")

    env = os.environ.copy()
    env["PYTHONPATH"] = str(PROJECT_ROOT)

    subprocess.run(
        [sys.executable, "-m", "ui.app.main"],
        cwd=str(PROJECT_ROOT),
        env=env,
    )


if __name__ == "__main__":
    main()
