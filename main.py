"""Module representing core functionality."""

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
    """Base representation class."""
    ZOOM_FACTOR = 1.2
    MIN_ZOOM_FACTOR = 0.3
    MAX_ZOOM_FACTOR = 10.0

    def __init__(self, headless=False):
        """Executes internal logic."""
        self.headless = headless
        self.ui = UserInterface(title="Polytope Visualizer", headless=headless)
        self.nav = Navigator(self.ui)
        self.hud = HeadsUpDisplay(self.ui.window)
        self.hud.font = GLUT_STROKE_MONO_ROMAN
        self.hud.text_scale = 0.06
        self.rotator = Rotator()
        self.capture = Capture(self.ui.window)
        self.ui.register_draw_function(self.draw)

        self.shape_name = '600-cell'
        self.model = None

        self.vertex_modes = ['partition', 'bfs', 'distance', 'hopf']
        self.vertex_mode_index = 0

        self.edge_modes = ['bfs', 'icosi', 'hopf', 'zome']
        self.edge_mode_index = 0

        self.points_modes = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15]
        self.points_mode_index = 5

        self.slice_modes = ['at_least', 'exact', 'adjacent', 'echo']
        self.slice_mode_index = 0

        self.point_sets = ['dfs', 'distance', 'hopf']
        self.point_set_index = 0

        self.blend_values = [i / 10.0 for i in range(1, 11)]
        self.blend_index = 9

        self.d_values = [1.0, 1.2, 1.5, 2.0, 5.0, 10.0, 20.0, 50.0, 100.0]
        self.d_index = 3

        self.cell_contraction_values = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
        self.cell_contraction_index = 9
        self.draw_triangles = False
        self.cell_chain = 0
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
        self.ui.register_keyboard_callback(glfw.KEY_B, self.toggle_draw_triangles)
        self.ui.register_keyboard_callback(glfw.KEY_G, self.toggle_cell_contraction)
        self.ui.register_keyboard_callback(glfw.KEY_N, self.toggle_cell_chain)
        self.ui.register_keyboard_callback(glfw.KEY_H, self.toggle_chain_grouping)
        self.ui.register_keyboard_callback(glfw.KEY_SLASH, self.toggle_help)
        self.ui.register_any_key_callback(self.any_key_handler)

        self.show_help = False
        self.chain_grouping_mode = 0

    def toggle_help(self, *args):
        """Executes internal logic."""
        self.show_help = not self.show_help

    def any_key_handler(self, key):
        """Executes internal logic."""
        if self.show_help and key != glfw.KEY_SLASH:
            self.show_help = False
            return True
        return False

    def zoom_in(self, *args):
        """Executes internal logic."""
        new_dist = self.camera_distance / self.ZOOM_FACTOR
        min_dist = self.default_camera_distance * self.MIN_ZOOM_FACTOR
        self.camera_distance = max(new_dist, min_dist)

    def zoom_out(self, *args):
        """Executes internal logic."""
        new_dist = self.camera_distance * self.ZOOM_FACTOR
        max_dist = self.default_camera_distance * self.MAX_ZOOM_FACTOR
        self.camera_distance = min(new_dist, max_dist)

    def toggle_d_value(self, *args):
        """Executes internal logic."""
        self.d_index = (self.d_index + 1) % len(self.d_values)

    def toggle_vertex_mode(self, *args):
        """Executes internal logic."""
        self.vertex_mode_index = (self.vertex_mode_index + 1) % len(self.vertex_modes)
        self.load_shape()

    def toggle_edge_mode(self, *args):
        """Executes internal logic."""
        self.edge_mode_index = (self.edge_mode_index + 1) % len(self.edge_modes)
        self.load_shape()

    def toggle_points_mode(self, *args):
        """Executes internal logic."""
        self.points_mode_index = (self.points_mode_index + 1) % len(self.points_modes)
        self.load_shape()

    def toggle_slice_mode(self, *args):
        """Executes internal logic."""
        self.slice_mode_index = (self.slice_mode_index + 1) % len(self.slice_modes)
        self.load_shape()

    def toggle_point_set(self, *args):
        """Executes internal logic."""
        self.point_set_index = (self.point_set_index + 1) % len(self.point_sets)
        self.load_shape()

    def toggle_blend(self, *args):
        """Executes internal logic."""
        self.blend_index = (self.blend_index + 1) % len(self.blend_values)
        self.load_shape()

    def toggle_draw_triangles(self, *args):
        """Executes internal logic."""
        self.draw_triangles = not self.draw_triangles

    def toggle_cell_contraction(self, *args):
        """Executes internal logic."""
        self.cell_contraction_index = (self.cell_contraction_index + 1) % len(self.cell_contraction_values)
        self.load_shape()

    def toggle_chain_grouping(self, *args):
        """Executes internal logic."""
        if self.model and hasattr(self.model, 'chain_groupings'):
            group_name = self.model.chain_grouping_names[self.chain_grouping_mode]
            num_modes = len(self.model.chain_grouping_names)
            self.chain_grouping_mode = (self.chain_grouping_mode + 1) % num_modes
            self.cell_chain = 0 # reset selection

    def toggle_cell_chain(self, *args):
        """Executes internal logic."""
        if self.model and self.model.num_chains > 0 and hasattr(self.model, 'chain_groupings'):
            group_name = self.model.chain_grouping_names[self.chain_grouping_mode]
            num_groups = len(self.model.chain_groupings[group_name])
            self.cell_chain = (self.cell_chain + 1) % (num_groups + 1)

    def load_shape(self):
        """Executes internal logic."""
        current_style = self.model.style if self.model else None
        blend = self.blend_values[self.blend_index]
        contraction = self.cell_contraction_values[self.cell_contraction_index]
        if self.shape_name == '24-cell':
            self.model = Cell24Model(blend=blend, cell_contraction=contraction)
        elif self.shape_name == '120-cell':
            self.model = Cell120Model(is_vertex_centered=False, edge_coloring=self.edge_modes[self.edge_mode_index],
                                      points_mode=self.points_modes[self.points_mode_index], vertex_coloring=self.vertex_modes[self.vertex_mode_index],
                                      blend=blend, slice_mode=self.slice_modes[self.slice_mode_index], point_set=self.point_sets[self.point_set_index],
                                      cell_contraction=contraction)
        elif self.shape_name == '600-cell':
            self.model = Cell600Model(is_vertex_centered=False, edge_coloring=self.edge_modes[self.edge_mode_index],
                                      points_mode=self.points_modes[self.points_mode_index], vertex_coloring=self.vertex_modes[self.vertex_mode_index],
                                      blend=blend, slice_mode=self.slice_modes[self.slice_mode_index], point_set=self.point_sets[self.point_set_index],
                                      cell_contraction=contraction)
        if current_style:
            self.model.style = current_style

        # Ensure the active cell chain selection is still valid for the newly generated geometry
        if self.model and self.cell_chain > self.model.num_chains:
            self.cell_chain = 0

    def toggle_shape(self, *args):
        """Executes internal logic."""
        if self.shape_name == '24-cell':
            self.shape_name = '120-cell'
        elif self.shape_name == '120-cell':
            self.shape_name = '600-cell'
        else:
            self.shape_name = '24-cell'
        self.cell_chain = 0
        self.load_shape()

    def set_rotation_plane(self, plane_index):
        """Executes internal logic."""
        self.rotation_plane = plane_index

    def increase_rotation_speed(self, *args):
        """Executes internal logic."""
        self.rotation_speed_level = min(10, self.rotation_speed_level + 1)
    def decrease_rotation_speed(self, *args):
        """Executes internal logic."""
        self.rotation_speed_level = max(0, self.rotation_speed_level - 1)

    def draw(self):
        """Executes internal logic."""
        current_time = glfw.get_time()
        delta_time = (current_time - self.last_frame_time) if self.last_frame_time > 0 else 0.0
        if self.capture.recording:
            delta_time = 1.0 / 60.0
        self.last_frame_time = current_time

        width, height = glfw.get_window_size(self.ui.window)

        if self.show_help:
            help_lines = [
                "POLYTOPE VISUALIZER KEYBOARD CONTROLS",
                "",
                "V: Toggle render style (Wireframe/Cylinder)",
                "T: Toggle shape (24-cell, 120-cell, 600-cell)",
                "P: Toggle recording to WebP video",
                "1-6: Set 4D rotation plane (XY, XZ, XW, YZ, YW, ZW)",
                "A: Increase rotation speed",
                "Z: Decrease rotation speed",
                "D: Toggle 4D perspective depth (d-value)",
                "K: Zoom out",
                "M: Zoom in",
                "8: Toggle vertex coloring mode",
                "9: Toggle edge coloring mode",
                "0: Toggle points mode (filtering geometry)",
                "S: Toggle slice mode (cutting planes)",
                "F: Toggle point set (DFS generation)",
                "Q: Toggle face opacity (blend)",
                "B: Toggle drawing of 2D face triangles",
                "G: Toggle 3D cell contraction (spacing out cells)",
                "N: Cycle through isolated Boerdijk-Coxeter cell chains",
                "/: Toggle this Help Screen",
                "ESC: Quit"
            ]
            self.hud.draw(help_lines)
            return

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
        fixed_vertices_indices = set()
        if self.rotation_plane in (0, 1):
            plane_indices = self.rotator.modes[self.rotation_plane][0]
            fixed_vertices_indices = {i for i, v in enumerate(self.model.vertices_4d) if abs(v[plane_indices[0]]) < 1e-6 and abs(v[plane_indices[1]]) < 1e-6}

        projected_vertices = project_4d_to_3d(self.model.vertices_4d, rotation_matrix, d=self.d_values[self.d_index])
        drawing.draw(projected_vertices, self.model.edges, self.model.colors, self.model.style, volume_dimension=self.camera_distance, fixed_vertices_indices=fixed_vertices_indices, edge_colors=self.model.edge_colors, edge_width_multipliers=self.model.edge_width_multipliers)

        # Draw the cell triangles if activated
        if self.draw_triangles and self.model.triangle_vertices_4d is not None and len(self.model.triangle_vertices_4d) > 0:
            projected_triangle_vertices = project_4d_to_3d(self.model.triangle_vertices_4d, rotation_matrix, d=self.d_values[self.d_index])

            if self.cell_chain == 0:
                drawing.draw_triangles(projected_triangle_vertices, self.model.triangles, self.model.triangle_colors, normals=None)
            elif hasattr(self.model, 'chain_groupings'):
                group_name = self.model.chain_grouping_names[self.chain_grouping_mode]
                active_group = self.model.chain_groupings[group_name][self.cell_chain - 1]
                for chain_idx in active_group:
                    tris_to_draw, _, colors_to_draw = self.model.triangles_by_chain[chain_idx]
                    drawing.draw_triangles(projected_triangle_vertices, tris_to_draw, colors_to_draw, normals=None)
            else:
                tris_to_draw, _, colors_to_draw = self.model.triangles_by_chain[self.cell_chain - 1]
                drawing.draw_triangles(projected_triangle_vertices, tris_to_draw, colors_to_draw, normals=None)

        glPopMatrix()

        if self.rotation_speed_level > 0:
            self.angle_4d += self.base_rotation_speed * (1.5 ** (self.rotation_speed_level - 3)) * delta_time * 100.0

        if self.capture.recording:
            self.capture.capture_frame()

        render_mode = "Wireframe" if self.model.style.line_style.style == LineStyle.LINE else "Cylinders"
        plane_name = self.rotator.get_plane_name(self.rotation_plane)
        capture_status = f"recording ({self.capture.frame_idx:04d})" if self.capture.recording else "stopped"

        if hasattr(self.model, 'chain_groupings'):
            group_name = self.model.chain_grouping_names[self.chain_grouping_mode]
            num_groups = len(self.model.chain_groupings[group_name])
            chain_status = f"{self.cell_chain}/{num_groups} ({group_name})" if self.cell_chain > 0 else f"ALL ({group_name})"
        else:
            chain_status = f"{self.cell_chain}/{self.model.num_chains}" if self.cell_chain > 0 else "ALL"

        hud_lines = [
            f"Shape: {self.shape_name:<8} | Dist: {self.camera_distance:5.2f} | Render: {render_mode:<9} | Rotation: {plane_name:<6} | Speed: {self.rotation_speed_level:2} | FPS: {self.ui.fps:>4} | Capture: {capture_status:<16}",
            f"Vertex: {self.vertex_modes[self.vertex_mode_index]:<9} | Edge: {self.edge_modes[self.edge_mode_index]:<5} | PtSet: {self.point_sets[self.point_set_index]:<8} | Points: {self.points_modes[self.points_mode_index]:2} | Slice: {self.slice_modes[self.slice_mode_index]:<8} | Blend: {self.blend_values[self.blend_index]:3.1f} | d: {self.d_values[self.d_index]:5.1f}",
            f"Tris: {'ON' if self.draw_triangles else 'OFF':<3} | CellCont: {self.cell_contraction_values[self.cell_contraction_index]:3.1f} | Chain: {chain_status:<6}"
        ]
        self.hud.draw(hud_lines)

    def setup_gl(self):
        """Executes internal logic."""
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_LIGHTING)
        glEnable(GL_LIGHT0)
        glEnable(GL_LIGHT1)
        glEnable(GL_LIGHT2)
        glEnable(GL_COLOR_MATERIAL)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glColorMaterial(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE)
        glLightModeli(GL_LIGHT_MODEL_TWO_SIDE, GL_TRUE)

    def run(self):
        """Executes internal logic."""
        self.setup_gl()
        self.ui.run(self)

if __name__ == '__main__':
    glutInit(sys.argv)
    app = App()
    app.run()
