import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import os
import threading
import datetime
import sys
import signal
from src.whisper_transcriber.audio import select_video, extract_audio_with_ffmpeg, load_audio_manually
from src.whisper_transcriber.transcription import process_long_audio, transcribe_with_whisper

class RoundedFrame(tk.Canvas):
    def __init__(self, parent, bg='white', corner_radius=10, **kwargs):
        tk.Canvas.__init__(self, parent, **kwargs)
        self.bg = bg
        self.corner_radius = corner_radius
        self.configure(bg=self.bg, bd=0, highlightthickness=0)
        self.bind("<Configure>", self._on_configure)

    def _on_configure(self, event):
        self.delete("all")
        width, height = event.width, event.height
        self.create_rounded_rect(0, 0, width, height, self.corner_radius, fill=self.bg, outline="")

    def create_rounded_rect(self, x1, y1, x2, y2, radius=10, **kwargs):
        points = [
            x1+radius, y1,
            x2-radius, y1,
            x2, y1,
            x2, y1+radius,
            x2, y2-radius,
            x2, y2,
            x2-radius, y2,
            x1+radius, y2,
            x1, y2,
            x1, y2-radius,
            x1, y1+radius,
            x1, y1
        ]
        return self.create_polygon(points, **kwargs, smooth=True)

class TranscriptionApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Whisper Transcriber")
        self.root.geometry("900x650")
        
        self.colors = {
            "bg": "#ffffff",
            "accent": "#4b6bfb",
            "text": "#18181b",
            "secondary": "#71717a",
            "border": "#e9e9ec",
            "success": "#10b981"
        }
        
        self.fonts = {
            "normal": ("Segoe UI", 11),
            "bold": ("Segoe UI", 11, "bold"),
            "heading": ("Segoe UI", 16, "bold")
        }
        
        self.root.configure(bg=self.colors["bg"])
        self.style = ttk.Style()
        self.style.theme_use('clam')
        self.configure_styles()
        
        self.main_frame = tk.Frame(root, bg=self.colors["bg"], padx=30, pady=20)
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        header = tk.Frame(self.main_frame, bg=self.colors["bg"], pady=10)
        header.pack(fill=tk.X)
        
        title = tk.Label(
            header, 
            text="Whisper Transcriber", 
            font=self.fonts["heading"], 
            bg=self.colors["bg"], 
            fg=self.colors["text"]
        )
        title.pack(side=tk.LEFT)
        
        subtitle = tk.Label(
            header, 
            text="Convert speech to text with AI", 
            font=self.fonts["normal"], 
            bg=self.colors["bg"], 
            fg=self.colors["secondary"],
            padx=15
        )
        subtitle.pack(side=tk.LEFT)
        
        action_frame = tk.Frame(self.main_frame, bg=self.colors["bg"], pady=15)
        action_frame.pack(fill=tk.X)
        
        self.select_btn = tk.Button(
            action_frame, 
            text="Select Video", 
            font=self.fonts["bold"],
            bg=self.colors["accent"],
            fg="white",
            activebackground="#3151e8",
            activeforeground="white",
            bd=0,
            relief=tk.FLAT,
            padx=12,
            pady=6,
            cursor="hand2",
            command=self.select_video
        )
        self.select_btn.pack(side=tk.LEFT, padx=(0, 15))
        
        model_label = tk.Label(
            action_frame, 
            text="Model Size:", 
            font=self.fonts["normal"], 
            bg=self.colors["bg"], 
            fg=self.colors["text"]
        )
        model_label.pack(side=tk.LEFT, padx=(0, 10))
        
        self.model_var = tk.StringVar(value="medium")
        self.model_combo = ttk.Combobox(
            action_frame, 
            textvariable=self.model_var,
            values=["tiny", "base", "small", "medium", "large"],
            width=10,
            state="readonly"
        )
        self.model_combo.pack(side=tk.LEFT)
        
        self.save_btn = tk.Button(
            action_frame, 
            text="Save Transcription",
            font=self.fonts["normal"],
            bg=self.colors["bg"],
            fg=self.colors["text"],
            activebackground=self.colors["border"],
            activeforeground=self.colors["text"],
            bd=0,
            relief=tk.FLAT,
            padx=12,
            pady=6,
            cursor="hand2",
            command=self.save_transcription,
            state=tk.DISABLED
        )
        self.save_btn.pack(side=tk.RIGHT)
        
        progress_frame = tk.Frame(self.main_frame, bg=self.colors["bg"], pady=5)
        progress_frame.pack(fill=tk.X)
        
        status_progress_frame = tk.Frame(progress_frame, bg=self.colors["bg"])
        status_progress_frame.pack(fill=tk.X)
        
        self.status_label = tk.Label(
            status_progress_frame, 
            text="Ready", 
            font=self.fonts["normal"], 
            bg=self.colors["bg"], 
            fg=self.colors["secondary"],
            anchor=tk.W
        )
        self.status_label.pack(side=tk.TOP, anchor=tk.W, pady=(0, 3))
        
        self.progress = ttk.Progressbar(
            status_progress_frame,
            orient="horizontal",
            length=100,
            mode="determinate",
            style="TProgressbar"
        )
        self.progress.pack(fill=tk.X, side=tk.TOP, pady=(0, 5))
        
        text_frame = RoundedFrame(
            self.main_frame,
            bg="white",
            corner_radius=8,
            highlightthickness=1,
            highlightbackground=self.colors["border"]
        )
        text_frame.pack(fill=tk.BOTH, expand=True, pady=(10, 0))
        
        inner_frame = tk.Frame(text_frame, bg="white", bd=0, highlightthickness=0)
        inner_frame.pack(fill=tk.BOTH, expand=True, padx=3, pady=3)
        
        # First create the text box
        self.text_box = tk.Text(
            inner_frame, 
            font=("Segoe UI", 12),
            bg="white", 
            fg=self.colors["text"],
            wrap=tk.WORD, 
            padx=20, 
            pady=20,
            bd=0,
            highlightthickness=0,
            relief=tk.FLAT
        )
        
        # Then create the scrollbar frame
        scrollbar_style_frame = tk.Frame(inner_frame, bg="white", width=16)
        scrollbar_style_frame.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Now create the scrollbar and connect it to the text box
        scrollbar = ttk.Scrollbar(
            scrollbar_style_frame, 
            command=self.text_box.yview
        )
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y, padx=4)
        
        # Connect the scrollbar to the text box and pack the text box
        self.text_box.config(yscrollcommand=scrollbar.set)
        self.text_box.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        self.video_path = None
        self.transcription_in_progress = False
        self.transcription_complete = False
        self.processing_thread = None
        self.stop_requested = False
        
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    def configure_styles(self):
        self.style.configure("TFrame", background=self.colors["bg"])
        
        self.style.configure("TProgressbar",
                           thickness=6,
                           borderwidth=0,
                           troughcolor="#EDF2F7",
                           background=self.colors["accent"])
                           
        self.style.configure("TScrollbar",
                           troughcolor="white",
                           background="#CBD5E0",
                           arrowcolor=self.colors["accent"],
                           borderwidth=0,
                           width=8)
        
        self.style.map("TScrollbar",
                     background=[('active', self.colors["accent"]),
                               ('!active', '#CBD5E0')])
        
        self.style.configure("TCombobox",
                           background="white",
                           fieldbackground="white",
                           foreground=self.colors["text"],
                           arrowsize=13,
                           padding=(5, 4),
                           borderwidth=1)
        
        self.style.map("TCombobox",
                     fieldbackground=[('readonly', 'white')],
                     selectbackground=[('readonly', 'white')],
                     selectforeground=[('readonly', self.colors["text"])])
    
    def select_video(self):
        video_path = select_video()
        if not video_path:
            return
            
        self.video_path = video_path
        
        self.text_box.delete(1.0, tk.END)
        self.text_box.insert(tk.END, "Processing video... please wait\n\n")
        
        self.progress["value"] = 0
        self.status_label.config(text="Preparing...")
        self.save_btn.config(state=tk.DISABLED)
        self.select_btn.config(state=tk.DISABLED)
        self.transcription_in_progress = True
        self.transcription_complete = False
        self.stop_requested = False
        
        self.processing_thread = threading.Thread(target=self.process_video)
        self.processing_thread.daemon = True
        self.processing_thread.start()
    
    def update_progress(self, value, message):
        if self.stop_requested:
            return
        self.progress["value"] = value
        self.status_label.config(text=message)
        self.root.update_idletasks()
    
    def update_transcription_text(self, text, append=False):
        if self.stop_requested:
            return
        if not append:
            self.text_box.delete(1.0, tk.END)
            self.text_box.insert(tk.END, text)
        else:
            self.text_box.insert(tk.END, text)
        self.text_box.see(tk.END)
        self.root.update_idletasks()
    
    def process_video(self):
        try:
            now = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            temp_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "temp")
            os.makedirs(temp_dir, exist_ok=True)
            audio_path = os.path.join(temp_dir, f"audio_{now}.wav")
            
            self.update_progress(10, "Extracting audio...")
            if not extract_audio_with_ffmpeg(self.video_path, audio_path):
                self.root.after(0, lambda: self.show_error("Failed to extract audio from video"))
                return
            
            if self.stop_requested:
                return
                
            self.update_progress(30, "Loading audio...")
            try:
                audio_array, sr = load_audio_manually(audio_path)
                if audio_array is None:
                    self.root.after(0, lambda: self.show_error("Failed to load audio file"))
                    return
            except Exception as e:
                self.root.after(0, lambda: self.show_error(f"Error loading audio: {str(e)}"))
                return
            
            if self.stop_requested:
                return
                
            model_size = self.model_var.get()
            self.update_progress(40, f"Transcribing with {model_size} model...")
            
            self.root.after(0, lambda: self.text_box.delete(1.0, tk.END))
            
            def segment_callback(text):
                if self.stop_requested:
                    return
                self.root.after(0, lambda t=text: self.update_transcription_text(t + "\n", append=True))
            
            try:
                audio_length = len(audio_array) / sr
                if audio_length > 300:
                    process_long_audio(audio_array, model_size, self.update_progress, segment_callback)
                else:
                    transcribe_with_whisper(audio_array, model_size, self.update_progress, segment_callback)
            except Exception as e:
                self.root.after(0, lambda: self.show_error(f"Transcription error: {str(e)}"))
                return
            
            if not self.stop_requested:
                self.root.after(0, lambda: self.finalize_transcription())
        
        except Exception as e:
            if not self.stop_requested:
                self.root.after(0, lambda: self.show_error(f"Error: {str(e)}"))
        
        finally:
            if 'audio_path' in locals() and os.path.exists(audio_path):
                try:
                    os.remove(audio_path)
                except:
                    pass
            
            if not self.stop_requested:
                self.root.after(0, lambda: self.select_btn.config(state=tk.NORMAL))
                self.transcription_in_progress = False
    
    def finalize_transcription(self):
        self.save_btn.config(state=tk.NORMAL)
        self.status_label.config(text="Transcription complete")
        self.progress["value"] = 100
        self.transcription_complete = True
    
    def show_error(self, message):
        self.update_progress(0, "Error")
        messagebox.showerror("Error", message)
        self.text_box.delete(1.0, tk.END)
        self.text_box.insert(tk.END, f"Error: {message}")
    
    def save_transcription(self):
        if not self.transcription_complete:
            return
            
        text = self.text_box.get(1.0, tk.END).strip()
        if not text:
            messagebox.showinfo("Info", "No text to save")
            return
            
        if self.video_path:
            video_name = os.path.splitext(os.path.basename(self.video_path))[0]
            default_filename = f"{video_name}_transcription.txt"
        else:
            now = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            default_filename = f"transcription_{now}.txt"
        
        save_path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
            initialfile=default_filename
        )
        
        if save_path:
            with open(save_path, "w", encoding="utf-8") as f:
                f.write(text)
            
            self.show_success_toast(f"Saved to {os.path.basename(save_path)}")
    
    def show_success_toast(self, message):
        toast = tk.Toplevel(self.root)
        toast.overrideredirect(True)
        toast.attributes('-topmost', True)
        
        toast_frame = RoundedFrame(toast, bg=self.colors["success"], corner_radius=10, width=300, height=60)
        toast_frame.pack(padx=0, pady=0)
        
        label = tk.Label(
            toast_frame, 
            text=f"✓ {message}",
            fg="white",
            bg=self.colors["success"],
            font=self.fonts["bold"]
        )
        label.place(relx=0.5, rely=0.5, anchor=tk.CENTER)
        
        toast.update_idletasks()
        x = self.root.winfo_x() + self.root.winfo_width() - toast_frame.winfo_width() - 20
        y = self.root.winfo_y() + self.root.winfo_height() - toast_frame.winfo_height() - 20
        toast.geometry(f"+{x}+{y}")
        
        toast.after(3000, toast.destroy)
    
    def on_closing(self):
        if self.transcription_in_progress:
            if messagebox.askokcancel("Quit", "Transcription is in progress. Do you want to quit anyway?"):
                self.stop_requested = True
                self.root.after(100, self._force_quit)
        else:
            self._force_quit()
    
    def _force_quit(self):
        self.root.destroy()
        sys.exit(0)

def main():
    root = tk.Tk()
    
    try:
        icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "icon.ico")
        if os.path.exists(icon_path):
            root.iconbitmap(icon_path)
    except:
        pass
    
    app = TranscriptionApp(root)
    
    def signal_handler(sig, frame):
        root.destroy()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    
    def check_signals():
        root.after(100, check_signals)
    
    check_signals()
    root.mainloop()

if __name__ == "__main__":
    main()