import tkinter as tk
import tkinter.font
from tkinter import ttk
import cv2
import PIL.Image, PIL.ImageTk
import moviepy
import os
import pyaudio
import wave

import youtube

# Instantiate PyAudio
PYAUDIO = pyaudio.PyAudio()

SHORTS_PATH = "videos/"

def extract_audio(video_path: str, audio_path: str):
    video_clip = moviepy.VideoFileClip(video_path)

    # Extract the audio from the video clip
    audio_clip = video_clip.audio

    if not os.path.exists(os.path.dirname(audio_path)):
        print(f"{audio_path} does not exist. Creating {audio_path}")
        os.mkdir(audio_path)

    # Write the audio to a separate file
    audio_clip.write_audiofile(audio_path)

    audio_clip.close()
    video_clip.close()


class App:
    def __init__(self, root, title):
        self.root = root
        self.root.configure(bg="#FFFFFF") # Main background is white
        self.root.title(title)

        self.shorts = []
        self.shortidx = 0
        self.load_videos()

        # Create a canvas for the short
        self.canvas = tk.Canvas(root, width=1, height=1)
        self.canvas.pack()

        self.video = None
        self.audio = None
        self.ratio = 0
        self.playing = False
        if self.shorts:
            self.disp_video(0)

        self.searchbox = tk.Text(self.root, height=1, width=40)
        self.searchbox.pack()
        self.searchbox.bind("<Return>", lambda e:self.on_download())

        self.downloadbtn = ttk.Button(self.root, text="DOWNLOAD", command=self.on_download)
        self.downloadbtn.pack()

        self.nextbtn = ttk.Button(self.root, text=">>>", command=lambda:self.disp_video(self.shortidx + 1))
        self.nextbtn.pack()

        self.playpausebtn = ttk.Button(self.root, text="PLAY/PAUSE", command=self.toggle_play_pause)
        self.playpausebtn.pack()

        # After it is called once, the update method will be automatically called every delay milliseconds
        # self.delay = int(1000/self.video.fps)
        self.delay = 1
        self.update()

        self.root.mainloop()

    def toggle_play_pause(self):
        self.playing = not self.playing

    def load_videos(self):
        if not os.path.exists(os.path.dirname(SHORTS_PATH)):
            return

        for file in os.listdir(SHORTS_PATH):
            path = os.path.join(SHORTS_PATH, file)
            print(f"Loading {path}")
            self.shorts.append(path)

    def on_download(self):
        search = self.searchbox.get(1.0, "end")
        self.searchbox.delete(1.0, "end") # Clear the search box

        if not self.shorts:
            self.shorts.append(youtube.download_videos(search, 15, SHORTS_PATH))
            self.disp_video(0)
        else:
            self.shorts.append(youtube.download_videos(search, 15, SHORTS_PATH))

    def disp_video(self, idx):
        video_path = self.shorts[self.shortidx]
        audio_path = f"cache/{os.path.splitext(os.path.basename(video_path))[0]}.wav"
        self.shortidx = idx
        try:
            extract_audio(video_path, audio_path)
        except:
            print(f"Could not load audio for video {video_path}")
            self.playing = False
            msg = f"Could not load video {video_path}"
            font = tk.font.Font(family="Georgia", size=17)
            width, height = font.measure(msg), font.metrics("linespace")
            self.canvas.delete("all")
            self.canvas.configure(width=width, height=height)
            self.canvas.create_text((width/2, height/2), text=msg, font=font)
            return
        self.video = VideoPlayer(video_path)
        self.audio = AudioPlayer(audio_path)
        self.canvas.configure(width=self.video.width, height=self.video.height)
        self.ratio = int(self.audio.fps/self.video.fps)
        self.playing = True

    def update(self):
        if self.playing:
            # Get a frame from the video source
            self.audio.play_frames(self.ratio)
            ret, frame = self.video.next_frame()

            if ret:
                self.photo = PIL.ImageTk.PhotoImage(image = PIL.Image.fromarray(frame))
                self.canvas.create_image(0, 0, image = self.photo, anchor = tk.NW)

        self.root.after(self.delay, self.update)


class AudioPlayer:
    def __init__(self, path):
        self.f = wave.open(path, "rb") 
        self.samplewidth = self.f.getsampwidth()
        self.channels = self.f.getnchannels()
        self.fps = self.f.getframerate()


        fmt = PYAUDIO.get_format_from_width(self.samplewidth)
        self.stream = PYAUDIO.open(format=fmt, channels=self.channels, rate=self.fps, output=True)  


    def play_frames(self, n: int):
        data = self.f.readframes(n)  
        if data:
            self.stream.write(data)  
          
          
    def __del__(self):
        # Close audio stream when destroyed
        self.stream.stop_stream()
        self.stream.close()


class VideoPlayer:
    def __init__(self, path):
        # Open the video source
        self.video = cv2.VideoCapture(path)
        if not self.video.isOpened():
            raise ValueError("Unable to open video source", path)

        # Get video source width and height
        self.width = self.video.get(cv2.CAP_PROP_FRAME_WIDTH)
        self.height = self.video.get(cv2.CAP_PROP_FRAME_HEIGHT)
        self.fps = self.video.get(cv2.CAP_PROP_FPS)

    def next_frame(self):
        """ Return the next frame of the video """

        if self.video.isOpened():
            ret, frame = self.video.read()
            if ret:
                # Return a boolean success flag and the current frame converted to BGR
                return (True, cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))

        return (ret, None)

    # Release the video source when the object is destroyed
    def __del__(self):
        if self.video.isOpened():
            self.video.release()


def main():
    root = tk.Tk()
    app = App(root, "video")

if __name__ == "__main__":
    main()

PYAUDIO.terminate()  
