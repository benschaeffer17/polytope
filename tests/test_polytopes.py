import unittest
import numpy as np
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from polytopes import get_600_cell_vertices, get_600_cell_cells

class TestPolytopes(unittest.TestCase):

    def test_get_600_cell_vertices(self):
        """
        Tests that the 600-cell has 120 vertices.
        """
        vertices = get_600_cell_vertices()
        # Note: A 600-cell has 120 vertices (and 600 facets). The 120-cell has 600 vertices.
        self.assertEqual(len(vertices), 120, "A 600-cell should have exactly 120 vertices.")

    def test_get_600_cell_cells(self):
        """
        Tests that the 600-cell has 600 cells (facets) and each is a tetrahedron (4 vertices).
        """
        cells = get_600_cell_cells()
        self.assertEqual(len(cells), 600, "A 600-cell should have exactly 600 facets.")
        for cell in cells:
            self.assertEqual(len(cell), 4, "Each facet of a 600-cell should be a tetrahedron (4 vertices).")

if __name__ == '__main__':
    unittest.main()