import numpy as np
from itertools import combinations
from .model import Model
from quaternion import q_mult
from polytopes import get_600_cell_vertices, get_600_cell_cells
from .color_constants import COLOR_VALUES, COLOR_SEQUENCE, get_scaling_multiplier_by_color

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
    def __init__(self, is_vertex_centered=False, edge_coloring="bfs", points_mode=None,
                 vertex_coloring="partition", blend=1.0, slice_mode="at_least", point_set="dfs", cell_contraction=1.0):
        super().__init__(blend=blend, cell_contraction=cell_contraction)
        self.base_vertices_4d, self.base_edges = get_120_cell()
        self.style.point_style.relative_size = 0.5
        self.style.line_style.relative_width = 0.15

        self.color_values = COLOR_VALUES
        self.color_sequence = COLOR_SEQUENCE

        # 1. Base initialization (Adjacency, etc)
        self.base_adj = [[] for _ in range(len(self.base_vertices_4d))]
        self.base_edge_map = {}
        for i, (v1, v2) in enumerate(self.base_edges):
            self.base_adj[v1].append(v2)
            self.base_adj[v2].append(v1)
            self.base_edge_map[tuple(sorted((v1, v2)))] = i

        # 2. Compute vertex coloring mappings
        self.vertex_color_maps = {
            "partition": self._compute_vertex_colors_partition(),
        }

        # 3. Handle vertex centering
        if is_vertex_centered:
            red_vertex_index = -1
            partition_map = self.vertex_color_maps["partition"]
            for i in range(len(self.base_vertices_4d)):
                if partition_map.get(i) == self.color_sequence[0]:
                    red_vertex_index = i
                    break
            if red_vertex_index != -1:
                translation_vector = self.base_vertices_4d[red_vertex_index]
                self.base_vertices_4d = self.base_vertices_4d - translation_vector

        # 4. Find start vertices (points at minimal distance from North Pole)
        north_pole = np.array([0.0, 0.0, 0.0, 1.0])
        distances_to_np = np.linalg.norm(self.base_vertices_4d - north_pole, axis=1)
        min_dist = np.min(distances_to_np)
        
        self.start_vertices = set()
        for i, dist in enumerate(distances_to_np):
            if np.isclose(dist, min_dist, atol=1e-5):
                self.start_vertices.add(i)

        # 5. Compute BFS depths (labels) for vertices
        self.vertex_depths = {}
        if self.start_vertices:
            q = [(v, 0) for v in sorted(list(self.start_vertices))]
            visited = set(self.start_vertices)
            for v in self.start_vertices:
                self.vertex_depths[v] = 0
            
            head = 0
            while head < len(q):
                curr_v, curr_dist = q[head]
                head += 1
                for neighbor in self.base_adj[curr_v]:
                    if neighbor not in visited:
                        visited.add(neighbor)
                        self.vertex_depths[neighbor] = curr_dist + 1
                        q.append((neighbor, curr_dist + 1))

        # 5b. Compute distance depths (labels) for vertices
        self.distance_depths = {}
        distances = []
        for i, v in enumerate(self.base_vertices_4d):
            dist = np.linalg.norm(v - north_pole)
            distances.append((i, dist))
            
        distances.sort(key=lambda x: x[1])
        
        current_depth = 0
        last_dist = -1.0
        for i, dist in distances:
            if dist > last_dist + 1e-5:
                current_depth += 1
                last_dist = dist
            self.distance_depths[i] = current_depth - 1

        # 5c. Compute hopf depths
        self.hopf_depths = {}
        # Hopf logic from 600-cell may not perfectly apply to 120-cell
        # However, we port it as requested to make visualizations similar
        from quaternion import order10
        q = order10
        base_ring = [np.array([1.0, 0.0, 0.0, 0.0])]
        for _ in range(9):
            base_ring.append(q_mult(base_ring[-1], q))
        base_ring = np.array(base_ring)

        visited_vertices = set()
        for i in range(len(self.base_vertices_4d)):
            if i in visited_vertices:
                continue
            
            v = self.base_vertices_4d[i]
            # Normalize for hopf logic (approximate since 120 centers are < 1 radius)
            v_norm = np.linalg.norm(v)
            v_quat = np.array([v[0], v[1], v[2], v[3]]) / (v_norm if v_norm > 1e-5 else 1.0)
            
            coset = np.array([q_mult(r, v_quat) * v_norm for r in base_ring])
            
            for j, q_v in enumerate(coset):
                q_v_vert = np.array([q_v[0], q_v[1], q_v[2], q_v[3]])
                distances_hopf = np.sum((self.base_vertices_4d - q_v_vert)**2, axis=1)
                closest_idx = np.argmin(distances_hopf)
                self.hopf_depths[closest_idx] = j
                visited_vertices.add(closest_idx)

        # 6. Compute remaining color maps
        self.vertex_color_maps["bfs"] = self._compute_vertex_colors_bfs()
        self.vertex_color_maps["distance"] = self._compute_vertex_colors_distance()
        self.vertex_color_maps["hopf"] = self._compute_vertex_colors_hopf()
        self.edge_color_maps = {
            "bfs": self._compute_edge_colors_bfs(),
            "icosi": self._compute_edge_colors_icosi(),
            "hopf": self._compute_edge_colors_hopf(),
            "zome": self._compute_edge_colors_zome()
        }

        # 7. Cull vertices and edges based on points_mode
        kept_vertices = set()
        if point_set == "dfs":
            active_depths = self.vertex_depths
        elif point_set == "distance":
            active_depths = self.distance_depths
        elif point_set == "hopf":
            active_depths = self.hopf_depths
        else:
            active_depths = self.vertex_depths
        
        if points_mode is not None and points_mode > 0 and active_depths:
            for v, depth in active_depths.items():
                if slice_mode == "exact":
                    if depth == points_mode - 1:
                        kept_vertices.add(v)
                elif slice_mode == "adjacent":
                    if points_mode - 2 <= depth <= points_mode:
                        kept_vertices.add(v)
                elif slice_mode == "echo":
                    max_depth = max(active_depths.values()) if active_depths else 0
                    if depth == points_mode - 1 or depth == max_depth - (points_mode - 1):
                        kept_vertices.add(v)
                else:
                    if depth < points_mode:
                        kept_vertices.add(v)
        else:
            kept_vertices = set(range(len(self.base_vertices_4d)))

        # Compacting vertices
        old_to_new_indices = {old_idx: new_idx for new_idx, old_idx in enumerate(sorted(list(kept_vertices)))}
        self.vertices_4d = self.base_vertices_4d[sorted(list(kept_vertices))]

        # Produce final self.colors
        selected_vertex_map = self.vertex_color_maps.get(vertex_coloring, {})
        self.colors = []
        for old_idx in sorted(list(kept_vertices)):
            color_sym = selected_vertex_map.get(old_idx, "BLACK" if vertex_coloring == "bfs" else "WHITE")
            color_val = self.color_values[color_sym] + [self.blend]
            self.colors.append(color_val)
        self.colors = np.array(self.colors, dtype=np.float32)

        # Cull and map edges
        selected_edge_map = self.edge_color_maps.get(edge_coloring, {})
        self.edges = []
        self.edge_colors = []
        
        for v1, v2 in self.base_edges:
            if v1 in kept_vertices and v2 in kept_vertices:
                edge_tuple = tuple(sorted((v1, v2)))
                if edge_coloring == "hopf" and edge_tuple not in selected_edge_map:
                    continue
                
                new_v1 = old_to_new_indices[v1]
                new_v2 = old_to_new_indices[v2]
                self.edges.append((new_v1, new_v2))
                
                color_sym = selected_edge_map.get(edge_tuple, "WHITE")
                color_val = self.color_values.get(color_sym, self.color_values["WHITE"]) + [self.blend]
                self.edge_colors.append(color_val)

        self.edge_colors = np.array(self.edge_colors, dtype=np.float32) if self.edge_colors else np.array([], dtype=np.float32)
        self.edge_width_multipliers = np.array([get_scaling_multiplier_by_color(color) for color in self.edge_colors], dtype=np.float32) if len(self.edge_colors) > 0 else np.array([], dtype=np.float32)

        self._generate_triangles()

    def _compute_vertex_colors_partition(self):
        color_map = {}
        for i, v in enumerate(self.base_vertices_4d):
            if np.sum(np.abs(v)) > 0.9:
                color_map[i] = self.color_sequence[0]
            elif np.all(np.abs(v) > 0.2):
                color_map[i] = self.color_sequence[1]
            else:
                color_map[i] = self.color_sequence[2]
        return color_map

    def _compute_vertex_colors_bfs(self):
        color_map = {}
        if not hasattr(self, 'start_vertices') or not self.start_vertices:
            return color_map
            
        for v, depth in self.vertex_depths.items():
            color_map[v] = self.color_sequence[depth % len(self.color_sequence)]
            
        return color_map

    def _compute_vertex_colors_distance(self):
        color_map = {}
        for v, depth in self.distance_depths.items():
            color_map[v] = self.color_sequence[depth % len(self.color_sequence)]
        return color_map

    def _compute_vertex_colors_hopf(self):
        color_map = {}
        for v, depth in self.hopf_depths.items():
            color_map[v] = self.color_sequence[depth % len(self.color_sequence)]
        return color_map

    def _compute_edge_colors_bfs(self):
        color_map = {}
        if not hasattr(self, 'start_vertices') or not self.start_vertices:
            return color_map
            
        color_index = 3
        working_set = set(self.start_vertices)
        colored_edges = set()
        
        while len(colored_edges) < len(self.base_edges):
            color = self.color_sequence[color_index % len(self.color_sequence)]
            next_working_set = set()
            
            for v1 in working_set:
                for v2 in self.base_adj[v1]:
                    edge = tuple(sorted((v1, v2)))
                    if edge not in colored_edges:
                        color_map[edge] = color
                        colored_edges.add(edge)
                        next_working_set.add(v2)
            
            working_set = next_working_set
            color_index += 1
            if not working_set:
                for i, (v1, v2) in enumerate(self.base_edges):
                    edge = tuple(sorted((v1, v2)))
                    if edge not in colored_edges:
                        working_set = {v1}
                        break
        return color_map

    def _compute_edge_colors_icosi(self):
        color_map = {}
        if not hasattr(self, 'start_vertices') or not self.start_vertices:
            return color_map
            
        color_index = 3
        frontier = set(self.start_vertices)
        total_working_set = set(self.start_vertices)
        colored_edges = set()
        
        while len(colored_edges) < len(self.base_edges):
            color = self.color_sequence[color_index % len(self.color_sequence)]
            
            if color_index % 2 == 0:
                next_frontier = set()
                for v1 in frontier:
                    for v2 in self.base_adj[v1]:
                        if v2 not in total_working_set:
                            edge = tuple(sorted((v1, v2)))
                            if edge not in colored_edges:
                                color_map[edge] = color
                                colored_edges.add(edge)
                                next_frontier.add(v2)
                frontier = next_frontier
                total_working_set.update(frontier)
            
            else:
                for v1 in total_working_set:
                    for v2 in self.base_adj[v1]:
                        if v2 in total_working_set:
                            edge = tuple(sorted((v1, v2)))
                            if edge not in colored_edges:
                                color_map[edge] = color
                                colored_edges.add(edge)
            
            color_index += 1
            if not frontier and len(colored_edges) < len(self.base_edges):
                for i, (v1, v2) in enumerate(self.base_edges):
                    edge = tuple(sorted((v1, v2)))
                    if edge not in colored_edges:
                        frontier = {v1}
                        total_working_set.add(v1)
                        break
        return color_map

    def _compute_edge_colors_hopf(self):
        color_map = {}
        from quaternion import order10
        q = order10
        base_ring = [np.array([1.0, 0.0, 0.0, 0.0])]
        for _ in range(9):
            base_ring.append(q_mult(base_ring[-1], q))
        base_ring = np.array(base_ring)

        visited_vertices = set()
        fibrations = []
        for i in range(len(self.base_vertices_4d)):
            if i in visited_vertices:
                continue
            
            v = self.base_vertices_4d[i]
            v_norm = np.linalg.norm(v)
            v_quat = np.array([v[0], v[1], v[2], v[3]]) / (v_norm if v_norm > 1e-5 else 1.0)
            coset = np.array([q_mult(r, v_quat) * v_norm for r in base_ring])
            
            fibration_indices = []
            for q_v in coset:
                q_v_vert = np.array([q_v[0], q_v[1], q_v[2], q_v[3]])
                distances = np.sum((self.base_vertices_4d - q_v_vert)**2, axis=1)
                closest_idx = np.argmin(distances)
                fibration_indices.append(closest_idx)
                visited_vertices.add(closest_idx)
            
            fibrations.append(fibration_indices)

        for i, fibration in enumerate(fibrations):
            color = self.color_sequence[i % len(self.color_sequence)]
            for j in range(len(fibration)):
                v1 = fibration[j]
                v2 = fibration[(j + 1) % len(fibration)]
                edge = tuple(sorted((v1, v2)))
                if edge in self.base_edge_map:
                    color_map[edge] = color
                    
        return color_map

    def _compute_edge_colors_zome(self):
        color_map = {}
        if not hasattr(self, 'start_vertices') or not self.start_vertices:
            return color_map

        vertex_classes = {}
        for v in range(len(self.base_vertices_4d)):
            if v not in self.vertex_depths:
                vertex_classes[v] = (0, 0)
                continue
            
            a = self.vertex_depths[v]
            if a == 0:
                b = 0
            else:
                b = sum(1 for neighbor in self.base_adj[v] if self.vertex_depths.get(neighbor) == a - 1)
            vertex_classes[v] = (a, b)
            
        edge_classes = {}
        for v1, v2 in self.base_edges:
            edge = tuple(sorted((v1, v2)))
            c1 = vertex_classes[v1]
            c2 = vertex_classes[v2]
            edge_class = tuple(sorted((c1, c2)))
            if edge_class not in edge_classes:
                edge_classes[edge_class] = []
            edge_classes[edge_class].append(edge)
            
        sorted_classes = sorted(list(edge_classes.keys()))
        
        for i, edge_class in enumerate(sorted_classes):
            color = self.color_sequence[(i + 3) % len(self.color_sequence)]
            for edge in edge_classes[edge_class]:
                color_map[edge] = color
                
        return color_map
