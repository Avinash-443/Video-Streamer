import cv2
import tkinter as tk
from tkinter import ttk
from ttkthemes import ThemedTk
from ttkthemes import ThemedStyle
from ffpyplayer.player import MediaPlayer
import threading
import pysubs2
from PIL import Image, ImageTk
from abc import ABC, abstractmethod

# ========================== State Pattern ==========================

class PlayerState(ABC):
    @abstractmethod
    def play(self, context, resume_time=0): pass

    @abstractmethod
    def pause(self, context): pass

    @abstractmethod
    def resume(self, context): pass

class PlayingState(PlayerState):
    def play(self, context, resume_time=0):
        pass  # Already playing

    def pause(self, context):
        context._pause_internal()
        context.set_state(PausedState())

    def resume(self, context):
        pass  # Already playing

class PausedState(PlayerState):
    def play(self, context, resume_time=0):
        context._play_internal(resume_time)
        context.set_state(PlayingState())

    def pause(self, context):
        pass  # Already paused

    def resume(self, context):
        context._resume_internal()
        context.set_state(PlayingState())

class StoppedState(PlayerState):
    def play(self, context, resume_time=0):
        context._play_internal(resume_time)
        context.set_state(PlayingState())

    def pause(self, context): pass

    def resume(self, context): pass

# ========================== Decorator Pattern Core ==========================

class IVideoPlayer(ABC):
    @abstractmethod
    def play(self, resume_time=0): pass

    @abstractmethod
    def pause(self): pass

    @abstractmethod
    def resume(self): pass

    @abstractmethod
    def stop_video(self): pass

class BasicVideoPlayer(IVideoPlayer):
    def __init__(self, video_path):
        self.video_path = video_path
        self.cap = None
        self.player = None
        self.paused = False
        self.current_time = 0

    def play(self, resume_time=0):
        if self.cap:
            self.cap.release()
        if self.player:
            self.player.close()
        self.cap = cv2.VideoCapture(self.video_path)
        self.player = MediaPlayer(self.video_path)
        self.paused = False
        if resume_time > 0:
            self.cap.set(cv2.CAP_PROP_POS_MSEC, resume_time * 1000)

    def pause(self):
        if self.player:
            self.player.set_pause(True)
            self.paused = True

    def resume(self):
        if self.player:
            self.player.set_pause(False)
            self.paused = False

    def stop_video(self):
        if self.cap:
            self.cap.release()
            self.cap = None
        if self.player:
            self.player = None

class VideoPlayerDecorator(IVideoPlayer):
    def __init__(self, player: IVideoPlayer):
        self._player = player

    def play(self, resume_time=0):
        self._player.play(resume_time)

    def pause(self):
        self._player.pause()

    def resume(self):
        self._player.resume()

    def stop_video(self):
        self._player.stop_video()

# ========================== Feature Decorators ==========================

class SubtitleDecorator(VideoPlayerDecorator):
    def __init__(self, player, subtitle_path, subtitle_label):
        super().__init__(player)
        self.subtitle_label = subtitle_label
        self.subtitles = pysubs2.load(subtitle_path)

    def display_subtitles(self, current_time):
        for subtitle in self.subtitles:
            if subtitle.start / 1000 <= current_time <= subtitle.end / 1000:
                self.subtitle_label.config(text=subtitle.text)
                return
        self.subtitle_label.config(text="")

