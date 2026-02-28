
import glfw
from OpenGL.GL import *

class UserInterface:
    def __init__(self, title="Polytope Visualizer", width=800, height=600):
        if not glfw.init():
            raise Exception("GLFW can't be initialized")

        self.window = glfw.create_window(width, height, title, None, None)

        if not self.window:
            glfw.terminate()
            raise Exception("GLFW window can't be created")

        glfw.make_context_current(self.window)

        self.keyboard_callbacks = {}
        self.mouse_button_callbacks = {}
        self.cursor_pos_callback = None
        self.draw_func = None

        glfw.set_key_callback(self.window, self._key_callback)
        glfw.set_mouse_button_callback(self.window, self._mouse_button_callback)
        glfw.set_cursor_pos_callback(self.window, self._cursor_pos_callback)

        # Default ESC key handler
        self.register_keyboard_callback(glfw.KEY_ESCAPE, self.close_window)

    def register_keyboard_callback(self, key, func):
        self.keyboard_callbacks[key] = func

    def register_mouse_button_callback(self, button, func):
        self.mouse_button_callbacks[button] = func
    
    def register_cursor_pos_callback(self, func):
        self.cursor_pos_callback = func

    def register_draw_function(self, func):
        self.draw_func = func

    def _key_callback(self, window, key, scancode, action, mods):
        if action == glfw.PRESS or action == glfw.REPEAT:
            if key in self.keyboard_callbacks:
                self.keyboard_callbacks[key](window, key, scancode, action, mods)

    def _mouse_button_callback(self, window, button, action, mods):
        if button in self.mouse_button_callbacks:
            self.mouse_button_callbacks[button](window, button, action, mods)

    def _cursor_pos_callback(self, window, xpos, ypos):
        if self.cursor_pos_callback:
            self.cursor_pos_callback(window, xpos, ypos)

    def close_window(self, *args):
        glfw.set_window_should_close(self.window, True)

    def run(self):
        while not glfw.window_should_close(self.window):
            glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
            
            if self.draw_func:
                self.draw_func()

            glfw.swap_buffers(self.window)
            glfw.poll_events()

        glfw.terminate()

if __name__ == '__main__':
    def draw():
        # A simple spinning triangle for testing
        glBegin(GL_TRIANGLES)
        glColor3f(1.0, 0.0, 0.0)
        glVertex3f(-0.5, -0.5, 0.0)
        glColor3f(0.0, 1.0, 0.0)
        glVertex3f(0.5, -0.5, 0.0)
        glColor3f(0.0, 0.0, 1.0)
        glVertex3f(0.0, 0.5, 0.0)
        glEnd()
        glRotatef(1, 0, 1, 0)

    ui = UserInterface()
    ui.register_draw_function(draw)
    ui.run()
