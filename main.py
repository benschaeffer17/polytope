
import glfw
from OpenGL.GL import *
import numpy as np
import sys
from OpenGL.GLUT import glutInit
import os
from PIL import Image

from viz.ui import UserInterface, HeadsUpDisplay
from navigation.navigator import Navigator
from navigation.rotator import Rotator
from polytopes import get_24_cell, project_4d_to_3d
from viz.style import Style, LineStyle
import viz.drawing as drawing

class App:
    def __init__(self):
        self.ui = UserInterface(title="24-Cell Visualizer")
        self.nav = Navigator(self.ui)
        self.hud = HeadsUpDisplay(self.ui.window)
        self.rotator = Rotator()
        self.ui.register_draw_function(self.draw)
        
        self.vertices_4d, self.edges = get_24_cell()
        self.angle_4d = 0.0
        
        self.style = Style()
        self.rotation_plane = 0 # Default to xy plane
        self.rotation_speed_level = 3
        self.base_rotation_speed = 0.001
        self.last_frame_time = 0.0
        self.recording = False
        self.frame_idx = 0
        self.movie_dir = "polymovie"


        self.ui.register_keyboard_callback(glfw.KEY_V, self.toggle_style)
        self.ui.register_keyboard_callback(glfw.KEY_P, self.toggle_recording)
        self.ui.register_keyboard_callback(glfw.KEY_1, lambda *args: self.set_rotation_plane(0))
        self.ui.register_keyboard_callback(glfw.KEY_2, lambda *args: self.set_rotation_plane(1))
        self.ui.register_keyboard_callback(glfw.KEY_3, lambda *args: self.set_rotation_plane(2))
        self.ui.register_keyboard_callback(glfw.KEY_4, lambda *args: self.set_rotation_plane(3))
        self.ui.register_keyboard_callback(glfw.KEY_5, lambda *args: self.set_rotation_plane(4))
        self.ui.register_keyboard_callback(glfw.KEY_6, lambda *args: self.set_rotation_plane(5))
        self.ui.register_keyboard_callback(glfw.KEY_A, self.increase_rotation_speed)
        self.ui.register_keyboard_callback(glfw.KEY_Z, self.decrease_rotation_speed)


        # Vertex and Edge coloring based on 24-cell geometry
        # The 24-cell vertices are the permutations of (±1, ±1, 0, 0).
        # We can partition the vertices into three groups based on their w-coordinate
        # in the initial projection, which corresponds to a cell-first projection of the 24-cell.
        # w = -1: Inner octahedron (6 vertices) - rendered smaller
        # w = 0:  Cuboctahedron (12 vertices)
        # w = 1:  Outer octahedron (6 vertices) - rendered larger

        v_inner_indices = {i for i, v in enumerate(self.vertices_4d) if v[3] == -1}
        v_middle_indices = {i for i, v in enumerate(self.vertices_4d) if v[3] == 0}
        v_outer_indices = {i for i, v in enumerate(self.vertices_4d) if v[3] == 1}

        # --- Set Vertex Colors ---
        # Assign colors based on the vertex groups.
        cyan = [0.0, 1.0, 1.0]
        orange = [1.0, 0.65, 0.0]
        pale_red = [1.0, 0.5, 0.5]
        self.colors = []
        for i in range(len(self.vertices_4d)):
            if i in v_inner_indices:
                self.colors.append(cyan)
            elif i in v_middle_indices:
                self.colors.append(orange)
            else: # outer
                self.colors.append(pale_red)
        self.colors = np.array(self.colors, dtype=np.float32)

        # --- Set Edge Colors and Widths ---
        # Edges are classified and colored based on the vertex groups they connect.
        # A width multiplier is also assigned to each edge type for visual clarity.
        self.edge_colors = []
        self.edge_width_multipliers = []
        
        # Color definitions for edges
        green = [0.0, 1.0, 0.0]  # Inner octahedron edges
        red = [1.0, 0.0, 0.0]    # Inner to middle edges
        blue = [0.0, 0.0, 1.0]   # Middle (cuboctahedron) edges
        yellow = [1.0, 1.0, 0.0] # Middle to outer edges
        purple = [1.0, 0.0, 1.0] # Outer octahedron edges

        # Width multipliers, in descending order: Red > Green > Blue > Yellow > Purple
        width_multipliers = {
            "red": 1.2,
            "green": 1.15,
            "blue": 1.1,
            "yellow": 1.05,
            "purple": 1.0
        }

        for i, j in self.edges:
            is_i_inner = i in v_inner_indices
            is_i_middle = i in v_middle_indices
            is_i_outer = i in v_outer_indices

            is_j_inner = j in v_inner_indices
            is_j_middle = j in v_middle_indices
            is_j_outer = j in v_outer_indices

            if is_i_inner and is_j_inner:
                self.edge_colors.append(green) # Central octahedron
                self.edge_width_multipliers.append(width_multipliers["green"])
            elif (is_i_inner and is_j_middle) or (is_i_middle and is_j_inner):
                self.edge_colors.append(red) # Connecting inner to middle
                self.edge_width_multipliers.append(width_multipliers["red"])
            elif is_i_middle and is_j_middle:
                self.edge_colors.append(blue) # Cuboctahedron
                self.edge_width_multipliers.append(width_multipliers["blue"])
            elif (is_i_middle and is_j_outer) or (is_i_outer and is_j_middle):
                self.edge_colors.append(yellow) # Connecting middle to outer
                self.edge_width_multipliers.append(width_multipliers["yellow"])
            elif is_i_outer and is_j_outer:
                self.edge_colors.append(purple) # Outer octahedron
                self.edge_width_multipliers.append(width_multipliers["purple"])
            else:
                # Should not happen with the current 24-cell geometry
                self.edge_colors.append([1.0, 1.0, 1.0])
                self.edge_width_multipliers.append(1.0)
        
        self.edge_colors = np.array(self.edge_colors, dtype=np.float32)
        self.edge_width_multipliers = np.array(self.edge_width_multipliers, dtype=np.float32)

    def set_rotation_plane(self, plane_index):
        self.rotation_plane = plane_index

    def increase_rotation_speed(self, *args):
        self.rotation_speed_level = min(10, self.rotation_speed_level + 1)

    def decrease_rotation_speed(self, *args):
        self.rotation_speed_level = max(0, self.rotation_speed_level - 1)

    def toggle_style(self, *args):
        self.style.toggle_style()
    
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
        width, height = glfw.get_framebuffer_size(self.ui.window)
        glReadBuffer(GL_BACK)
        pixels = glReadPixels(0, 0, width, height, GL_RGB, GL_UNSIGNED_BYTE)
        image = Image.frombytes("RGB", (width, height), pixels)
        image = image.transpose(Image.FLIP_TOP_BOTTOM)
        image.save(os.path.join(self.movie_dir, f"frame_{self.frame_idx:04d}.jpg"), "JPEG", quality=90)
        self.frame_idx += 1

    def draw(self):
        current_time = glfw.get_time()
        if self.last_frame_time == 0.0:
            delta_time = 0.0
        else:
            delta_time = current_time - self.last_frame_time
        
        if self.recording:
            delta_time = 1.0 / 60.0

        self.last_frame_time = current_time

        # Set projection matrix
        width, height = glfw.get_window_size(self.ui.window)
        height = height if height > 0 else 1
        aspect_ratio = width / height
        
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        if width >= height:
            glOrtho(-2 * aspect_ratio, 2 * aspect_ratio, -2, 2, -10, 10)
        else:
            glOrtho(-2, 2, -2 / aspect_ratio, 2 / aspect_ratio, -10, 10)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()

        # Setup lights in fixed space relative to the observer
        glLightfv(GL_LIGHT0, GL_POSITION, [0.0, 0.0, 7.0, 1.0])
        glLightfv(GL_LIGHT1, GL_POSITION, [5.0, 5.0, 0.0, 1.0])
        glLightfv(GL_LIGHT2, GL_POSITION, [-5.0, 5.0, 0.0, 1.0])

        glPushMatrix()
        
        # Apply 3D rotation from mouse
        self.nav.apply_rotation()

        # Get 4D rotation matrix
        rotation_matrix = self.rotator.get_rotation_matrix(self.rotation_plane, self.angle_4d)

        # Get fixed vertices
        plane_indices = self.rotator.planes[self.rotation_plane]
        fixed_vertices_indices = set()
        for i, v in enumerate(self.vertices_4d):
            if abs(v[plane_indices[0]]) < 1e-6 and abs(v[plane_indices[1]]) < 1e-6:
                fixed_vertices_indices.add(i)

        # Get projected 3D vertices
        projected_vertices = project_4d_to_3d(self.vertices_4d, rotation_matrix)
        
        # Draw the polytope
        drawing.draw(projected_vertices, self.edges, self.colors, self.style, fixed_vertices_indices=fixed_vertices_indices, edge_colors=self.edge_colors)
        
        glPopMatrix()

        # Slowly rotate in 4D
        if self.rotation_speed_level > 0:
            speed_factor = 1.5 ** (self.rotation_speed_level - 3)
            self.angle_4d += self.base_rotation_speed * speed_factor * delta_time * 100.0

        if self.recording:
            self.capture_frame()

        # Draw the heads-up display
        if self.style.line_style.style == LineStyle.LINE:
            render_mode = "Wireframe"
        else:
            render_mode = "Cylinders"
        
        plane_name = self.rotator.get_plane_name(self.rotation_plane)
        
        if self.recording:
            capture_status = f"recording ({self.frame_idx:04d})"
        else:
            capture_status = "stopped"

        self.hud.draw(f"Render: {render_mode} | Rotation: {plane_name} | Speed: {self.rotation_speed_level} | FPS: {self.ui.fps} | Capture: {capture_status}")

    def run(self):
        # Initial OpenGL setup
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_LIGHTING)
        glEnable(GL_LIGHT0)
        glEnable(GL_LIGHT1)
        glEnable(GL_LIGHT2)
        glEnable(GL_COLOR_MATERIAL)
        glColorMaterial(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE)
        
        self.ui.run(self)

if __name__ == '__main__':
    glutInit(sys.argv)
    app = App()
    app.run()
