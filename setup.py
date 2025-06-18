from setuptools import setup, find_packages

setup(
    name="whisper-transcriber",
    version="0.1.0",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    install_requires=[
        "openai-whisper",
        "imageio-ffmpeg",
        "librosa",
        "numpy",
        "tk"
    ],
    entry_points={
        "console_scripts": [
            "whisper-transcriber=whisper_transcriber.app:main",
        ],
    },
    python_requires=">=3.8",
)