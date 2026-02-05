import cv2
import tkinter as tk
from tkinter import Button
from ffpyplayer.player import MediaPlayer
import threading
import time
from PIL import Image, ImageTk

class VideoPlayer:
    def __init__(self, root):
        self.root = root
        self.root.title("Video Player")

        # Video quality paths
        self.quality_levels = {
            "Low Quality": "C:/College projects/3rd year/Design Patterns/Implementation/videofolder/ZrpEIw8IWwk_low.mp4",
            "Medium Quality": "C:/College projects/3rd year/Design Patterns/Implementation/videofolder/ZrpEIw8IWwk_medium.mp4",
            "High Quality": "C:/College projects/3rd year/Design Patterns/Implementation/videofolder/ZrpEIw8IWwk_high.mp4"
        }

        self.current_quality = "Medium Quality"
        self.cap = None
        self.player = None
        self.paused = False
        self.playing = False
        self.current_time = 0  # Store playback time

        # Create video canvas
        self.canvas = tk.Canvas(root, width=800, height=600)
        self.canvas.pack()

        # Quality buttons
        self.low_quality_btn = Button(root, text="Low Quality", command=lambda: self.switch_quality("Low Quality"))
        self.low_quality_btn.pack(side=tk.LEFT)

        self.medium_quality_btn = Button(root, text="Medium Quality", command=lambda: self.switch_quality("Medium Quality"))
        self.medium_quality_btn.pack(side=tk.LEFT)

        self.high_quality_btn = Button(root, text="High Quality", command=lambda: self.switch_quality("High Quality"))
        self.high_quality_btn.pack(side=tk.LEFT)

        # Playback buttons
        self.play_btn = Button(root, text="Play", command=self.play)
        self.play_btn.pack(side=tk.LEFT)

        self.pause_btn = Button(root, text="Pause", command=self.pause)
        self.pause_btn.pack(side=tk.LEFT)

        self.resume_btn = Button(root, text="Resume", command=self.resume)
        self.resume_btn.pack(side=tk.LEFT)

    def switch_quality(self, quality):
        """Switch video quality safely."""
        if not self.playing:
            print(f"Cannot switch to {quality}, no video is playing.")
            return

        if self.player:  
            self.current_time = self.player.get_pts()  # Save playback time
        else:
            self.current_time = 0  # Default to 0 if player is None

        print(f"Switching to {quality} at {self.current_time:.2f} seconds")

        self.stop_video()  # Stop the current video safely
        time.sleep(1)  # Allow time for FFmpeg to release resources
        self.current_quality = quality
        self.play(start_time=self.current_time)  # Resume at same position

    def play(self, start_time=0):
        """Play or resume video from a given timestamp."""
        if self.playing:
            return  # Prevent multiple play threads

        video_path = self.quality_levels[self.current_quality]
        print(f"Playing video: {video_path}")

        self.cap = cv2.VideoCapture(video_path)
        self.player = MediaPlayer(video_path)
        self.paused = False
        self.playing = True

        if not self.cap.isOpened():
            print("Error: Could not open video file")
            return

        # Seek to saved timestamp for smooth quality switch
        if start_time > 0:
            time.sleep(0.5)  # Give time for the player to initialize before seeking
            self.player.seek(start_time)

        # Start video thread
        self.video_thread = threading.Thread(target=self.update_frame, daemon=True)
        self.video_thread.start()

    def update_frame(self):
        """Update video frames and sync with audio."""
        while self.cap and self.cap.isOpened() and self.playing:
            if self.paused:
                time.sleep(0.1)  # Prevent CPU overuse while paused
                continue

            ret, frame = self.cap.read()
            if not ret:
                print("End of video")
                break

            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            frame = cv2.resize(frame, (800, 600))

            # Convert frame to a format tkinter can use
            frame = Image.fromarray(frame)
            self.photo = ImageTk.PhotoImage(frame)

            self.canvas.create_image(0, 0, anchor=tk.NW, image=self.photo)
            self.canvas.image = self.photo  # Keep reference to avoid garbage collection issues

            audio_frame, val = self.player.get_frame() if self.player else (None, None)
            if val != "eof" and audio_frame:
                self.player.get_frame()

            self.root.update()

        self.stop_video()  # Cleanup when video ends

    def pause(self):
        """Pause the video."""
        if self.player and self.playing:
            self.player.set_pause(True)
            self.paused = True
            self.current_time = self.player.get_pts() if self.player else 0  # Save time
            print("Video Paused")

    def resume(self):
        """Resume the video."""
        if self.player and self.playing:
            self.player.set_pause(False)
            self.paused = False
            print("Video Resumed")

    def stop_video(self):
        """Stop video playback and release resources properly."""
        if self.playing:
            self.playing = False  # Stop the playback loop

        if self.cap:
            self.cap.release()
            self.cap = None

        if self.player:
            try:
                self.player.close()  # Safely close MediaPlayer
            except AttributeError:
                pass  # Ignore if close() doesn't exist
            self.player = None  # Ensure it's fully released

        print("Video Stopped")
        cv2.destroyAllWindows()


if __name__ == "__main__":  # Fixed incorrect main check
    root = tk.Tk()
    player = VideoPlayer(root)
    root.mainloop()
