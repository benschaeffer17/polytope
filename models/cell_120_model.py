"""Module representing polytope geometry and rendering logic."""
import numpy as np
from .model import Model
from polytopes import get_600_cell_vertices, get_600_cell_cells

def get_120_cell():
    """
    Returns the vertices and edges of a 120-cell.
    The vertices are the centers of the 600-cell facets.
    """
    vertices_600 = get_600_cell_vertices()
    cells_600 = get_600_cell_cells(vertices_600)

    vertices = []
    for cell in cells_600:
        vertices.append(np.mean(vertices_600[cell], axis=0))
    vertices = np.array(vertices, dtype=np.float32)

    # Sort vertices to make them deterministic
    # Sort by w, z, y, x
    sort_indices = np.lexsort((vertices[:,0], vertices[:,1], vertices[:,2], vertices[:,3]))
    vertices = vertices[sort_indices]

    # Generate edges
    from scipy.spatial import cKDTree
    tree = cKDTree(vertices)

    # Find distance to closest distinct neighbor for vertex 0
    dists, indices = tree.query(vertices[0], k=2)
    edge_length = dists[1]

    pairs = tree.query_pairs(edge_length + 1e-3)
    edges = []
    edge_length_sq = edge_length**2
    for i, j in pairs:
        dist_sq = np.sum((vertices[i] - vertices[j])**2)
        if np.isclose(dist_sq, edge_length_sq, atol=1e-5):
            edges.append((i, j))

    return vertices, edges

class Cell120Model(Model):
    """Base representation class."""
    def __init__(self, is_vertex_centered=False, edge_coloring="bfs", points_mode=None,
                 vertex_coloring="partition", blend=1.0, slice_mode="at_least", point_set="dfs", cell_contraction=1.0, cell_coloring="hopf"):
        from quaternion import q_identity, order10
        super().__init__(blend=blend, cell_contraction=cell_contraction, cell_coloring=cell_coloring, hopf_L=q_identity, hopf_R=order10)
        self.base_vertices_4d, self.base_edges = get_120_cell()
        self._initialize_base_geometry(is_vertex_centered)
        self._compute_base_depths(start_mode="nearest_pole")

        self._compute_all_color_maps()
        self._finalize_geometry(points_mode, slice_mode, point_set, vertex_coloring, edge_coloring)

    def _compute_vertex_colors_partition(self):
        """Executes internal logic."""
        color_map = {}
        for i, v in enumerate(self.base_vertices_4d):
            if np.sum(np.abs(v)) > 0.9:
                color_map[i] = self.color_sequence[0]
            elif np.all(np.abs(v) > 0.2):
                color_map[i] = self.color_sequence[1]
            else:
                color_map[i] = self.color_sequence[2]
        return color_map


