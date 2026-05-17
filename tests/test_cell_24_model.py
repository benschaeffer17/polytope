"""
Unit tests for the 24-Cell topological model.
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from models.cell_24_model import Cell24Model

class Test24Cell(unittest.TestCase):
    """Test suite validating the 24-Cell geometry generation."""
    def test_triangle_count(self):
        """
        Tests that the 24-cell has exactly 192 triangles (24 cells * 8 triangles).
        """
        model = Cell24Model()
        # pylint: disable=protected-access
        model._generate_triangles()
        # pylint: enable=protected-access
        self.assertEqual(len(model.triangles), 192)

if __name__ == '__main__':
    unittest.main()
