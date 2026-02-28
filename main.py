
import glfw
from OpenGL.GL import *
import numpy as np

from viz.ui import UserInterface
from navigation.navigator import Navigator
from polytopes import get_24_cell, project_4d_to_3d
from viz.style import Style
import viz.drawing as drawing

class App:
    def __init__(self):
        self.ui = UserInterface(title="24-Cell Visualizer")
        self.nav = Navigator(self.ui)
        self.ui.register_draw_function(self.draw)
        
        self.vertices_4d, self.edges = get_24_cell()
        self.angle_4d = 0.0
        
        self.style = Style()
        self.ui.register_keyboard_callback(glfw.KEY_V, self.toggle_style)

        # Generate colors based on 4D coordinates
        self.colors = np.abs(self.vertices_4d[:, :3])

    def toggle_style(self, *args):
        self.style.toggle_style()

    def draw(self):
        glPushMatrix()
        
        # Apply 3D rotation from mouse
        self.nav.apply_rotation()
        
        # Get projected 3D vertices
        projected_vertices = project_4d_to_3d(self.vertices_4d, self.angle_4d)
        
        # Draw the polytope
        drawing.draw(projected_vertices, self.edges, self.colors, self.style)
        
        glPopMatrix()
        
        # Slowly rotate in 4D
        self.angle_4d += 0.001

    def run(self):
        # Initial OpenGL setup
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_LIGHTING)
        glEnable(GL_LIGHT0)
        glEnable(GL_COLOR_MATERIAL)
        glColorMaterial(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE)
        
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        glOrtho(-2, 2, -2, 2, -10, 10)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        
        self.ui.run()

if __name__ == '__main__':
    app = App()
    app.run()
