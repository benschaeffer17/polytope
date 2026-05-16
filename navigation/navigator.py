"""Module representing core functionality."""

import numpy as np
from OpenGL.GL import *
import glfw

class Navigator:
    """Base representation class."""
    def __init__(self, ui):
        """Executes internal logic."""
        self.ui = ui
        self.rotation = np.array([1.0, 0.0, 0.0, 0.0], dtype=np.float32) # w, x, y, z
        self.last_mouse_pos = None
        self.mouse_pressed = False

        self.ui.register_mouse_button_callback(glfw.MOUSE_BUTTON_LEFT, self.mouse_button_callback)
        self.ui.register_cursor_pos_callback(self.cursor_pos_callback)

    def mouse_button_callback(self, window, button, action, mods):
        """Executes internal logic."""
        if button == glfw.MOUSE_BUTTON_LEFT:
            if action == glfw.PRESS:
                self.mouse_pressed = True
                self.last_mouse_pos = glfw.get_cursor_pos(window)
            elif action == glfw.RELEASE:
                self.mouse_pressed = False
                self.last_mouse_pos = None

    def cursor_pos_callback(self, window, xpos, ypos):
        """Executes internal logic."""
        if self.mouse_pressed and self.last_mouse_pos:
            width, height = glfw.get_window_size(window)

            def to_hemisphere(x, y):
                """Executes internal logic."""
                x_norm = (2.0 * x / width) - 1.0
                y_norm = 1.0 - (2.0 * y / height)

                len_sq = x_norm**2 + y_norm**2
                if len_sq > 1.0:
                    norm = np.sqrt(len_sq)
                    x_norm /= norm
                    y_norm /= norm
                    z_norm = 0
                else:
                    z_norm = np.sqrt(1.0 - len_sq)
                return np.array([x_norm, y_norm, z_norm])

            start_vec = to_hemisphere(self.last_mouse_pos[0], self.last_mouse_pos[1])
            end_vec = to_hemisphere(xpos, ypos)

            if np.allclose(start_vec, end_vec):
                return

            angle = np.arccos(np.dot(start_vec, end_vec))
            axis = np.cross(end_vec, start_vec)

            if np.linalg.norm(axis) > 1e-6:
                axis = axis / np.linalg.norm(axis)

                q_delta = np.array([np.cos(angle / 2.0), *(np.sin(angle / 2.0) * axis)])

                from quaternion import q_mult
                self.rotation = q_mult(self.rotation, q_delta)
                self.normalize_quaternion()

            self.last_mouse_pos = (xpos, ypos)

    def normalize_quaternion(self):
        """Executes internal logic."""
        norm = np.linalg.norm(self.rotation)
        if norm > 0:
            self.rotation /= norm

    def get_rotation_matrix(self):
        """Executes internal logic."""
        w, x, y, z = self.rotation

        # 4D rotation matrix (projection from 4D to 3D)
        # For now, let's stick to 3D rotation for simplicity
        # We'll add 4D rotation later.

        xx, yy, zz = x*x, y*y, z*z
        xy, xz, yz = x*y, x*z, y*z
        wx, wy, wz = w*x, w*y, w*z

        return np.array([
            [1-2*(yy+zz),   2*(xy-wz),   2*(xz+wy), 0],
            [  2*(xy+wz), 1-2*(xx+zz),   2*(yz-wx), 0],
            [  2*(xz-wy),   2*(yz+wx), 1-2*(xx+yy), 0],
            [          0,           0,           0, 1]
        ], dtype=np.float32)

    def apply_rotation(self):
        """Executes internal logic."""
        glMultMatrixf(self.get_rotation_matrix())

if __name__ == '__main__':
    import sys
    sys.path.append('..')
    from widgets.ui import UserInterface

    class App:
        """Base representation class."""
        def __init__(self):
            """Executes internal logic."""
            self.ui = UserInterface()
            self.nav = Navigator(self.ui)
            self.ui.register_draw_function(self.draw)

        def draw(self):
            """Executes internal logic."""
            glPushMatrix()
            self.nav.apply_rotation()

            # Draw a cube for testing
            glBegin(GL_QUADS)

            glColor3f(0.0,1.0,0.0)
            glVertex3f( 1.0, 1.0,-1.0)
            glVertex3f(-1.0, 1.0,-1.0)
            glVertex3f(-1.0, 1.0, 1.0)
            glVertex3f( 1.0, 1.0, 1.0)

            glColor3f(1.0,0.5,0.0)
            glVertex3f( 1.0,-1.0, 1.0)
            glVertex3f(-1.0,-1.0, 1.0)
            glVertex3f(-1.0,-1.0,-1.0)
            glVertex3f( 1.0,-1.0,-1.0)

            glColor3f(1.0,0.0,0.0)
            glVertex3f( 1.0, 1.0, 1.0)
            glVertex3f(-1.0, 1.0, 1.0)
            glVertex3f(-1.0,-1.0, 1.0)
            glVertex3f( 1.0,-1.0, 1.0)

            glColor3f(1.0,1.0,0.0)
            glVertex3f( 1.0,-1.0,-1.0)
            glVertex3f(-1.0,-1.0,-1.0)
            glVertex3f(-1.0, 1.0,-1.0)
            glVertex3f( 1.0, 1.0,-1.0)

            glColor3f(0.0,0.0,1.0)
            glVertex3f(-1.0, 1.0, 1.0)
            glVertex3f(-1.0, 1.0,-1.0)
            glVertex3f(-1.0,-1.0,-1.0)
            glVertex3f(-1.0,-1.0, 1.0)

            glColor3f(1.0,0.0,1.0)
            glVertex3f( 1.0, 1.0,-1.0)
            glVertex3f( 1.0, 1.0, 1.0)
            glVertex3f( 1.0,-1.0, 1.0)
            glVertex3f( 1.0,-1.0,-1.0)

            glEnd()

            glPopMatrix()

        def run(self):
            """Executes internal logic."""
            self.ui.run()

    # Running this directly requires running from the viz directory
    # This is just for testing purposes.
    # To run: python -m polytope.navigation.navigator
    # This is not ideal, we will create a main script later.
    # For now, let's assume we are in the viz directory
    # and run python navigator.py
    # to fix this, I'll move the if __name__ == '__main__': to a main.py later

    # Due to the import `from ui import UserInterface`, we need to be in the `polytope/viz` directory to run this.
    # I'll create a main.py in the root `polytope` directory later to handle this properly.
    pass

