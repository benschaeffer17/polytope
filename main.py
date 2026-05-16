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
from widgets.state import UIStateManager, UIStateVariable, UIAction
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

        self.state = UIStateManager()
        
        # Discrete configuration variables
        self.state.register(UIStateVariable("vertex_mode", ['partition', 'bfs', 'distance', 'hopf'], glfw.KEY_8, "8", "Toggle vertex coloring mode", on_change=self.load_shape))
        self.state.register(UIStateVariable("edge_mode", ['bfs', 'icosi', 'hopf', 'zome'], glfw.KEY_9, "9", "Toggle edge coloring mode", on_change=self.load_shape))
        self.state.register(UIStateVariable("points_mode", [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15], glfw.KEY_0, "0", "Toggle points mode (filtering geometry)", default_index=5, on_change=self.load_shape))
        self.state.register(UIStateVariable("slice_mode", ['at_least', 'exact', 'adjacent', 'echo'], glfw.KEY_S, "S", "Toggle slice mode (cutting planes)", on_change=self.load_shape))
        self.state.register(UIStateVariable("point_set", ['dfs', 'distance', 'hopf'], glfw.KEY_F, "F", "Toggle point set (DFS generation)", on_change=self.load_shape))
        self.state.register(UIStateVariable("blend", [i / 10.0 for i in range(1, 11)], glfw.KEY_Q, "Q", "Toggle face opacity (blend)", default_index=9, on_change=self.load_shape))
        self.state.register(UIStateVariable("d_value", [1.0, 1.2, 1.5, 2.0, 5.0, 10.0, 20.0, 50.0, 100.0], glfw.KEY_D, "D", "Toggle 4D perspective depth (d-value)", default_index=3))
        self.state.register(UIStateVariable("cell_contraction", [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0], glfw.KEY_G, "G", "Toggle 3D cell contraction (spacing out cells)", default_index=9, on_change=self.load_shape))
        self.state.register(UIStateVariable("draw_triangles", [False, True], glfw.KEY_B, "B", "Toggle drawing of 2D face triangles"))
        
        self.cell_chain = 0
        self.chain_grouping_mode = 0

        # Load initial shape based on default states
        self.load_shape()

        self.angle_4d = 0.0
        self.rotation_plane = 0 # Default to xy plane
        self.rotation_speed_level = 3
        self.base_rotation_speed = 0.001
        self.last_frame_time = 0.0
        self.default_camera_distance = 2.0
        self.camera_distance = self.default_camera_distance
        
        self.show_help = False

        # Continuous / Stateless Actions
        self.state.register(UIAction(glfw.KEY_V, "V", "Toggle render style (Wireframe/Cylinder)", lambda: self.model.style.toggle_style() if self.model else None))
        self.state.register(UIAction(glfw.KEY_T, "T", "Toggle shape (24-cell, 120-cell, 600-cell)", self.toggle_shape))
        self.state.register(UIAction(glfw.KEY_P, "P", "Toggle recording to WebP video", self.capture.toggle_recording))
        self.state.register(UIAction(glfw.KEY_1, "1", "Set 4D rotation plane to XY", lambda: self.set_rotation_plane(0)))
        self.state.register(UIAction(glfw.KEY_2, "2", "Set 4D rotation plane to XZ", lambda: self.set_rotation_plane(1)))
        self.state.register(UIAction(glfw.KEY_3, "3", "Set 4D rotation plane to XW", lambda: self.set_rotation_plane(2)))
        self.state.register(UIAction(glfw.KEY_4, "4", "Set 4D rotation plane to YZ", lambda: self.set_rotation_plane(3)))
        self.state.register(UIAction(glfw.KEY_5, "5", "Set 4D rotation plane to YW", lambda: self.set_rotation_plane(4)))
        self.state.register(UIAction(glfw.KEY_6, "6", "Set 4D rotation plane to ZW", lambda: self.set_rotation_plane(5)))
        self.state.register(UIAction(glfw.KEY_A, "A", "Increase rotation speed", self.increase_rotation_speed))
        self.state.register(UIAction(glfw.KEY_Z, "Z", "Decrease rotation speed", self.decrease_rotation_speed))
        self.state.register(UIAction(glfw.KEY_K, "K", "Zoom out", self.zoom_out))
        self.state.register(UIAction(glfw.KEY_M, "M", "Zoom in", self.zoom_in))
        self.state.register(UIAction(glfw.KEY_N, "N", "Cycle through isolated Boerdijk-Coxeter cell chains", self.toggle_cell_chain))
        self.state.register(UIAction(glfw.KEY_H, "H", "Toggle chain grouping", self.toggle_chain_grouping))
        self.state.register(UIAction(glfw.KEY_SLASH, "/", "Toggle this Help Screen", self.toggle_help))
        self.state.register(UIAction(glfw.KEY_ESCAPE, "ESC", "Quit", self.ui.close_window))

        # Proxy the UI manager to the GLFW keyboard callback
        def proxy_keyboard_callback(window, key, scancode, action, mods):
            if action == glfw.PRESS or action == glfw.REPEAT:
                self.state.handle_keypress(key)
        self.ui.register_any_key_callback(self.any_key_handler)
        # Override the existing keyboard callback
        self.ui.window_key_proxy = proxy_keyboard_callback
        glfw.set_key_callback(self.ui.window, self.ui._key_callback)
        # Hack to intercept it via ui
        self.ui.keyboard_callbacks.clear()
        self.ui.any_key_callback = lambda k: self.any_key_handler(k) or self.state.handle_keypress(k)
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
        blend = self.state.get_variable("blend").get_value()
        contraction = self.state.get_variable("cell_contraction").get_value()
        
        edge_coloring = self.state.get_variable("edge_mode").get_value()
        points_mode = self.state.get_variable("points_mode").get_value()
        vertex_coloring = self.state.get_variable("vertex_mode").get_value()
        slice_mode = self.state.get_variable("slice_mode").get_value()
        point_set = self.state.get_variable("point_set").get_value()

        if self.shape_name == '24-cell':
            self.model = Cell24Model(blend=blend, cell_contraction=contraction)
        elif self.shape_name == '120-cell':
            self.model = Cell120Model(is_vertex_centered=False, edge_coloring=edge_coloring,
                                      points_mode=points_mode, vertex_coloring=vertex_coloring,
                                      blend=blend, slice_mode=slice_mode, point_set=point_set,
                                      cell_contraction=contraction)
        elif self.shape_name == '600-cell':
            self.model = Cell600Model(is_vertex_centered=False, edge_coloring=edge_coloring,
                                      points_mode=points_mode, vertex_coloring=vertex_coloring,
                                      blend=blend, slice_mode=slice_mode, point_set=point_set,
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
            self.hud.draw(self.state.get_help_lines())
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

        projected_vertices = project_4d_to_3d(self.model.vertices_4d, rotation_matrix, d=self.state.get_variable("d_value").get_value())
        drawing.draw(projected_vertices, self.model.edges, self.model.colors, self.model.style, volume_dimension=self.camera_distance, fixed_vertices_indices=fixed_vertices_indices, edge_colors=self.model.edge_colors, edge_width_multipliers=self.model.edge_width_multipliers)

        # Draw the cell triangles if activated
        if self.state.get_variable("draw_triangles").get_value() and self.model.triangle_vertices_4d is not None and len(self.model.triangle_vertices_4d) > 0:
            projected_triangle_vertices = project_4d_to_3d(self.model.triangle_vertices_4d, rotation_matrix, d=self.state.get_variable("d_value").get_value())

            if self.cell_chain == 0:
                drawing.draw_triangles(projected_triangle_vertices, self.model.triangles, self.model.triangle_colors, normals=None)
            elif self.model.chain_groupings and self.model.chain_grouping_names:
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

        if self.model.chain_groupings and self.model.chain_grouping_names:
            group_name = self.model.chain_grouping_names[self.chain_grouping_mode]
            num_groups = len(self.model.chain_groupings[group_name])
            chain_status = f"{self.cell_chain}/{num_groups} ({group_name})" if self.cell_chain > 0 else f"ALL ({group_name})"
        else:
            chain_status = f"{self.cell_chain}/{self.model.num_chains}" if self.cell_chain > 0 else "ALL"

        v_mode = self.state.get_variable("vertex_mode").format_hud()
        e_mode = self.state.get_variable("edge_mode").format_hud()
        pset = self.state.get_variable("point_set").format_hud()
        pmode = self.state.get_variable("points_mode").format_hud()
        smode = self.state.get_variable("slice_mode").format_hud()
        blend = self.state.get_variable("blend").format_hud()
        d_val = self.state.get_variable("d_value").format_hud()
        tris = 'ON' if self.state.get_variable("draw_triangles").get_value() else 'OFF'
        c_cont = self.state.get_variable("cell_contraction").format_hud()

        hud_lines = [
            f"Shape: {self.shape_name:<8} | Dist: {self.camera_distance:5.2f} | Render: {render_mode:<9} | Rotation: {plane_name:<6} | Speed: {self.rotation_speed_level:2} | FPS: {self.ui.fps:>4} | Capture: {capture_status:<16}",
            f"Vertex: {v_mode:<9} | Edge: {e_mode:<5} | PtSet: {pset:<8} | Points: {pmode:2} | Slice: {smode:<8} | Blend: {blend:>4} | d: {d_val:>4}",
            f"Tris: {tris:<3} | CellCont: {c_cont:>4} | Chain: {chain_status:<6}"
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
