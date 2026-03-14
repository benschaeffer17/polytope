
import os
import glfw
from OpenGL.GL import *
from PIL import Image

class Capture:
    def __init__(self, window):
        self.window = window
        self.recording = False
        self.frame_idx = 0
        self.movie_dir = "polymovie"

    def toggle_recording(self, *args):
        self.recording = not self.recording
        if self.recording:
            self.frame_idx = 0
            if not os.path.exists(self.movie_dir):
                os.makedirs(self.movie_dir)
            else:
                for f in os.listdir(self.movie_dir):
                    os.remove(os.path.join(self.movie_dir, f))

    def capture_frame(self):
        width, height = glfw.get_framebuffer_size(self.window)
        glReadBuffer(GL_BACK)
        pixels = glReadPixels(0, 0, width, height, GL_RGB, GL_UNSIGNED_BYTE)
        image = Image.frombytes("RGB", (width, height), pixels)
        image = image.transpose(Image.FLIP_TOP_BOTTOM)
        image.save(os.path.join(self.movie_dir, f"frame_{self.frame_idx:04d}.jpg"), "JPEG", quality=90)
        self.frame_idx += 1
