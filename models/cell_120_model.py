
import numpy as np
from itertools import permutations, combinations
from .model import Model

def get_120_cell():
    """
    Returns the vertices and edges of a 120-cell.
    """
    phi = (1 + np.sqrt(5)) / 2
    
    vertices = set()

    # Generate vertices
    base_coords = [
        (2, 2, 0, 0),
        (np.sqrt(5), 1, 1, 1),
        (phi, phi, phi, 1/phi**2),
        (phi**2, 1/phi, 1/phi, 1/phi)
    ]

    for coords in base_coords:
        for p in set(permutations(coords)):
            for i in range(16): # signs
                v = list(p)
                if (i >> 0) & 1: v[0] *= -1
                if (i >> 1) & 1: v[1] *= -1
                if (i >> 2) & 1: v[2] *= -1
                if (i >> 3) & 1: v[3] *= -1
                vertices.add(tuple(v))
    
    vertices = np.array(list(vertices), dtype=np.float32)

    # Generate edges
    edges = []
    edge_length_sq = (3 - np.sqrt(5))**2
    for i, j in combinations(range(len(vertices)), 2):
        v1 = vertices[i]
        v2 = vertices[j]
        dist_sq = np.sum((v1 - v2)**2)
        if np.isclose(dist_sq, edge_length_sq, atol=1e-3):
            edges.append((i, j))
            
    return vertices, edges

class Cell120Model(Model):
    def __init__(self, blend=1.0):
        super().__init__(blend=blend)
        self.vertices_4d, self.edges = get_120_cell()
        self.style.point_style.relative_size = 0.33
        self.style.line_style.relative_width = 0.15
        self.colors = np.array([[1.0, 1.0, 1.0, self.blend]] * len(self.vertices_4d), dtype=np.float32)
        self.edge_colors = np.array([[1.0, 1.0, 1.0, self.blend]] * len(self.edges), dtype=np.float32)
        self.edge_width_multipliers = np.array([1.0] * len(self.edges), dtype=np.float32)
