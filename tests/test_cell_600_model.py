
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
        Tests that the 'hopf' edge coloring results in groups of 20 and 10 edges,
        rotating through the color sequence.
        """
        model = Cell600Model(edge_coloring="hopf")
        
        from models.color_constants import COLOR_VALUES, COLOR_SEQUENCE
        
        color_counts = {name: 0 for name in COLOR_VALUES.keys()}
        
        for edge_color in model.edge_colors:
            # Find the exact match in the COLOR_VALUES
            for name, rgb in COLOR_VALUES.items():
                if np.allclose(edge_color[:3], rgb, atol=1e-5):
                    color_counts[name] += 1
                    break

        expected_counts = {name: 0 for name in COLOR_VALUES.keys()}
        for i in range(12):
            color_name = COLOR_SEQUENCE[i % len(COLOR_SEQUENCE)]
            expected_counts[color_name] += 10

        print("Color counts:", color_counts)

        for name in COLOR_VALUES.keys():
            self.assertEqual(
                color_counts[name], 
                expected_counts[name], 
                f"{name} count is {color_counts[name]}, expected {expected_counts[name]}"
            )

    def test_hopf_edge_count(self):
        """
        Tests that there are exactly 120 edges in hopf mode.
        """
        model = Cell600Model(edge_coloring="hopf")
        self.assertEqual(len(model.edges), 120)

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
