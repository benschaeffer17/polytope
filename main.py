
import glfw
from OpenGL.GL import *
import numpy as np
import sys
from OpenGL.GLUT import glutInit, GLUT_STROKE_MONO_ROMAN
import os
from PIL import Image

from widgets.ui import UserInterface, HeadsUpDisplay
from widgets.capture import Capture
from navigation.navigator import Navigator
from navigation.rotator import Rotator
from polytopes import project_4d_to_3d
from viz.style import LineStyle
import viz.drawing as drawing
from models import (
    Cell24Model,
    Cell120Model,
    Cell600Model
)

class App:
    ZOOM_FACTOR = 1.2
    MIN_ZOOM_FACTOR = 0.3
    MAX_ZOOM_FACTOR = 10.0

    def __init__(self):
        self.ui = UserInterface(title="Polytope Visualizer")
        self.nav = Navigator(self.ui)
        self.hud = HeadsUpDisplay(self.ui.window)
        self.hud.font = GLUT_STROKE_MONO_ROMAN
        self.hud.text_scale = 0.06
        self.rotator = Rotator()
        self.capture = Capture(self.ui.window)
        self.ui.register_draw_function(self.draw)
        
        self.shape_name = '600-cell'
        self.model = None

        self.vertex_modes = ['partition', 'bfs', 'distance']
        self.vertex_mode_index = 0

        self.edge_modes = ['bfs', 'icosi', 'hopf', 'zome']
        self.edge_mode_index = 0

        self.points_modes = [1, 2, 3, 4, 5, 6, 7, 8, 9]
        self.points_mode_index = 5

        self.slice_modes = ['at_least', 'exact', 'adjacent', 'echo']
        self.slice_mode_index = 0

        self.point_sets = ['dfs', 'distance']
        self.point_set_index = 0

        self.blend_values = [i / 10.0 for i in range(1, 11)]
        self.blend_index = 9

        self.d_values = [1.0, 1.2, 1.5, 2.0, 5.0, 10.0, 20.0, 50.0, 100.0]
        self.d_index = 3

        self.load_shape()
        
        self.angle_4d = 0.0
        self.rotation_plane = 0 # Default to xy plane
        self.rotation_speed_level = 3
        self.base_rotation_speed = 0.001
        self.last_frame_time = 0.0


        self.default_camera_distance = 2.0
        self.camera_distance = self.default_camera_distance

        self.ui.register_keyboard_callback(glfw.KEY_V, lambda *args: self.model.style.toggle_style())
        self.ui.register_keyboard_callback(glfw.KEY_T, self.toggle_shape)
        self.ui.register_keyboard_callback(glfw.KEY_P, self.capture.toggle_recording)
        self.ui.register_keyboard_callback(glfw.KEY_1, lambda *args: self.set_rotation_plane(0))
        self.ui.register_keyboard_callback(glfw.KEY_2, lambda *args: self.set_rotation_plane(1))
        self.ui.register_keyboard_callback(glfw.KEY_3, lambda *args: self.set_rotation_plane(2))
        self.ui.register_keyboard_callback(glfw.KEY_4, lambda *args: self.set_rotation_plane(3))
        self.ui.register_keyboard_callback(glfw.KEY_5, lambda *args: self.set_rotation_plane(4))
        self.ui.register_keyboard_callback(glfw.KEY_6, lambda *args: self.set_rotation_plane(5))
        self.ui.register_keyboard_callback(glfw.KEY_A, self.increase_rotation_speed)
        self.ui.register_keyboard_callback(glfw.KEY_D, self.toggle_d_value)

        self.ui.register_keyboard_callback(glfw.KEY_Z, self.decrease_rotation_speed)
        self.ui.register_keyboard_callback(glfw.KEY_K, self.zoom_out)
        self.ui.register_keyboard_callback(glfw.KEY_M, self.zoom_in)
        self.ui.register_keyboard_callback(glfw.KEY_8, self.toggle_vertex_mode)
        self.ui.register_keyboard_callback(glfw.KEY_9, self.toggle_edge_mode)
        self.ui.register_keyboard_callback(glfw.KEY_0, self.toggle_points_mode)
        self.ui.register_keyboard_callback(glfw.KEY_S, self.toggle_slice_mode)
        self.ui.register_keyboard_callback(glfw.KEY_F, self.toggle_point_set)
        self.ui.register_keyboard_callback(glfw.KEY_Q, self.toggle_blend)

    def zoom_in(self, *args):
        new_dist = self.camera_distance / self.ZOOM_FACTOR
        min_dist = self.default_camera_distance * self.MIN_ZOOM_FACTOR
        self.camera_distance = max(new_dist, min_dist)

    def zoom_out(self, *args):
        new_dist = self.camera_distance * self.ZOOM_FACTOR
        max_dist = self.default_camera_distance * self.MAX_ZOOM_FACTOR
        self.camera_distance = min(new_dist, max_dist)

    def toggle_d_value(self, *args):
        self.d_index = (self.d_index + 1) % len(self.d_values)

    def toggle_vertex_mode(self, *args):
        self.vertex_mode_index = (self.vertex_mode_index + 1) % len(self.vertex_modes)
        self.load_shape()

    def toggle_edge_mode(self, *args):
        self.edge_mode_index = (self.edge_mode_index + 1) % len(self.edge_modes)
        self.load_shape()

    def toggle_points_mode(self, *args):
        self.points_mode_index = (self.points_mode_index + 1) % len(self.points_modes)
        self.load_shape()

    def toggle_slice_mode(self, *args):
        self.slice_mode_index = (self.slice_mode_index + 1) % len(self.slice_modes)
        self.load_shape()

    def toggle_point_set(self, *args):
        self.point_set_index = (self.point_set_index + 1) % len(self.point_sets)
        self.load_shape()

    def toggle_blend(self, *args):
        self.blend_index = (self.blend_index + 1) % len(self.blend_values)
        self.load_shape()

    def load_shape(self):
        current_style = self.model.style if self.model else None
        blend = self.blend_values[self.blend_index]
        if self.shape_name == '24-cell':
            self.model = Cell24Model(blend=blend)
        elif self.shape_name == '120-cell':
            self.model = Cell120Model(blend=blend)
        elif self.shape_name == '600-cell':
            self.model = Cell600Model(is_vertex_centered=False, edge_coloring=self.edge_modes[self.edge_mode_index],
                                      points_mode=self.points_modes[self.points_mode_index], vertex_coloring=self.vertex_modes[self.vertex_mode_index],
                                      blend=blend, slice_mode=self.slice_modes[self.slice_mode_index], point_set=self.point_sets[self.point_set_index])
        if current_style:
            self.model.style = current_style

    def toggle_shape(self, *args):
        if self.shape_name == '24-cell':
            self.shape_name = '120-cell'
        elif self.shape_name == '120-cell':
            self.shape_name = '600-cell'
        else:
            self.shape_name = '24-cell'
        self.load_shape()

    def set_rotation_plane(self, plane_index):
        self.rotation_plane = plane_index

    def increase_rotation_speed(self, *args):
        self.rotation_speed_level = min(10, self.rotation_speed_level + 1)
    def decrease_rotation_speed(self, *args):
        self.rotation_speed_level = max(0, self.rotation_speed_level - 1)

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
        fixed_vertices_indices = {i for i, v in enumerate(self.model.vertices_4d) if abs(v[plane_indices[0]]) < 1e-6 and abs(v[plane_indices[1]]) < 1e-6}

        projected_vertices = project_4d_to_3d(self.model.vertices_4d, rotation_matrix, d=self.d_values[self.d_index])
        drawing.draw(projected_vertices, self.model.edges, self.model.colors, self.model.style, volume_dimension=self.camera_distance, fixed_vertices_indices=fixed_vertices_indices, edge_colors=self.model.edge_colors, edge_width_multipliers=self.model.edge_width_multipliers)
        
        glPopMatrix()

        if self.rotation_speed_level > 0:
            self.angle_4d += self.base_rotation_speed * (1.5 ** (self.rotation_speed_level - 3)) * delta_time * 100.0

        if self.capture.recording:
            self.capture.capture_frame()

        render_mode = "Wireframe" if self.model.style.line_style.style == LineStyle.LINE else "Cylinders"
        plane_name = self.rotator.get_plane_name(self.rotation_plane)
        capture_status = f"recording ({self.capture.frame_idx:04d})" if self.capture.recording else "stopped"
        
        hud_lines = [
            f"Shape: {self.shape_name:<8} | Dist: {self.camera_distance:5.2f} | Render: {render_mode:<9} | Rotation: {plane_name:<2} | Speed: {self.rotation_speed_level:2} | FPS: {self.ui.fps:>4} | Capture: {capture_status:<16}",
            f"Vertex: {self.vertex_modes[self.vertex_mode_index]:<9} | Edge: {self.edge_modes[self.edge_mode_index]:<5} | PtSet: {self.point_sets[self.point_set_index]:<8} | Points: {self.points_modes[self.points_mode_index]:2} | Slice: {self.slice_modes[self.slice_mode_index]:<8} | Blend: {self.blend_values[self.blend_index]:3.1f} | d: {self.d_values[self.d_index]:5.1f}"
        ]
        self.hud.draw(hud_lines)

    def run(self):
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_LIGHTING)
        glEnable(GL_LIGHT0)
        glEnable(GL_LIGHT1)
        glEnable(GL_LIGHT2)
        glEnable(GL_COLOR_MATERIAL)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glColorMaterial(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE)
        self.ui.run(self)

if __name__ == '__main__':
    glutInit(sys.argv)
    app = App()
    app.run()
