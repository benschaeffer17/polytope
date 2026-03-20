
import numpy as np
from itertools import permutations, combinations
from .model import Model

def get_600_cell():
    """
    Returns the vertices and edges of a 600-cell.
    The vertices are the 120 elements of the binary icosahedral group.
    """
    phi = (1 + np.sqrt(5)) / 2
    vertices = set()

    # 8 vertices of the form (±1, 0, 0, 0)
    for p in set(permutations([1, 0, 0, 0])):
        v = list(p)
        vertices.add(tuple(v))
        v[0] *= -1
        vertices.add(tuple(v))

    # 16 vertices of the form 1/2 * (±1, ±1, ±1, ±1)
    for i in range(16):
        v = [0.5, 0.5, 0.5, 0.5]
        if (i >> 0) & 1: v[0] *= -1
        if (i >> 1) & 1: v[1] *= -1
        if (i >> 2) & 1: v[2] *= -1
        if (i >> 3) & 1: v[3] *= -1
        vertices.add(tuple(v))

    # 96 vertices from even permutations of (0, ±1/2, ±1/(2φ), ±φ/2)
    vals = [0, 0.5, 0.5 / phi, 0.5 * phi]
    for p_vals in set(permutations(vals)):
        p = list(p_vals)
        # Check for even permutation
        inversions = 0
        for i in range(len(p)):
            for j in range(i + 1, len(p)):
                # Create a temporary list for comparison to handle the case where p[i] == p[j]
                temp_p = list(p)
                if temp_p[i] > temp_p[j]:
                    inversions += 1
        
        if inversions % 2 == 0:
            for i in range(8): # signs for non-zero elements
                v = list(p)
                k = 0
                for j in range(4):
                    if v[j] != 0:
                        if (i >> k) & 1:
                            v[j] *= -1
                        k += 1
                vertices.add(tuple(v))
                
    vertices = np.array(list(vertices), dtype=np.float32)
    
    # Edges
    edges = []
    edge_length_sq = (1/phi)**2
    for i, j in combinations(range(len(vertices)), 2):
        v1 = vertices[i]
        v2 = vertices[j]
        dist_sq = np.sum((v1 - v2)**2)
        if np.isclose(dist_sq, edge_length_sq, atol=1e-3):
            edges.append((i, j))

    return vertices, edges

class Cell600Model(Model):
    def __init__(self):
        super().__init__()
        self.vertices_4d, self.edges = get_600_cell()
        self.style.point_style.relative_size = 0.5
        self.style.line_style.relative_width = 0.15
        self._setup_coloring()

    def _setup_coloring(self):
        red = [1.0, 0.0, 0.0]
        blue = [0.0, 0.0, 1.0]
        green = [0.0, 1.0, 0.0]
        self.colors = []
        for v in self.vertices_4d:
            if np.sum(np.abs(v)) == 1.0:
                self.colors.append(red)
            elif np.all(np.abs(v) == 0.5):
                self.colors.append(blue)
            else:
                self.colors.append(green)
        self.colors = np.array(self.colors, dtype=np.float32)
        self.edge_colors = np.array([[1.0, 1.0, 1.0]] * len(self.edges), dtype=np.float32)
        self.edge_width_multipliers = np.array([1.0] * len(self.edges), dtype=np.float32)
