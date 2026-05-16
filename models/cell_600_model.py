"""Module representing polytope geometry and rendering logic."""
import numpy as np
from .model import Model
from polytopes import get_600_cell_vertices

def get_600_cell():
    """
    Returns the vertices and edges of a 600-cell.
    The vertices are the 120 elements of the binary icosahedral group.
    """
    phi = (1 + np.sqrt(5)) / 2
    vertices = get_600_cell_vertices()

    # Edges
    from scipy.spatial import cKDTree
    tree = cKDTree(vertices)
    edge_length = 1/phi
    pairs = tree.query_pairs(edge_length + 1e-3)
    edges = []
    edge_length_sq = edge_length**2
    for i, j in pairs:
        dist_sq = np.sum((vertices[i] - vertices[j])**2)
        if np.isclose(dist_sq, edge_length_sq, atol=1e-2):
            edges.append((i, j))

    return vertices, edges

class Cell600Model(Model):
    """Base representation class."""
    def __init__(self, is_vertex_centered=False, edge_coloring="bfs", points_mode=None,
                 vertex_coloring="partition", blend=1.0, slice_mode="at_least", point_set="dfs", cell_contraction=1.0, cell_coloring="hopf"):
        from quaternion import hopf_600_L, hopf_600_R
        super().__init__(blend=blend, cell_contraction=cell_contraction, cell_coloring=cell_coloring, hopf_L=hopf_600_L, hopf_R=hopf_600_R)
        self.base_vertices_4d, self.base_edges = get_600_cell()
        self._initialize_base_geometry(is_vertex_centered)
        self._compute_base_depths(start_mode="exact_pole")

        self._compute_all_color_maps()
        self._finalize_geometry(points_mode, slice_mode, point_set, vertex_coloring, edge_coloring)

    def _compute_vertex_colors_partition(self):
        """Executes internal logic."""
        color_map = {}
        for i, v in enumerate(self.base_vertices_4d):
            if np.sum(np.abs(v)) == 1.0:
                color_map[i] = self.color_sequence[0]
            elif np.all(np.abs(v) == 0.5):
                color_map[i] = self.color_sequence[1]
            else:
                color_map[i] = self.color_sequence[2]
        return color_map
