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
        Tests that the 120-cell dynamically clusters into exactly 12 Hopf fibers,
        where each fiber is a chain of exactly 10 dodecahedra.
        Adjacent dodecahedra in a chain must share a face (5 vertices).
        """
        model = Cell120Model(cell_coloring="hopf")
        model._generate_triangles()
        
        self.assertEqual(len(model.cell_chains), 12, "120-cell should have exactly 12 chains.")
        for chain in model.cell_chains:
            self.assertEqual(len(chain), 10, "Each 120-cell chain should have exactly 10 cells.")
            # Verify adjacency
            for k in range(len(chain)):
                c1 = set(model.cells[chain[k]])
                c2 = set(model.cells[chain[(k+1) % 10]])
                shared = len(c1.intersection(c2))
                self.assertEqual(shared, 5, f"120-cell adjacent cells must share a face (5 vertices), but shared {shared}.")

    def test_600_cell_hopf_fibration(self):
        """
        Tests that the 600-cell dynamically clusters into exactly 20 Hopf fibers,
        where each fiber is an orbit of exactly 30 tetrahedra under the L*c*R screw motion.
        For the equator orbits, adjacent tetrahedra in the chain mathematically share a face (3 vertices).
        """
        model = Cell600Model(cell_coloring="hopf")
        model._generate_triangles()
        
        self.assertEqual(len(model.cell_chains), 20, "600-cell should have exactly 20 chains.")
        connected_helices_found = 0
        
        for chain in model.cell_chains:
            self.assertEqual(len(chain), 30, "Each 600-cell chain should have exactly 30 cells.")
            # Check if this chain is a perfect equator helix (adjacent cells share faces)
            is_connected = True
            for k in range(len(chain)):
                c1 = set(model.cells[chain[k]])
                c2 = set(model.cells[chain[(k+1) % 30]])
                shared = len(c1.intersection(c2))
                if shared != 3:
                    is_connected = False
                    break
            
            if is_connected:
                connected_helices_found += 1
                
        self.assertTrue(connected_helices_found > 0, "At least one orbit must be a perfect Boerdijk-Coxeter helix sharing 3-vertex faces.")

    def test_24_cell_hopf_fibration(self):
        """
        Tests that the 24-cell dynamically clusters into exactly 6 Hopf fibers,
        where each fiber is a chain of exactly 4 octahedra.
        Adjacent octahedra in a chain must share exactly 1 vertex.
        """
        model = Cell24Model(cell_coloring="hopf")
        model._generate_triangles()
        
        self.assertEqual(len(model.cell_chains), 6, "24-cell should have exactly 6 chains.")
        for chain in model.cell_chains:
            self.assertEqual(len(chain), 4, "Each 24-cell chain should have exactly 4 cells.")
            # Verify adjacency
            for k in range(len(chain)):
                c1 = set(model.cells[chain[k]])
                c2 = set(model.cells[chain[(k+1) % 4]])
                shared = len(c1.intersection(c2))
                self.assertEqual(shared, 1, f"24-cell adjacent cells must share exactly 1 vertex, but shared {shared}.")

if __name__ == '__main__':
    unittest.main()