class QualitySwitchDecorator(VideoPlayerDecorator):
    def __init__(self, player, quality_levels, canvas, root, subtitle_decorator=None):
        super().__init__(player)
        self.quality_levels = quality_levels
        self.current_quality = "Medium Quality"
        self.video_path = self.quality_levels[self.current_quality]
        self.canvas = canvas
        self.root = root
        self.cap = None
        self.player = None
        self.paused = False
        self.photo = None
        self.subtitle_decorator = subtitle_decorator
        self.current_time = 0
        self.state = StoppedState()

    def set_state(self, state: PlayerState):
        self.state = state

    def switch_quality(self, quality):
        if self.cap:
            self.current_time = self.cap.get(cv2.CAP_PROP_POS_MSEC) / 1000
        self.current_quality = quality
        self.video_path = self.quality_levels[self.current_quality]
        self.stop_video()
        self.play(self.current_time)

    def play(self, resume_time=0):
        self.state.play(self, resume_time)

    def pause(self):
        self.state.pause(self)

    def resume(self):
        self.state.resume(self)

    def _play_internal(self, resume_time=0):
        self.video_path = self.quality_levels[self.current_quality]
        self.cap = cv2.VideoCapture(self.video_path)
        self.player = MediaPlayer(self.video_path)
        self.paused = False

        if resume_time > 0:
            self.cap.set(cv2.CAP_PROP_POS_MSEC, resume_time * 1000)

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

                self.current_time = self.cap.get(cv2.CAP_PROP_POS_MSEC) / 1000
                if self.subtitle_decorator:
                    self.subtitle_decorator.display_subtitles(self.current_time)

                self.root.update()

            self.stop_video()

        threading.Thread(target=update_frame, daemon=True).start()

    def _pause_internal(self):
        if self.player:
            self.player.set_pause(True)
            self.paused = True

    def _resume_internal(self):
        if self.player:
            self.player.set_pause(False)
            self.paused = False

    def stop_video(self):
        if self.cap:
            self.cap.release()
            self.cap = None
        if self.player:
            self.player = None
        self.set_state(StoppedState())

# ========================== GUI Setup ==========================

class VideoPlayerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("🎬 Stylish Video Player")
        self.root.geometry("900x700")
        self.root.configure(bg="#2E2E2E")

        style = ThemedStyle(root)
        style.set_theme("radiance")

        self.quality_levels = {
            "Low Quality": "C:/College projects/3rd year/Design Patterns/Implementation/videofolder/ZrpEIw8IWwk_low.mp4",
            "Medium Quality": "C:/College projects/3rd year/Design Patterns/Implementation/videofolder/ZrpEIw8IWwk_medium.mp4",
            "High Quality": "C:/College projects/3rd year/Design Patterns/Implementation/videofolder/ZrpEIw8IWwk_high.mp4"
        }

        self.subtitle_path = "C:/College projects/3rd year/Design Patterns/Implementation/subtitles/subtitles_content.srt"

        self.canvas = tk.Canvas(root, width=800, height=500, bg="black", highlightthickness=5, highlightbackground="#FF5733")
        self.canvas.pack(pady=10)

        self.controls_frame = ttk.Frame(root, style="TFrame")
        self.controls_frame.pack(pady=10)

        self.subtitle_label = tk.Label(root, text="Subtitles will appear here...", font=("Arial", 14, "bold"), fg="white", bg="#444444", wraplength=800, pady=10, padx=10)
        self.subtitle_label.pack(side=tk.BOTTOM, fill=tk.X)

        base_player = BasicVideoPlayer(self.quality_levels["Medium Quality"])
        subtitle_decorator = SubtitleDecorator(base_player, self.subtitle_path, self.subtitle_label)
        self.video_player = QualitySwitchDecorator(subtitle_decorator, self.quality_levels, self.canvas, root, subtitle_decorator)

        # Buttons
        self.style = ttk.Style()
        self.style.configure("TButton", font=("Arial", 12, "bold"), padding=5)
        self.style.map("TButton", background=[("active", "#FF5733")])

        ttk.Button(self.controls_frame, text="Low", command=lambda: self.video_player.switch_quality("Low Quality"), style="TButton").grid(row=0, column=0, padx=10)
        ttk.Button(self.controls_frame, text="Medium", command=lambda: self.video_player.switch_quality("Medium Quality"), style="TButton").grid(row=0, column=1, padx=10)
        ttk.Button(self.controls_frame, text="High", command=lambda: self.video_player.switch_quality("High Quality"), style="TButton").grid(row=0, column=2, padx=10)

        ttk.Button(self.controls_frame, text="▶ Play", command=lambda: self.video_player.play(), style="TButton").grid(row=0, column=3, padx=10)
        ttk.Button(self.controls_frame, text="⏸ Pause", command=self.video_player.pause, style="TButton").grid(row=0, column=4, padx=10)
        ttk.Button(self.controls_frame, text="⏯ Resume", command=self.video_player.resume, style="TButton").grid(row=0, column=5, padx=10)

# ========================== Main ==========================

if __name__ == "__main__":
    root = ThemedTk(theme="breeze")
    app = VideoPlayerApp(root)
    root.mainloop()
