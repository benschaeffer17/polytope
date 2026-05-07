import unittest
from collections import Counter
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from models.cell_120_model import Cell120Model
from models.cell_600_model import Cell600Model
from models.cell_24_model import Cell24Model

class TestHopfFibration(unittest.TestCase):
    def test_120_cell_hopf_fibration(self):
        """
        Tests that the 120-cell's 120 cells dynamically cluster into exactly 
        12 Hopf fibers, where each fiber is a chain of exactly 10 dodecahedra.
        """
        model = Cell120Model(cell_coloring="hopf")
        
        # Count the number of cells in each fiber
        fiber_counts = Counter(model.cell_fibers.values())
        
        # Verify exactly 12 fibers were discovered
        self.assertEqual(len(fiber_counts), 12, "120-cell should have exactly 12 Hopf fibers.")
        
        # Verify each fiber contains exactly 10 cells
        for fiber_id, count in fiber_counts.items():
            self.assertEqual(count, 10, f"120-cell Fiber {fiber_id} should have exactly 10 cells, got {count}.")

    def test_24_cell_hopf_fibration(self):
        """
        Tests that the 24-cell's 24 cells dynamically cluster into exactly 
        6 Hopf fibers, where each fiber is a chain of exactly 4 octahedra.
        """
        model = Cell24Model(cell_coloring="hopf")
        
        # Count the number of cells in each fiber
        fiber_counts = Counter(model.cell_fibers.values())
        
        # Verify exactly 6 fibers were discovered
        self.assertEqual(len(fiber_counts), 6, "24-cell should have exactly 6 Hopf fibers.")
        
        # Verify each fiber contains exactly 4 cells
        for fiber_id, count in fiber_counts.items():
            self.assertEqual(count, 4, f"24-cell Fiber {fiber_id} should have exactly 4 cells, got {count}.")

    def test_600_cell_hopf_fibration(self):
        """
        Tests that the 600-cell's 600 cells cluster uniformly under the standard Hopf map.
        (Using the standard 'i' axis yields 150 fibers of 4 cells each).
        """
        model = Cell600Model(cell_coloring="hopf")
        
        # Count the number of cells in each fiber
        fiber_counts = Counter(model.cell_fibers.values())
        
        # Verify 150 fibers were discovered
        self.assertEqual(len(fiber_counts), 150, "600-cell should have exactly 150 Hopf fibers under the standard i-axis map.")
        
        # Verify each fiber contains exactly 4 cells
        for fiber_id, count in fiber_counts.items():
            self.assertEqual(count, 4, f"600-cell Fiber {fiber_id} should have exactly 4 cells, got {count}.")

if __name__ == '__main__':
    unittest.main()
