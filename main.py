
import glfw
from OpenGL.GL import *
import numpy as np
import sys
from OpenGL.GLUT import glutInit
import os
from PIL import Image

from widgets.ui import UserInterface, HeadsUpDisplay
from widgets.capture import Capture
from navigation.navigator import Navigator
from navigation.rotator import Rotator
from polytopes import get_24_cell, get_120_cell, get_600_cell, project_4d_to_3d
from viz.style import Style, LineStyle
import viz.drawing as drawing

class App:
    ZOOM_FACTOR = 1.2
    MIN_ZOOM_FACTOR = 0.3
    MAX_ZOOM_FACTOR = 10.0

    def __init__(self):
        self.ui = UserInterface(title="Polytope Visualizer")
        self.nav = Navigator(self.ui)
        self.hud = HeadsUpDisplay(self.ui.window)
        self.rotator = Rotator()
        self.capture = Capture(self.ui.window)
        self.ui.register_draw_function(self.draw)
        
        self.shape_name = '24-cell'
        self.load_shape()
        
        self.angle_4d = 0.0
        
        self.style = Style()
        self.rotation_plane = 0 # Default to xy plane
        self.rotation_speed_level = 3
        self.base_rotation_speed = 0.001
        self.last_frame_time = 0.0

        self.default_camera_distance = 2.0
        self.camera_distance = self.default_camera_distance

        self.ui.register_keyboard_callback(glfw.KEY_V, self.toggle_style)
        self.ui.register_keyboard_callback(glfw.KEY_T, self.toggle_shape)
        self.ui.register_keyboard_callback(glfw.KEY_P, self.capture.toggle_recording)
        self.ui.register_keyboard_callback(glfw.KEY_1, lambda *args: self.set_rotation_plane(0))
        self.ui.register_keyboard_callback(glfw.KEY_2, lambda *args: self.set_rotation_plane(1))
        self.ui.register_keyboard_callback(glfw.KEY_3, lambda *args: self.set_rotation_plane(2))
        self.ui.register_keyboard_callback(glfw.KEY_4, lambda *args: self.set_rotation_plane(3))
        self.ui.register_keyboard_callback(glfw.KEY_5, lambda *args: self.set_rotation_plane(4))
        self.ui.register_keyboard_callback(glfw.KEY_6, lambda *args: self.set_rotation_plane(5))
        self.ui.register_keyboard_callback(glfw.KEY_A, self.increase_rotation_speed)
        self.ui.register_keyboard_callback(glfw.KEY_Z, self.decrease_rotation_speed)
        self.ui.register_keyboard_callback(glfw.KEY_K, self.zoom_out)
        self.ui.register_keyboard_callback(glfw.KEY_M, self.zoom_in)

    def zoom_in(self, *args):
        new_dist = self.camera_distance / self.ZOOM_FACTOR
        min_dist = self.default_camera_distance * self.MIN_ZOOM_FACTOR
        self.camera_distance = max(new_dist, min_dist)

    def zoom_out(self, *args):
        new_dist = self.camera_distance * self.ZOOM_FACTOR
        max_dist = self.default_camera_distance * self.MAX_ZOOM_FACTOR
        self.camera_distance = min(new_dist, max_dist)

    def load_shape(self):
        if self.shape_name == '24-cell':
            self.vertices_4d, self.edges = get_24_cell()
        elif self.shape_name == '120-cell':
            self.vertices_4d, self.edges = get_120_cell()
        elif self.shape_name == '600-cell':
            self.vertices_4d, self.edges = get_600_cell()
        self.setup_coloring()

    def toggle_shape(self, *args):
        if self.shape_name == '24-cell':
            self.shape_name = '120-cell'
        elif self.shape_name == '120-cell':
            self.shape_name = '600-cell'
        else:
            self.shape_name = '24-cell'
        self.load_shape()

    def setup_coloring(self):
        if self.shape_name == '24-cell':
            # Vertex and Edge coloring based on 24-cell geometry
            v_inner_indices = {i for i, v in enumerate(self.vertices_4d) if v[3] == -1}
            v_middle_indices = {i for i, v in enumerate(self.vertices_4d) if v[3] == 0}
            v_outer_indices = {i for i, v in enumerate(self.vertices_4d) if v[3] == 1}

            # --- Set Vertex Colors ---
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
            self.edge_colors = []
            self.edge_width_multipliers = []
            
            green = [0.0, 1.0, 0.0]
            red = [1.0, 0.0, 0.0]
            blue = [0.0, 0.0, 1.0]
            yellow = [1.0, 1.0, 0.0]
            purple = [1.0, 0.0, 1.0]

            width_multipliers = {
                "red": 1.2, "green": 1.15, "blue": 1.1,
                "yellow": 1.05, "purple": 1.0
            }

            for i, j in self.edges:
                is_i_inner = i in v_inner_indices
                is_i_middle = i in v_middle_indices
                is_i_outer = i in v_outer_indices
                is_j_inner = j in v_inner_indices
                is_j_middle = j in v_middle_indices
                is_j_outer = j in v_outer_indices

                if is_i_inner and is_j_inner:
                    self.edge_colors.append(green)
                    self.edge_width_multipliers.append(width_multipliers["green"])
                elif (is_i_inner and is_j_middle) or (is_i_middle and is_j_inner):
                    self.edge_colors.append(red)
                    self.edge_width_multipliers.append(width_multipliers["red"])
                elif is_i_middle and is_j_middle:
                    self.edge_colors.append(blue)
                    self.edge_width_multipliers.append(width_multipliers["blue"])
                elif (is_i_middle and is_j_outer) or (is_i_outer and is_j_middle):
                    self.edge_colors.append(yellow)
                    self.edge_width_multipliers.append(width_multipliers["yellow"])
                elif is_i_outer and is_j_outer:
                    self.edge_colors.append(purple)
                    self.edge_width_multipliers.append(width_multipliers["purple"])
                else:
                    self.edge_colors.append([1.0, 1.0, 1.0])
                    self.edge_width_multipliers.append(1.0)
            
            self.edge_colors = np.array(self.edge_colors, dtype=np.float32)
            self.edge_width_multipliers = np.array(self.edge_width_multipliers, dtype=np.float32)
        elif self.shape_name == '600-cell':
            red = [1.0, 0.0, 0.0]
            blue = [0.0, 0.0, 1.0]
            green = [0.0, 1.0, 0.0]
            self.colors = []
            for v in self.vertices_4d:
                if np.sum(np.abs(v)) == 1.0: # 8 vertices
                    self.colors.append(red)
                elif np.all(np.abs(v) == 0.5): # 16 vertices
                    self.colors.append(blue)
                else: # 96 vertices
                    self.colors.append(green)
            self.colors = np.array(self.colors, dtype=np.float32)
            self.edge_colors = np.array([[1.0, 1.0, 1.0]] * len(self.edges), dtype=np.float32)
            self.edge_width_multipliers = np.array([1.0] * len(self.edges), dtype=np.float32)
        else: # 120-cell
            self.colors = np.array([[1.0, 1.0, 1.0]] * len(self.vertices_4d), dtype=np.float32)
            self.edge_colors = np.array([[1.0, 1.0, 1.0]] * len(self.edges), dtype=np.float32)
            self.edge_width_multipliers = np.array([1.0] * len(self.edges), dtype=np.float32)
    
    def set_rotation_plane(self, plane_index):
        self.rotation_plane = plane_index

    def increase_rotation_speed(self, *args):
        self.rotation_speed_level = min(10, self.rotation_speed_level + 1)
    def decrease_rotation_speed(self, *args):
        self.rotation_speed_level = max(0, self.rotation_speed_level - 1)

    def toggle_style(self, *args):
        self.style.toggle_style()
    
    def draw(self):
        current_time = glfw.get_time()
        delta_time = (current_time - self.last_frame_time) if self.last_frame_time > 0 else 0.0
        if self.capture.recording:
            delta_time = 1.0 / 60.0
        self.last_frame_time = current_time

        width, height = glfw.get_window_size(self.ui.window)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        aspect_ratio = width / (height if height > 0 else 1)
        
        d = self.camera_distance
        if width >= height:
            glOrtho(-d * aspect_ratio, d * aspect_ratio, -d, d, -10, 10)
        else:
            glOrtho(-d, d, -d / aspect_ratio, d / aspect_ratio, -10, 10)
        
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()

        glLightfv(GL_LIGHT0, GL_POSITION, [0.0, 0.0, 7.0, 1.0])
        glLightfv(GL_LIGHT1, GL_POSITION, [5.0, 5.0, 0.0, 1.0])
        glLightfv(GL_LIGHT2, GL_POSITION, [-5.0, 5.0, 0.0, 1.0])

        glPushMatrix()
        self.nav.apply_rotation()

        rotation_matrix = self.rotator.get_rotation_matrix(self.rotation_plane, self.angle_4d)
        plane_indices = self.rotator.planes[self.rotation_plane]
        fixed_vertices_indices = {i for i, v in enumerate(self.vertices_4d) if abs(v[plane_indices[0]]) < 1e-6 and abs(v[plane_indices[1]]) < 1e-6}

        projected_vertices = project_4d_to_3d(self.vertices_4d, rotation_matrix)
        drawing.draw(projected_vertices, self.edges, self.colors, self.style, fixed_vertices_indices=fixed_vertices_indices, edge_colors=self.edge_colors)
        
        glPopMatrix()

        if self.rotation_speed_level > 0:
            self.angle_4d += self.base_rotation_speed * (1.5 ** (self.rotation_speed_level - 3)) * delta_time * 100.0

        if self.capture.recording:
            self.capture.capture_frame()

        render_mode = "Wireframe" if self.style.line_style.style == LineStyle.LINE else "Cylinders"
        plane_name = self.rotator.get_plane_name(self.rotation_plane)
        capture_status = f"recording ({self.capture.frame_idx:04d})" if self.capture.recording else "stopped"
        self.hud.draw(f"Shape: {self.shape_name} | Dist: {self.camera_distance:.2f} | Render: {render_mode} | Rotation: {plane_name} | Speed: {self.rotation_speed_level} | FPS: {self.ui.fps} | Capture: {capture_status}")

    def run(self):
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
