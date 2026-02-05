import cv2
import tkinter as tk
from tkinter import ttk
from ttkthemes import ThemedTk
from ttkthemes import ThemedStyle
from ffpyplayer.player import MediaPlayer
import threading
import pysubs2
from PIL import Image, ImageTk


class VideoPlayer:
    def __init__(self, root):
        self.root = root
        self.root.title("🎬 Stylish Video Player")
        self.root.geometry("900x700")
        self.root.configure(bg="#2E2E2E")  # Set background color

        # Apply a stylish theme
        style = ThemedStyle(root)
        style.set_theme("radiance")  # Try 'equilux', 'adapta', 'arc', etc.

        # Video quality levels
        self.quality_levels = {
            "Low Quality": "C:/College projects/3rd year/Design Patterns/Implementation/videofolder/ZrpEIw8IWwk_low.mp4",
            "Medium Quality": "C:/College projects/3rd year/Design Patterns/Implementation/videofolder/ZrpEIw8IWwk_medium.mp4",
            "High Quality": "C:/College projects/3rd year/Design Patterns/Implementation/videofolder/ZrpEIw8IWwk_high.mp4"
        }
        self.current_quality = "Medium Quality"
        self.video_path = self.quality_levels[self.current_quality]
        self.subtitle_path = "C:/College projects/3rd year/Design Patterns/Implementation/subtitles/subtitles_content.srt"
        self.subtitles = pysubs2.load(self.subtitle_path)

        self.cap = None
        self.player = None
        self.paused = False
        self.current_time = 0  # Track playback time

        # Create Video Display Canvas
        self.canvas = tk.Canvas(root, width=800, height=500, bg="black", highlightthickness=5, highlightbackground="#FF5733")  # Glowing border effect
        self.canvas.pack(pady=10)

        # Buttons Frame
        self.controls_frame = ttk.Frame(root, style="TFrame")
        self.controls_frame.pack(pady=10)

        # Quality Switch Buttons (Styled)
        self.style = ttk.Style()
        self.style.configure("TButton", font=("Arial", 12, "bold"), padding=5)
        self.style.map("TButton", background=[("active", "#FF5733")])  # Change color on hover

        self.low_quality_btn = ttk.Button(self.controls_frame, text="Low", command=lambda: self.switch_quality("Low Quality"), style="TButton")
        self.low_quality_btn.grid(row=0, column=0, padx=10)

        self.medium_quality_btn = ttk.Button(self.controls_frame, text="Medium", command=lambda: self.switch_quality("Medium Quality"), style="TButton")
        self.medium_quality_btn.grid(row=0, column=1, padx=10)

        self.high_quality_btn = ttk.Button(self.controls_frame, text="High", command=lambda: self.switch_quality("High Quality"), style="TButton")
        self.high_quality_btn.grid(row=0, column=2, padx=10)

        # Play / Pause / Resume Buttons
        self.play_btn = ttk.Button(self.controls_frame, text="▶ Play", command=self.play, style="TButton")
        self.play_btn.grid(row=0, column=3, padx=10)

        self.pause_btn = ttk.Button(self.controls_frame, text="⏸ Pause", command=self.pause, style="TButton")
        self.pause_btn.grid(row=0, column=4, padx=10)

        self.resume_btn = ttk.Button(self.controls_frame, text="⏯ Resume", command=self.resume, style="TButton")
        self.resume_btn.grid(row=0, column=5, padx=10)

        # Subtitle Label (Styled with a dark background)
        self.subtitle_label = tk.Label(root, text="Subtitles will appear here...", font=("Arial", 14, "bold"), fg="white", bg="#444444", wraplength=800, pady=10, padx=10)
        self.subtitle_label.pack(side=tk.BOTTOM, fill=tk.X)

    def display_subtitles(self, current_time):
        """Show subtitle for the current timestamp"""
        for subtitle in self.subtitles:
            if subtitle.start / 1000 <= current_time <= subtitle.end / 1000:
                self.subtitle_label.config(text=subtitle.text)
                return
        self.subtitle_label.config(text="")

    def switch_quality(self, quality):
        """Switch video quality while keeping the same timestamp"""
        if self.cap:
            self.current_time = self.cap.get(cv2.CAP_PROP_POS_MSEC) / 1000  # Get current timestamp
            print(f"Switching to {quality} at {self.current_time:.2f} seconds")
        
        self.current_quality = quality
        self.stop_video()
        self.play(resume_time=self.current_time)  # Pass the saved timestamp

    def play(self, resume_time=0):
        """Plays the video from the given timestamp"""
        self.video_path = self.quality_levels[self.current_quality]
        print(f"Playing video: {self.video_path} from {resume_time:.2f} seconds")
        
        if self.cap:
            self.cap.release()
        if self.player:
            self.player.close()
        
        self.cap = cv2.VideoCapture(self.video_path)
        self.player = MediaPlayer(self.video_path)
        self.paused = False

        if resume_time > 0:
            self.cap.set(cv2.CAP_PROP_POS_MSEC, resume_time * 1000)  # Seek to timestamp

        def update_frame():
            while self.cap.isOpened():
                if self.paused:
                    continue
                ret, frame = self.cap.read()
                audio_frame, val = self.player.get_frame()
                if not ret:
                    break
                
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                frame = cv2.resize(frame, (800, 500))
                self.photo = ImageTk.PhotoImage(image=Image.fromarray(frame))
                self.canvas.create_image(0, 0, anchor=tk.NW, image=self.photo)
                
                if val != "eof" and audio_frame:
                    self.player.get_frame()
                
                self.current_time = self.cap.get(cv2.CAP_PROP_POS_MSEC) / 1000  # Update timestamp
                self.display_subtitles(self.current_time)  # Update subtitle display
                
                self.root.update()
            
            self.stop_video()
        
        threading.Thread(target=update_frame, daemon=True).start()

    def stop_video(self):
        """Stops the video"""
        if self.cap:
            self.cap.release()
            self.cap = None
        if self.player:
            self.player = None  
        print("Video Stopped Successfully")

    def pause(self):
        """Pauses the video"""
        if self.player:
            self.player.set_pause(True)
            self.paused = True
            print("Video Paused")

    def resume(self):
        """Resumes the video"""
        if self.player:
            self.player.set_pause(False)
            self.paused = False
            print("Video Resumed")


if __name__ == "__main__":
    root = ThemedTk(theme="breeze")  # Try "arc", "radiance", "equilux" for different themes
    player = VideoPlayer(root)
    root.mainloop()