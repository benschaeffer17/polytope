
import numpy as np
from itertools import permutations, combinations
from .model import Model

def get_24_cell():
    """
    Returns the vertices and edges of a 24-cell.
    """
    vertices = set()
    for p in permutations([1, 1, 0, 0]):
        for i in range(1 << 2): # 2 is the number of non-zero elements
            signs = [(i >> j) & 1 for j in range(2)]
            v = list(p)
            k = 0
            for j in range(4):
                if v[j] != 0:
                    if signs[k] == 1:
                        v[j] *= -1
                    k += 1
            vertices.add(tuple(v))
    
    vertices = np.array(list(vertices), dtype=np.float32)

    edges = []
    for i, j in combinations(range(len(vertices)), 2):
        v1 = vertices[i]
        v2 = vertices[j]
        if np.linalg.norm(v1 - v2) < 1.5: # sqrt(2) is approx 1.414
            edges.append((i, j))
            
    return vertices, edges

class Cell24Model(Model):
    def __init__(self):
        super().__init__()
        self.vertices_4d, self.edges = get_24_cell()
        self.style.point_style.relative_size = 1.0
        self.style.line_style.relative_width = 0.45
        self._setup_coloring()

    def _setup_coloring(self):
        v_inner_indices = {i for i, v in enumerate(self.vertices_4d) if v[3] == -1}
        v_middle_indices = {i for i, v in enumerate(self.vertices_4d) if v[3] == 0}
        v_outer_indices = {i for i, v in enumerate(self.vertices_4d) if v[3] == 1}

        cyan = [0.0, 1.0, 1.0]
        orange = [1.0, 0.65, 0.0]
        pale_red = [1.0, 0.5, 0.5]
        self.colors = []
        for i in range(len(self.vertices_4d)):
            if i in v_inner_indices:
                self.colors.append(cyan)
            elif i in v_middle_indices:
                self.colors.append(orange)
            else:
                self.colors.append(pale_red)
        self.colors = np.array(self.colors, dtype=np.float32)

        self.edge_colors = []
        self.edge_width_multipliers = []
        
        green = [0.0, 1.0, 0.0]
        red = [1.0, 0.0, 0.0]
        blue = [0.0, 0.0, 1.0]
        yellow = [1.0, 1.0, 0.0]
        purple = [1.0, 0.0, 1.0]

        width_multipliers = {
            "red": 1.2, "green": 1.15, "blue": 1.1,
            "yellow": 1.05, "purple": 1.0
        }

        for i, j in self.edges:
            is_i_inner = i in v_inner_indices
            is_i_middle = i in v_middle_indices
            is_i_outer = i in v_outer_indices
            is_j_inner = j in v_inner_indices
            is_j_middle = j in v_middle_indices
            is_j_outer = j in v_outer_indices

            if is_i_inner and is_j_inner:
                self.edge_colors.append(green)
                self.edge_width_multipliers.append(width_multipliers["green"])
            elif (is_i_inner and is_j_middle) or (is_i_middle and is_j_inner):
                self.edge_colors.append(red)
                self.edge_width_multipliers.append(width_multipliers["red"])
            elif is_i_middle and is_j_middle:
                self.edge_colors.append(blue)
                self.edge_width_multipliers.append(width_multipliers["blue"])
            elif (is_i_middle and is_j_outer) or (is_i_outer and is_j_middle):
                self.edge_colors.append(yellow)
                self.edge_width_multipliers.append(width_multipliers["yellow"])
            elif is_i_outer and is_j_outer:
                self.edge_colors.append(purple)
                self.edge_width_multipliers.append(width_multipliers["purple"])
            else:
                self.edge_colors.append([1.0, 1.0, 1.0])
                self.edge_width_multipliers.append(1.0)
        
        self.edge_colors = np.array(self.edge_colors, dtype=np.float32)
        self.edge_width_multipliers = np.array(self.edge_width_multipliers, dtype=np.float32)
