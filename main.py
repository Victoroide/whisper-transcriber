#!/usr/bin/env python3
"""
Main entry point for Whisper Transcriber
"""
import os
import sys
import tkinter as tk

project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from src.whisper_transcriber.app import main

if __name__ == "__main__":
    main()