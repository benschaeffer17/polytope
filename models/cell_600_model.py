
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
        self.vertices_4d, self.edges = get_600_cell()
        self.style.point_style.relative_size = 0.5
        self.style.line_style.relative_width = 0.15

        if is_vertex_centered:
            red_vertex_index = -1
            for i, color in enumerate(self.colors):
                if np.all(color[:3] == [1.0, 0.0, 0.0]):
                    red_vertex_index = i
                    break
            
            if red_vertex_index != -1:
                translation_vector = self.vertices_4d[red_vertex_index]
                self.vertices_4d = self.vertices_4d - translation_vector
        
        if points_mode is not None and points_mode > 0:
            start_vertex_pos = np.array([0.0, 0.0, 0.0, 1.0])
            start_vertex_index = -1
            for i, v in enumerate(self.vertices_4d):
                if np.allclose(v, start_vertex_pos):
                    start_vertex_index = i
                    break
            
            if start_vertex_index != -1:
                adj = [[] for _ in range(len(self.vertices_4d))]
                for v1, v2 in self.edges:
                    adj[v1].append(v2)
                    adj[v2].append(v1)
                
                q = [(start_vertex_index, 0)]
                visited = {start_vertex_index}
                kept_vertices = {start_vertex_index}
                
                for v, depth in q:
                    if depth >= points_mode - 1:
                        continue
                    
                    for neighbor in adj[v]:
                        if neighbor not in visited:
                            visited.add(neighbor)
                            kept_vertices.add(neighbor)
                            q.append((neighbor, depth + 1))
                
                old_to_new_indices = {old_idx: new_idx for new_idx, old_idx in enumerate(sorted(list(kept_vertices)))}
                
                self.vertices_4d = self.vertices_4d[sorted(list(kept_vertices))]
                
                new_edges = []
                
                for i, (v1, v2) in enumerate(self.edges):
                    if v1 in kept_vertices and v2 in kept_vertices:
                        new_edges.append((old_to_new_indices[v1], old_to_new_indices[v2]))
                
                self.edges = new_edges
        self._setup_coloring(edge_coloring, vertex_coloring)


    def _setup_coloring(self, edge_coloring, vertex_coloring):
        red = [1.0, 0.0, 0.0, self.blend]
        blue = [0.0, 0.0, 1.0, self.blend]
        green = [0.0, 1.0, 0.0, self.blend]
        yellow = [1.0, 1.0, 0.0, self.blend]
        purple = [1.0, 0.0, 1.0, self.blend]
        cyan = [0.0, 1.0, 1.0, self.blend]
        
        if vertex_coloring == "partition":
            self._vertex_coloring_partition(red, blue, green)
        elif vertex_coloring == "bfs":
            self._vertex_coloring_bfs(red, green, blue, yellow)

        start_vertex_pos = np.array([0.0, 0.0, 0.0, 1.0])
        start_vertex_index = -1
        for i, v in enumerate(self.vertices_4d):
            if np.allclose(v, start_vertex_pos):
                start_vertex_index = i
                break

        if start_vertex_index == -1:
            self.edge_colors = np.array([[1.0, 1.0, 1.0, self.blend]] * len(self.edges), dtype=np.float32)
            self.edge_width_multipliers = np.array([1.0] * len(self.edges), dtype=np.float32)
            return

        adj = [[] for _ in range(len(self.vertices_4d))]
        edge_map = {}
        for i, (v1, v2) in enumerate(self.edges):
            adj[v1].append(v2)
            adj[v2].append(v1)
            edge_map[tuple(sorted((v1, v2)))] = i
        
        self.edge_colors = np.array([[1.0, 1.0, 1.0, self.blend]] * len(self.edges), dtype=np.float32)
        colored_edges = set()
        
        if edge_coloring == "bfs":
            self._edge_coloring_bfs(start_vertex_index, adj, edge_map, colored_edges, green, yellow, red, blue)
        elif edge_coloring == "icosi":
            self._edge_coloring_icosi(start_vertex_index, adj, edge_map, colored_edges, green, yellow, red, blue)
        elif edge_coloring == "hopf":
            self._edge_coloring_hopf(edge_map, colored_edges, red, blue, green, yellow, purple, cyan)
        else:
            # Default to white edges if coloring scheme is unknown
            pass

        self.edge_width_multipliers = np.array([1.0] * len(self.edges), dtype=np.float32)

    def _vertex_coloring_partition(self, red, blue, green):
        self.colors = []
        for v in self.vertices_4d:
            if np.sum(np.abs(v)) == 1.0:
                self.colors.append(red)
            elif np.all(np.abs(v) == 0.5):
                self.colors.append(blue)
            else:
                self.colors.append(green)
        self.colors = np.array(self.colors, dtype=np.float32)

    def _vertex_coloring_bfs(self, red, green, blue, yellow):
        self.colors = np.array([[0.0, 0.0, 0.0, self.blend]] * len(self.vertices_4d), dtype=np.float32)
        
        start_vertex_pos = np.array([0.0, 0.0, 0.0, 1.0])
        start_vertex_index = -1
        for i, v in enumerate(self.vertices_4d):
            if np.allclose(v, start_vertex_pos):
                start_vertex_index = i
                break
        
        if start_vertex_index != -1:
            adj = [[] for _ in range(len(self.vertices_4d))]
            for v1, v2 in self.edges:
                adj[v1].append(v2)
                adj[v2].append(v1)

            colors = [red, green, blue, yellow]
            color_index = 0
            
            q = [(start_vertex_index, 0)]
            visited = {start_vertex_index}
            self.colors[start_vertex_index] = colors[0]
            
            head = 0
            while head < len(q):
                curr_v, curr_dist = q[head]
                head += 1
                
                for neighbor in adj[curr_v]:
                    if neighbor not in visited:
                        visited.add(neighbor)
                        color = colors[(curr_dist + 1) % len(colors)]
                        self.colors[neighbor] = color
                        q.append((neighbor, curr_dist + 1))

    def _edge_coloring_bfs(self, start_vertex_index, adj, edge_map, colored_edges, green, yellow, red, blue):
        colors = [green, yellow, red, blue]
        color_index = 0
        working_set = {start_vertex_index}
        while len(colored_edges) < len(self.edges):
            color = colors[color_index % len(colors)]
            next_working_set = set()
            
            for v1 in working_set:
                for v2 in adj[v1]:
                    edge = tuple(sorted((v1, v2)))
                    if edge not in colored_edges:
                        edge_index = edge_map[edge]
                        self.edge_colors[edge_index] = color
                        colored_edges.add(edge)
                        next_working_set.add(v2)
            
            working_set = next_working_set
            color_index += 1
            if not working_set:
                for i, (v1, v2) in enumerate(self.edges):
                    edge = tuple(sorted((v1, v2)))
                    if edge not in colored_edges:
                        working_set = {v1}
                        break

    def _edge_coloring_icosi(self, start_vertex_index, adj, edge_map, colored_edges, green, yellow, red, blue):
        colors = [green, yellow, red, blue]
        color_index = 0
        frontier = {start_vertex_index}
        total_working_set = {start_vertex_index}
        
        while len(colored_edges) < len(self.edges):
            color = colors[color_index % len(colors)]
            
            if color_index % 2 == 0: # Expand
                next_frontier = set()
                for v1 in frontier:
                    for v2 in adj[v1]:
                        if v2 not in total_working_set:
                            edge = tuple(sorted((v1, v2)))
                            if edge not in colored_edges:
                                edge_index = edge_map[edge]
                                self.edge_colors[edge_index] = color
                                colored_edges.add(edge)
                                next_frontier.add(v2)
                frontier = next_frontier
                total_working_set.update(frontier)
            
            else: # Internal
                for v1 in total_working_set:
                    for v2 in adj[v1]:
                        if v2 in total_working_set:
                            edge = tuple(sorted((v1, v2)))
                            if edge not in colored_edges:
                                edge_index = edge_map[edge]
                                self.edge_colors[edge_index] = color
                                colored_edges.add(edge)
            
            color_index += 1
            if not frontier and len(colored_edges) < len(self.edges):
                for i, (v1, v2) in enumerate(self.edges):
                    edge = tuple(sorted((v1, v2)))
                    if edge not in colored_edges:
                        frontier = {v1}
                        total_working_set.add(v1)
                        break

    def _edge_coloring_hopf(self, edge_map, colored_edges, red, blue, green, yellow, purple, cyan):
        from quaternion import q_mult, order10
        colors = [red, blue, green, yellow, purple, cyan]
        q = order10
        base_ring = [np.array([1.0, 0.0, 0.0, 0.0])]
        for _ in range(9):
            base_ring.append(q_mult(base_ring[-1], q))
        base_ring = np.array(base_ring)

        visited_vertices = set()
        fibrations = []
        for i in range(len(self.vertices_4d)):
            if i in visited_vertices:
                continue
            
            v = self.vertices_4d[i]
            v_quat = np.array([v[0], v[1], v[2], v[3]])
            coset = np.array([q_mult(r, v_quat) for r in base_ring])
            
            fibration_indices = []
            for q_v in coset:
                # convert back to (x, y, z, w)
                q_v_vert = np.array([q_v[0], q_v[1], q_v[2], q_v[3]])
                # Find the closest vertex index
                distances = np.sum((self.vertices_4d - q_v_vert)**2, axis=1)
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
                if edge in edge_map:
                    edge_index = edge_map[edge]
                    self.edge_colors[edge_index] = np.array(color)
                    colored_edges.add(edge)
        
        # Filter edges and edge_colors
        self.edges = list(colored_edges)
        edge_colors = np.array([[1.0, 1.0, 1.0, self.blend]] * len(self.edges), dtype=np.float32)
        for i, edge in enumerate(self.edges):
            edge_colors[i] = self.edge_colors[edge_map[edge]]
        self.edge_colors = edge_colors
