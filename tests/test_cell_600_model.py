
import unittest
import numpy as np

# Add the project root to the Python path
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from models.cell_600_model import get_600_cell, Cell600Model

class Test600Cell(unittest.TestCase):
    def test_vertex_count(self):
        """
        Tests that the 600-cell has 120 vertices.
        """
        vertices, _ = get_600_cell()
        self.assertEqual(len(vertices), 120)

    def test_points_mode_1(self):
        model = Cell600Model(points_mode=1)
        self.assertEqual(len(model.vertices_4d), 1)

    def test_points_mode_2(self):
        model = Cell600Model(points_mode=2)
        self.assertEqual(len(model.vertices_4d), 13)

    def test_points_mode_3(self):
        model = Cell600Model(points_mode=3)
        self.assertEqual(len(model.vertices_4d), 45)

    def test_points_mode_4(self):
        model = Cell600Model(points_mode=4)
        self.assertEqual(len(model.vertices_4d), 87)

    def test_points_mode_5(self):
        model = Cell600Model(points_mode=5)
        self.assertEqual(len(model.vertices_4d), 119)

    def test_points_mode_6(self):
        model = Cell600Model(points_mode=6)
        self.assertEqual(len(model.vertices_4d), 120)

    def test_points_mode_7(self):
        model = Cell600Model(points_mode=7)
        self.assertEqual(len(model.vertices_4d), 120)

    def test_points_mode_8(self):
        model = Cell600Model(points_mode=8)
        self.assertEqual(len(model.vertices_4d), 120)

    def test_points_mode_9(self):
        model = Cell600Model(points_mode=9)
        self.assertEqual(len(model.vertices_4d), 120)

    def test_hopf_edge_coloring(self):
        """
        Tests that the 'hopf' edge coloring results in 24 edges of each of the 5 colors,
        and the remaining 600 edges are white.
        """
        model = Cell600Model(edge_coloring="hopf")
        
        red = np.array([1.0, 0.0, 0.0])
        blue = np.array([0.0, 0.0, 1.0])
        green = np.array([0.0, 1.0, 0.0])
        yellow = np.array([1.0, 1.0, 0.0])
        purple = np.array([1.0, 0.0, 1.0])
        cyan = np.array([0.0, 1.0, 1.0])
        white = np.array([1.0, 1.0, 1.0])
        
        colors = [red, blue, green, yellow, purple, cyan, white]
        color_counts = {tuple(c): 0 for c in colors}
        
        for edge_color in model.edge_colors:
            # Find the closest color in the list of 7 colors
            distances = [np.linalg.norm(edge_color - c) for c in colors]
            closest_color_idx = np.argmin(distances)
            closest_color = colors[closest_color_idx]
            color_counts[tuple(closest_color)] += 1

        print("Color counts:", color_counts)

        self.assertEqual(color_counts[tuple(red)], 20, f"Red count is {color_counts[tuple(red)]}")
        self.assertEqual(color_counts[tuple(blue)], 20, f"Blue count is {color_counts[tuple(blue)]}")
        self.assertEqual(color_counts[tuple(green)], 20, f"Green count is {color_counts[tuple(green)]}")
        self.assertEqual(color_counts[tuple(yellow)], 20, f"Yellow count is {color_counts[tuple(yellow)]}")
        self.assertEqual(color_counts[tuple(purple)], 20, f"Purple count is {color_counts[tuple(purple)]}")
        self.assertEqual(color_counts[tuple(cyan)], 20, f"Cyan count is {color_counts[tuple(cyan)]}")
        self.assertEqual(color_counts[tuple(white)], 600, f"White count is {color_counts[tuple(white)]}")

    def test_adjacency_list_length(self):
        """
        Tests that each vertex in the 600-cell has 12 neighbors.
        """
        model = Cell600Model()
        adj = [[] for _ in range(len(model.vertices_4d))]
        for v1, v2 in model.edges:
            adj[v1].append(v2)
            adj[v2].append(v1)
        
        for i in range(len(model.vertices_4d)):
            self.assertEqual(len(adj[i]), 12)

if __name__ == '__main__':
    unittest.main()
