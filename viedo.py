import cv2
import tkinter as tk
from tkinter import Button
from ffpyplayer.player import MediaPlayer
import time
import threading
from PIL import Image, ImageTk

class VideoPlayer:
    def __init__(self, root):
        self.root = root
        self.root.title("Video Player")

        # Video Quality Options
        self.quality_levels = {
            "Low Quality": "C:/College projects/3rd year/Design Patterns/Implementation/videofolder/ZrpEIw8IWwk_low.mp4",
            "Medium Quality": "C:/College projects/3rd year/Design Patterns/Implementation/videofolder/ZrpEIw8IWwk_medium.mp4",
            "High Quality": "C:/College projects/3rd year/Design Patterns/Implementation/videofolder/ZrpEIw8IWwk_high.mp4"
        }
        self.current_quality = "Medium Quality"

        # Video & Player State
        self.cap = None  # OpenCV Video Capture
        self.player = None  # FFpyPlayer MediaPlayer
        self.paused = False  # Video Pause State

        # UI Elements
        self.canvas = tk.Canvas(root, width=800, height=600)
        self.canvas.pack()

        self.low_quality_btn = Button(root, text="Low Quality", command=lambda: self.switch_quality("Low Quality"))
        self.low_quality_btn.pack(side=tk.LEFT)

        self.medium_quality_btn = Button(root, text="Medium Quality", command=lambda: self.switch_quality("Medium Quality"))
        self.medium_quality_btn.pack(side=tk.LEFT)

        self.high_quality_btn = Button(root, text="High Quality", command=lambda: self.switch_quality("High Quality"))
        self.high_quality_btn.pack(side=tk.LEFT)

        self.play_btn = Button(root, text="Play", command=self.play)
        self.play_btn.pack(side=tk.LEFT)

        self.pause_btn = Button(root, text="Pause", command=self.pause)
        self.pause_btn.pack(side=tk.LEFT)

        self.resume_btn = Button(root, text="Resume", command=self.resume)
        self.resume_btn.pack(side=tk.LEFT)

        self.subtitle_label = tk.Label(root, text="", font=("Arial", 14), fg="white", bg="black")
        self.subtitle_label.pack(side=tk.BOTTOM, fill=tk.X)

    def switch_quality(self, quality):
        """Switch video quality and print status"""
        self.current_quality = quality
        print(f"Switched to {quality}")

    def play(self):
        """Play the selected video"""
        if self.cap and self.cap.isOpened():
            print("Video is already playing!")
            return  # Prevent multiple playbacks

        video_path = self.quality_levels[self.current_quality]
        print(f"Playing video: {video_path}")

        self.cap = cv2.VideoCapture(video_path)
        self.player = MediaPlayer(video_path)
        self.paused = False  # Reset pause state when playing a new video

        if not self.cap.isOpened():
            print("Error: Could not open video file")
            return

        # Start the video playback in a separate thread
        threading.Thread(target=self.update_frame, daemon=True).start()

    def update_frame(self):
        """Update the video frame in the Tkinter canvas"""
        while self.cap.isOpened():
            if self.paused:
                time.sleep(0.1)  # Pause loop while paused
                continue

            ret, frame = self.cap.read()
            audio_frame, val = self.player.get_frame()

            if not ret:
                print("End of video")
                break

            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            frame = cv2.resize(frame, (800, 600))

            # Convert frame to Tkinter-compatible format
            self.photo = tk.PhotoImage(data=cv2.imencode('.png', frame)[1].tobytes())
            self.canvas.create_image(0, 0, anchor=tk.NW, image=self.photo)

            if val != "eof" and audio_frame:
                self.player.get_frame()

            self.root.update()

        self.cap.release()
        cv2.destroyAllWindows()

    def pause(self):
        """Pause the video playback"""
        if self.player:
            self.player.set_pause(True)
            self.paused = True
            print("Video Paused")

    def resume(self):
        """Resume the video playback"""
        if self.player:
            self.player.set_pause(False)
            self.paused = False
            print("Video Resumed")

# Run the Tkinter application
if __name__ == "__main__":
    root = tk.Tk()
    player = VideoPlayer(root)
    root.mainloop()
