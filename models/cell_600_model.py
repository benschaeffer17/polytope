import numpy as np
from itertools import permutations, combinations
from .model import Model
from quaternion import q_mult

def get_600_cell():
    """
    Returns the vertices and edges of a 600-cell.
    The vertices are the 120 elements of the binary icosahedral group.
    """
    phi = (1 + np.sqrt(5)) / 2
    vertices = set()

    # 8 vertices of the form (±1, 0, 0, 0)
    for i in range(4):
        v = [0, 0, 0, 0]
        v[i] = 1
        vertices.add(tuple(v))
        v[i] = -1
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
        if np.isclose(dist_sq, edge_length_sq, atol=1e-2):
            edges.append((i, j))

    return vertices, edges

class Cell600Model(Model):
    def __init__(self, is_vertex_centered=False, edge_coloring="bfs", points_mode=None,
                 vertex_coloring="partition", blend=1.0):
        super().__init__(blend=blend)
        self.base_vertices_4d, self.base_edges = get_600_cell()
        self.style.point_style.relative_size = 0.5
        self.style.line_style.relative_width = 0.15

        self.color_values = {
            "RED": [1.0, 0.0, 0.0],
            "BLUE": [0.0, 0.0, 1.0],
            "GREEN": [0.0, 1.0, 0.0],
            "YELLOW": [1.0, 1.0, 0.0],
            "PURPLE": [1.0, 0.0, 1.0],
            "CYAN": [0.0, 1.0, 1.0],
            "WHITE": [1.0, 1.0, 1.0],
            "BLACK": [0.0, 0.0, 0.0]
        }
        
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
        
        # 3. Handle vertex centering (translation) based on partition map (finding the first RED vertex)
        if is_vertex_centered:
            red_vertex_index = -1
            partition_map = self.vertex_color_maps["partition"]
            for i in range(len(self.base_vertices_4d)):
                if partition_map.get(i) == "RED":
                    red_vertex_index = i
                    break
            
            if red_vertex_index != -1:
                translation_vector = self.base_vertices_4d[red_vertex_index]
                self.base_vertices_4d = self.base_vertices_4d - translation_vector

        # 4. Find start vertex
        start_vertex_pos = np.array([0.0, 0.0, 0.0, 1.0])
        self.start_vertex_index = -1
        for i, v in enumerate(self.base_vertices_4d):
            if np.allclose(v, start_vertex_pos):
                self.start_vertex_index = i
                break

        # 5. Compute BFS depths (labels) for vertices
        self.vertex_depths = {}
        if self.start_vertex_index != -1:
            q = [(self.start_vertex_index, 0)]
            visited = {self.start_vertex_index}
            self.vertex_depths[self.start_vertex_index] = 0
            
            head = 0
            while head < len(q):
                curr_v, curr_dist = q[head]
                head += 1
                for neighbor in self.base_adj[curr_v]:
                    if neighbor not in visited:
                        visited.add(neighbor)
                        self.vertex_depths[neighbor] = curr_dist + 1
                        q.append((neighbor, curr_dist + 1))

        # 6. Compute remaining color maps
        self.vertex_color_maps["bfs"] = self._compute_vertex_colors_bfs()
        self.edge_color_maps = {
            "bfs": self._compute_edge_colors_bfs(),
            "icosi": self._compute_edge_colors_icosi(),
            "hopf": self._compute_edge_colors_hopf()
        }

        # 7. Cull vertices and edges based on points_mode
        kept_vertices = set()
        if points_mode is not None and points_mode > 0 and self.start_vertex_index != -1:
            for v, depth in self.vertex_depths.items():
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
                    continue  # Hopf effectively culls uncolored edges
                
                new_v1 = old_to_new_indices[v1]
                new_v2 = old_to_new_indices[v2]
                self.edges.append((new_v1, new_v2))
                
                color_sym = selected_edge_map.get(edge_tuple, "WHITE")
                color_val = self.color_values[color_sym] + [self.blend]
                self.edge_colors.append(color_val)

        self.edge_colors = np.array(self.edge_colors, dtype=np.float32) if self.edge_colors else np.array([], dtype=np.float32)
        self.edge_width_multipliers = np.array([1.0] * len(self.edges), dtype=np.float32)

    def _compute_vertex_colors_partition(self):
        color_map = {}
        for i, v in enumerate(self.base_vertices_4d):
            if np.sum(np.abs(v)) == 1.0:
                color_map[i] = "RED"
            elif np.all(np.abs(v) == 0.5):
                color_map[i] = "BLUE"
            else:
                color_map[i] = "GREEN"
        return color_map

    def _compute_vertex_colors_bfs(self):
        color_map = {}
        if self.start_vertex_index == -1:
            return color_map
            
        colors = ["RED", "GREEN", "BLUE", "YELLOW"]
        color_map[self.start_vertex_index] = colors[0]
        
        for v, depth in self.vertex_depths.items():
            color_map[v] = colors[depth % len(colors)]
            
        return color_map

    def _compute_edge_colors_bfs(self):
        color_map = {}
        if self.start_vertex_index == -1:
            return color_map
            
        colors = ["GREEN", "YELLOW", "RED", "BLUE"]
        color_index = 0
        working_set = {self.start_vertex_index}
        colored_edges = set()
        
        while len(colored_edges) < len(self.base_edges):
            color = colors[color_index % len(colors)]
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
        if self.start_vertex_index == -1:
            return color_map
            
        colors = ["GREEN", "YELLOW", "RED", "BLUE"]
        color_index = 0
        frontier = {self.start_vertex_index}
        total_working_set = {self.start_vertex_index}
        colored_edges = set()
        
        while len(colored_edges) < len(self.base_edges):
            color = colors[color_index % len(colors)]
            
            if color_index % 2 == 0: # Expand
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
            
            else: # Internal
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
        from quaternion import q_mult, order10
        colors = ["RED", "BLUE", "GREEN", "YELLOW", "PURPLE", "CYAN"]
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
            v_quat = np.array([v[0], v[1], v[2], v[3]])
            coset = np.array([q_mult(r, v_quat) for r in base_ring])
            
            fibration_indices = []
            for q_v in coset:
                q_v_vert = np.array([q_v[0], q_v[1], q_v[2], q_v[3]])
                distances = np.sum((self.base_vertices_4d - q_v_vert)**2, axis=1)
                closest_idx = np.argmin(distances)
                fibration_indices.append(closest_idx)
                visited_vertices.add(closest_idx)
            
            fibrations.append(fibration_indices)

        for i, fibration in enumerate(fibrations):
            color = colors[i % len(colors)]
            for j in range(len(fibration)):
                v1 = fibration[j]
                v2 = fibration[(j + 1) % len(fibration)]
                edge = tuple(sorted((v1, v2)))
                if edge in self.base_edge_map:
                    color_map[edge] = color
                    
        return color_map