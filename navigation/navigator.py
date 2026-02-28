
import numpy as np
from OpenGL.GL import *
import glfw

class Navigator:
    def __init__(self, ui):
        self.ui = ui
        self.rotation = np.array([1.0, 0.0, 0.0, 0.0], dtype=np.float32) # w, x, y, z
        self.last_mouse_pos = None
        self.mouse_pressed = False

        self.ui.register_mouse_button_callback(glfw.MOUSE_BUTTON_LEFT, self.mouse_button_callback)
        self.ui.register_cursor_pos_callback(self.cursor_pos_callback)

    def mouse_button_callback(self, window, button, action, mods):
        if button == glfw.MOUSE_BUTTON_LEFT:
            if action == glfw.PRESS:
                self.mouse_pressed = True
                self.last_mouse_pos = glfw.get_cursor_pos(window)
            elif action == glfw.RELEASE:
                self.mouse_pressed = False
                self.last_mouse_pos = None

    def cursor_pos_callback(self, window, xpos, ypos):
        if self.mouse_pressed and self.last_mouse_pos:
            width, height = glfw.get_window_size(window)
            
            def to_hemisphere(x, y):
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
            axis = np.cross(start_vec, end_vec)
            
            if np.linalg.norm(axis) > 1e-6:
                axis = axis / np.linalg.norm(axis)
                
                q_delta = np.array([np.cos(angle / 2.0), *(np.sin(angle / 2.0) * axis)])
                
                self.rotation = self.quaternion_multiply(q_delta, self.rotation)
                self.normalize_quaternion()

            self.last_mouse_pos = (xpos, ypos)

    def quaternion_multiply(self, q1, q2):
        w1, x1, y1, z1 = q1
        w2, x2, y2, z2 = q2
        w = w1 * w2 - x1 * x2 - y1 * y2 - z1 * z2
        x = w1 * x2 + x1 * w2 + y1 * z2 - z1 * y2
        y = w1 * y2 - x1 * z2 + y1 * w2 + z1 * x2
        z = w1 * z2 + x1 * y2 - y1 * x2 + z1 * w2
        return np.array([w, x, y, z])
        
    def normalize_quaternion(self):
        norm = np.linalg.norm(self.rotation)
        if norm > 0:
            self.rotation /= norm

    def get_rotation_matrix(self):
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
        glMultMatrixf(self.get_rotation_matrix())

if __name__ == '__main__':
    from ui import UserInterface

    class App:
        def __init__(self):
            self.ui = UserInterface()
            self.nav = Navigator(self.ui)
            self.ui.register_draw_function(self.draw)

        def draw(self):
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

