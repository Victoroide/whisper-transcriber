import os
import sys
import tempfile

log_file = os.path.join(tempfile.gettempdir(), "whisper_transcriber_log.txt")
with open(log_file, 'w', encoding='utf-8') as f:
    f.write(f"Starting application at {__import__('datetime').datetime.now()}\n")
    f.write(f"Python: {sys.version}\n")
    f.write(f"Working directory: {os.getcwd()}\n\n")

try:
    project_root = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, project_root)
    
    from src.whisper_transcriber.app import main
    
    if __name__ == "__main__":
        main()
        
except Exception as e:
    import traceback
    with open(log_file, 'a', encoding='utf-8') as f:
        f.write(f"ERROR: {str(e)}\n")
        f.write(traceback.format_exc())
    
    import tkinter as tk
    from tkinter import messagebox
    root = tk.Tk()
    root.withdraw()
    messagebox.showerror("Error", f"An error occurred:\n{str(e)}\n\nCheck log: {log_file}")
    sys.exit(1)