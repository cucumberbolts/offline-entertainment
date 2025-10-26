import tkinter as tk
from tkinter import ttk
import cv2
import PIL.Image, PIL.ImageTk
import moviepy
import os
import pyaudio
import wave

import youtube

# video_path = input("Enter a video path: ")
video_path = "/home/julian/Downloads/sun.mp4"

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

# Instantiate PyAudio
PYAUDIO = pyaudio.PyAudio()

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
          
          
    def __del__():
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

class App(tk.Tk):
    def __init__(self, *args, **kwargs):
        tk.Tk.__init__(self, *args, **kwargs)

        # the container is where we'll stack a bunch of frames
        # on top of each other, then the one we want visible
        # will be raised above the others
        container = tk.Frame(self)
        container.pack(side="top", fill="both", expand=True)
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

        self.frames = {}
        for F in (StartPage, ScrollPage):
            page_name = F.__name__
            frame = F(parent=container, controller=self)
            self.frames[page_name] = frame

            # put all of the pages in the same location;
            # the one on the top of the stacking order
            # will be the one that is visible.
            frame.grid(row=0, column=0, sticky="nsew")

        self.show_frame("ScrollPage")

    def show_frame(self, name):
        frame = self.frames[name]
        frame.tkraise()


class StartPage(tk.Frame):
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        self.controller = controller
        label = tk.Label(self, text="This is the start page")
        label.pack(side="top", fill="x", pady=10)

        audio_path = f"cache/{os.path.splitext(os.path.basename(video_path))[0]}.wav"
        extract_audio(video_path, audio_path)
        self.video = VideoPlayer(video_path)
        self.audio = AudioPlayer(audio_path)

        self.ratio = int(self.audio.fps/self.video.fps)

        self.playing = True

        # Create a canvas that can fit the above video source size
        self.canvas = tk.Canvas(root, width=self.video.width, height=self.video.height)
        self.canvas.pack()

        self.searchbox = tk.Text(root, height=1, width=40)
        self.searchbox.pack()
        self.searchbox.bind("<Return>", lambda e:self.on_download())

        self.downloadbtn = ttk.Button(root, text="DOWNLOAD", command=self.on_download)
        self.downloadbtn.pack()

        self.nextbtn = ttk.Button(root, text=">>>", command=self.toggle_play_pause)
        self.nextbtn.pack()

        self.playpausebtn = ttk.Button(root, text="PLAY/PAUSE", command=self.toggle_play_pause)
        self.playpausebtn.pack()

        # After it is called once, the update method will be automatically called every delay milliseconds
        # self.delay = int(1000/self.video.fps)
        self.delay = 1
        self.update()

    def toggle_play_pause(self):
        self.playing = not self.playing

    def on_download(self):
        self.searchbox.delete(1.0, "end") # Clear the search box

    def next_video(self):
        pass

    def update(self):
        if self.playing:
            # Get a frame from the video source
            self.audio.play_frames(self.ratio)
            ret, frame = self.video.next_frame()

            if ret:
                self.photo = PIL.ImageTk.PhotoImage(image = PIL.Image.fromarray(frame))
                self.canvas.create_image(0, 0, image = self.photo, anchor = tk.NW)

        self.root.after(self.delay, self.update)


class ScrollPage(tk.Frame):
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        self.controller = controller
        label = tk.Label(self, text="This is page 1")
        label.pack(side="top", fill="x", pady=10)
        button = tk.Button(self, text="Go to the start page",
                           command=lambda: controller.show_frame("StartPage"))
        button.pack()


if __name__ == "__main__":
    app = App()
    app.mainloop()
