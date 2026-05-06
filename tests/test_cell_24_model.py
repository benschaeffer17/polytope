import unittest
import numpy as np
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from models.cell_24_model import Cell24Model

class Test24Cell(unittest.TestCase):
    def test_triangle_count(self):
        """
        Tests that the 24-cell has exactly 192 triangles (24 cells * 8 triangles).
        """
        model = Cell24Model()
        model._generate_triangles()
        self.assertEqual(len(model.triangles), 192)

if __name__ == '__main__':
    unittest.main()
