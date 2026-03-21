
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
                 vertex_coloring="partition"):
        super().__init__()
        self.vertices_4d, self.edges = get_600_cell()
        self.style.point_style.relative_size = 0.5
        self.style.line_style.relative_width = 0.15
        self._setup_coloring(edge_coloring, vertex_coloring)

        if is_vertex_centered:
            red_vertex_index = -1
            for i, color in enumerate(self.colors):
                if np.all(color == [1.0, 0.0, 0.0]):
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
                self.colors = self.colors[sorted(list(kept_vertices))]
                
                new_edges = []
                new_edge_colors = []
                new_edge_width_multipliers = []
                
                for i, (v1, v2) in enumerate(self.edges):
                    if v1 in kept_vertices and v2 in kept_vertices:
                        new_edges.append((old_to_new_indices[v1], old_to_new_indices[v2]))
                        new_edge_colors.append(self.edge_colors[i])
                        new_edge_width_multipliers.append(self.edge_width_multipliers[i])
                
                self.edges = new_edges
                self.edge_colors = np.array(new_edge_colors, dtype=np.float32)
                self.edge_width_multipliers = np.array(new_edge_width_multipliers, dtype=np.float32)


    def _setup_coloring(self, edge_coloring, vertex_coloring):
        red = [1.0, 0.0, 0.0]
        blue = [0.0, 0.0, 1.0]
        green = [0.0, 1.0, 0.0]
        yellow = [1.0, 1.0, 0.0]
        
        if vertex_coloring == "partition":
            self.colors = []
            for v in self.vertices_4d:
                if np.sum(np.abs(v)) == 1.0:
                    self.colors.append(red)
                elif np.all(np.abs(v) == 0.5):
                    self.colors.append(blue)
                else:
                    self.colors.append(green)
            self.colors = np.array(self.colors, dtype=np.float32)
        elif vertex_coloring == "bfs":
            self.colors = np.array([[0.0, 0.0, 0.0]] * len(self.vertices_4d), dtype=np.float32)
            
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

        start_vertex_pos = np.array([0.0, 0.0, 0.0, 1.0])
        start_vertex_index = -1
        for i, v in enumerate(self.vertices_4d):
            if np.allclose(v, start_vertex_pos):
                start_vertex_index = i
                break

        if start_vertex_index == -1:
            self.edge_colors = np.array([[1.0, 1.0, 1.0]] * len(self.edges), dtype=np.float32)
            self.edge_width_multipliers = np.array([1.0] * len(self.edges), dtype=np.float32)
            return

        adj = [[] for _ in range(len(self.vertices_4d))]
        edge_map = {}
        for i, (v1, v2) in enumerate(self.edges):
            adj[v1].append(v2)
            adj[v2].append(v1)
            edge_map[tuple(sorted((v1, v2)))] = i
        
        self.edge_colors = np.array([[1.0, 1.0, 1.0]] * len(self.edges), dtype=np.float32)
        colored_edges = set()
        colors = [green, yellow, red, blue]
        color_index = 0

        if edge_coloring == "bfs":
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
        
        elif edge_coloring == "icosi":
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
        else:
            # Default to white edges if coloring scheme is unknown
            pass

        self.edge_width_multipliers = np.array([1.0] * len(self.edges), dtype=np.float32)

