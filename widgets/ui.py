
import glfw
from OpenGL.GL import *
from OpenGL.GLUT import *

class HeadsUpDisplay:
    def __init__(self, window):
        self.window = window
        self.font = GLUT_STROKE_MONO_ROMAN
        self.text_scale = 0.06

    def draw(self, nav_state):
        glDisable(GL_LIGHTING)
        glDisable(GL_DEPTH_TEST)
        glDepthMask(GL_FALSE)

        glMatrixMode(GL_PROJECTION)
        glPushMatrix()
        glLoadIdentity()
        width, height = glfw.get_window_size(self.window)
        glOrtho(0, width, 0, height, -1, 1)

        glMatrixMode(GL_MODELVIEW)
        glPushMatrix()
        glLoadIdentity()

        glColor3f(1.0, 1.0, 1.0)
        
        if isinstance(nav_state, str):
            lines = nav_state.split('\n')
        else:
            lines = nav_state

        font = getattr(self, 'font', GLUT_STROKE_MONO_ROMAN)
        
        dynamic_scale = min(width / 800.0, height / 600.0)

        if font in [GLUT_STROKE_ROMAN, GLUT_STROKE_MONO_ROMAN]:
            scale = getattr(self, 'text_scale', 0.06) * dynamic_scale
            glLineWidth(max(1.0, 1.5 * dynamic_scale))
            y_pos = height - (150 * scale)
            line_spacing = 150 * scale
            for line in lines:
                glPushMatrix()
                glTranslatef(10.0, y_pos, 0.0)
                glScalef(scale, scale, scale)
                for character in line:
                    glutStrokeCharacter(font, ord(character))
                glPopMatrix()
                y_pos -= line_spacing
        else:
            y_pos = height - 30
            line_spacing = 18 if font == GLUT_BITMAP_9_BY_15 else 28
            for line in lines:
                x_pos = 10.0
                for character in line:
                    glRasterPos2f(x_pos, y_pos)
                    glutBitmapCharacter(font, ord(character))
                    x_pos += glutBitmapWidth(font, ord(character))
                y_pos -= line_spacing

        glMatrixMode(GL_PROJECTION)
        glPopMatrix()
        glMatrixMode(GL_MODELVIEW)
        glPopMatrix()

        glDepthMask(GL_TRUE)
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_LIGHTING)


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
        self.frame_count = 0
        self.last_time = glfw.get_time()
        self.fps = 0

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

    def run(self, app=None):
        while not glfw.window_should_close(self.window):
            glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
            
            if self.draw_func:
                if app and app.capture.recording:
                    self.draw_func()
                else:
                    self.draw_func()

            self.frame_count += 1
            current_time = glfw.get_time()
            if current_time - self.last_time >= 1.0:
                self.fps = self.frame_count
                self.frame_count = 0
                self.last_time = current_time

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
