import tkinter as tk
import cv2
import PIL.Image, PIL.ImageTk
import moviepy
import os
import pyaudio
import wave

video_path = input("Enter a video path: ")

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

        audio_path = f"cache/{os.path.splitext(os.path.basename(video_path))[0]}.wav"
        extract_audio(video_path, audio_path)
        self.video = VideoPlayer(video_path)
        self.audio = AudioPlayer(audio_path)

        # Create a canvas that can fit the above video source size
        self.canvas = tk.Canvas(root, width = self.video.width, height = self.video.height)
        self.canvas.pack()

        self.ratio = int(self.audio.fps/self.video.fps)

        # After it is called once, the update method will be automatically called every delay milliseconds
        # self.delay = int(1000/self.video.fps)
        self.delay = 1
        self.update()


        self.root.mainloop()

    def update(self):
        # Get a frame from the video source
        self.audio.play_frames(self.ratio)
        ret, frame = self.video.next_frame()

        if ret:
            self.photo = PIL.ImageTk.PhotoImage(image = PIL.Image.fromarray(frame))
            self.canvas.create_image(0, 0, image = self.photo, anchor = tk.NW)

        self.root.after(self.delay, self.update)


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


def main():
    root = tk.Tk()
    app = App(root, "video")
    root.resizable(False, False) # Prevent resizing

if __name__ == "__main__":
    main()

PYAUDIO.terminate()  
