"""Module representing polytope geometry and rendering logic."""

import numpy as np
from viz.style import Style

class Model:
    """Base representation class."""
    def __init__(self, blend=1.0, cell_contraction=1.0, cell_coloring="default", hopf_L=None, hopf_R=None):
        """Executes internal logic."""
        self.vertices_4d = None
        self.edges = None
        self.colors = None
        self.style = Style()
        self.edge_colors = None
        self.edge_width_multipliers = None
        self.blend = blend
        self.cell_contraction = cell_contraction
        self.cell_coloring = cell_coloring
        self.hopf_L = hopf_L
        self.hopf_R = hopf_R
        self.cell_fibers = {}
        
        # Abstract fields initialized by concrete subclasses or lifecycle methods
        self.base_vertices_4d = np.array([])
        self.base_edges = []
        self.base_adj = []
        self.base_edge_map = {}
        self.start_vertices = set()
        self.vertex_depths = {}
        self.distance_depths = {}
        self.hopf_depths = {}
        self.vertex_color_maps = {}
        self.edge_color_maps = {}
        self.color_values = {}
        self.color_sequence = []
        self.cell_chains = []
        self.cells = []
        self.chain_groupings = []
        self.chain_grouping_names = []

        self.triangle_vertices_4d = None
        self.triangles = None
        self.triangle_normals_4d = None
        self.triangle_colors = None

        self.num_chains = 0
        self.triangles_by_chain = []

    def _initialize_base_geometry(self, is_vertex_centered):
        """Executes internal logic."""
        from .color_constants import COLOR_VALUES, COLOR_SEQUENCE
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

    def _compute_base_depths(self, start_mode):
        """Executes internal logic."""
        # 4. Find start vertices
        north_pole = np.array([0.0, 0.0, 0.0, 1.0])
        self.start_vertices = set()

        if start_mode == "exact_pole":
            for i, v in enumerate(self.base_vertices_4d):
                if np.allclose(v, north_pole):
                    self.start_vertices.add(i)
                    break
        elif start_mode == "nearest_pole":
            distances_to_np = np.linalg.norm(self.base_vertices_4d - north_pole, axis=1)
            min_dist = np.min(distances_to_np)
            for i, dist in enumerate(distances_to_np):
                if np.isclose(dist, min_dist, atol=1e-5):
                    self.start_vertices.add(i)

        # 5. Compute BFS depths
        self.vertex_depths = {}
        if self.start_vertices:
            start_list = sorted(list(self.start_vertices))
            q = [(v, 0) for v in start_list]
            visited = set(start_list)
            for v in start_list:
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

        # 5b. Compute distance depths
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
        from quaternion import order10, q_mult
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
            v_norm = np.linalg.norm(v)
            v_quat = np.array([v[0], v[1], v[2], v[3]]) / (v_norm if v_norm > 1e-5 else 1.0)

            coset = np.array([q_mult(r, v_quat) * v_norm for r in base_ring])

            for j, q_v in enumerate(coset):
                q_v_vert = np.array([q_v[0], q_v[1], q_v[2], q_v[3]])
                distances_hopf = np.sum((self.base_vertices_4d - q_v_vert)**2, axis=1)
                closest_idx = np.argmin(distances_hopf)
                self.hopf_depths[closest_idx] = j
                visited_vertices.add(closest_idx)

    def _compute_all_color_maps(self):
        """Executes internal logic."""
        self.vertex_color_maps["bfs"] = self._compute_vertex_colors_bfs()
        self.vertex_color_maps["distance"] = self._compute_vertex_colors_distance()
        self.vertex_color_maps["hopf"] = self._compute_vertex_colors_hopf()
        self.edge_color_maps = {
            "bfs": self._compute_edge_colors_bfs(),
            "icosi": self._compute_edge_colors_icosi(),
            "hopf": self._compute_edge_colors_hopf(),
            "zome": self._compute_edge_colors_zome()
        }

    def _finalize_geometry(self, points_mode, slice_mode, point_set, vertex_coloring, edge_coloring):
        """Executes internal logic."""
        # 7. Cull vertices and edges based on points_mode
        kept_vertices = set()
        if point_set == "dfs":
            active_depths = getattr(self, 'vertex_depths', {})
        elif point_set == "distance":
            active_depths = getattr(self, 'distance_depths', {})
        elif point_set == "hopf":
            active_depths = getattr(self, 'hopf_depths', {})
        else:
            active_depths = getattr(self, 'vertex_depths', {})

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
            color_val = self.color_values.get(color_sym, [1,1,1]) + [self.blend]
            self.colors.append(color_val)
        self.colors = np.array(self.colors, dtype=np.float32)

        # Cull and map edges
        selected_edge_map = getattr(self, 'edge_color_maps', {}).get(edge_coloring, {})
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
                color_val = self.color_values.get(color_sym, [1,1,1]) + [self.blend]
                self.edge_colors.append(color_val)

        self.edge_colors = np.array(self.edge_colors, dtype=np.float32) if self.edge_colors else np.array([], dtype=np.float32)
        from .color_constants import get_scaling_multiplier_by_color
        self.edge_width_multipliers = np.array([get_scaling_multiplier_by_color(color) for color in self.edge_colors], dtype=np.float32) if len(self.edge_colors) > 0 else np.array([], dtype=np.float32)

        self._generate_triangles()

    def _generate_triangles(self):
        """Executes internal logic."""
        from scipy.spatial import ConvexHull

        vertices = self.vertices_4d
        if vertices is None or len(vertices) < 5:
            self.triangle_vertices_4d = np.array([], dtype=np.float32)
            self.triangles = []
            self.triangle_normals_4d = np.array([], dtype=np.float32)
            self.triangle_colors = np.array([], dtype=np.float32)
            return

        try:
            # In an N-dimensional space, scipy.spatial.ConvexHull mathematically computes the boundary
            # of the convex polytope formed by the given vertices. The boundary of an N-dimensional
            # convex hull is composed entirely of (N-1)-dimensional simplices.
            # In our 4D space (N=4), an (N-1)-dimensional simplex is a 3-simplex, which is a tetrahedron.
            # This means ConvexHull will ALWAYS return a collection of tetrahedra, regardless of the
            # true shapes of the 3D cells. For instance, the 120-cell's dodecahedral cells are artificially
            # decomposed (shattered) into arbitrary tetrahedra to satisfy this simplex requirement.
            hull = ConvexHull(vertices)
            equations = hull.equations
            simplices = hull.simplices
        except:
            self.triangle_vertices_4d = np.array([], dtype=np.float32)
            self.triangles = []
            self.triangle_normals_4d = np.array([], dtype=np.float32)
            self.triangle_colors = np.array([], dtype=np.float32)
            return

        # -------------------------------------------------------------------------
        # 1. Reconstruct True 3D Cells
        # -------------------------------------------------------------------------
        # To undo the artificial tetrahedral decomposition and recover the true 3D cells
        # (like the dodecahedra of the 120-cell), we group the tetrahedra by the 4D hyperplane
        # they lie on. If multiple tetrahedra share the exact same outward normal vector and
        # offset (the hyperplane equation), they are coplanar in 4D space and therefore
        # constitute parts of the exact same 3D cell.
        eqs_rounded = np.round(equations, 4)
        unique_eqs, inverse_indices = np.unique(eqs_rounded, axis=0, return_inverse=True)

        cells = []
        for i in range(len(unique_eqs)):
            simplex_indices = np.where(inverse_indices == i)[0]
            cell_verts = set()
            for idx in simplex_indices:
                cell_verts.update(simplices[idx])
            cells.append(list(cell_verts))

        t_verts = []
        t_tris = []
        t_norms = []
        t_colors = []

        # -------------------------------------------------------------------------
        # Dynamic Hopf Fibration Cell Clustering
        # -------------------------------------------------------------------------
        # We mathematically discover the chains of cells (fibers) by following
        # the geometric orbit generated by c_next = L * c * R.
        cell_colors = []
        if self.cell_coloring == "hopf":
            from quaternion import q_mult, q_identity
            from .color_constants import COLOR_SEQUENCE, COLOR_VALUES

            L_quat = self.hopf_L if self.hopf_L is not None else q_identity
            R_quat = self.hopf_R if self.hopf_R is not None else q_identity

            centers = []
            for cell_v_indices in cells:
                c = np.mean(vertices[list(cell_v_indices)], axis=0)
                c_norm = np.linalg.norm(c)
                c = c / c_norm if c_norm > 1e-6 else np.array([1.0, 0.0, 0.0, 0.0])
                centers.append(c)
            centers = np.array(centers)

            chains = []

            if len(centers) == 600:
                # -------------------------------------------------------------------------
                # 600-Cell Symmetric Boerdijk-Coxeter Helix Generation
                # -------------------------------------------------------------------------
                # The 600-cell discrete Hopf fibration partitions the 600 tetrahedral cells
                # into exactly 20 disjoint chains of 30 cells each. Each of these 30-cell
                # chains physically forms a perfectly face-adjacent Boerdijk-Coxeter helix!
                #
                # However, 4D screw motions (isometries of the form c -> L * c * R) have a
                # subtle property: their translation distance varies depending on the invariant
                # torus the points lie on. Because the 600 cells are scattered throughout the
                # 3-sphere, a single global screw motion can only translate cells by exactly
                # one face-adjacent step if those cells lie exactly on its perfect "equator".
                #
                # This mathematically proves why out of the 20 orbits generated by the screw
                # motion, exactly 2 of them are "special" (they lie perfectly on the equators
                # and step face-by-face), while the other 18 orbits "scatter" or skip faces
                # because their translation displacement on off-equator tori does not match
                # the physical face-to-face adjacency distance.
                #
                # To construct all 20 mathematically perfect helices, we use the symmetry group:
                # 1. We use the screw motion to generate ONE perfect "equator" base helix.
                # 2. We use the rotational symmetry of the 600-cell (the 120 icosian vertices)
                #    to iteratively rotate this perfect base helix into the 19 other disjoint
                #    symmetric positions!

                from scipy.spatial import KDTree
                tree = KDTree(centers)

                # Step 1: Generate the perfect face-adjacent base helix (one of the 2 special equator helices)
                base_helix = []
                curr = centers[0]
                for _ in range(30):
                    _, idx = tree.query(curr)
                    base_helix.append(idx)
                    curr = q_mult(q_mult(L_quat, curr), R_quat)

                # Step 2: Use symmetry group (the 600-cell vertices themselves) to rotate the base helix
                helices_set = set()
                group = vertices

                for qL in group:
                    if len(chains) == 20: break
                    for qR in group:
                        if len(chains) == 20: break

                        # Rotate the perfect base helix into a new symmetry-invariant position
                        rotated_helix = []
                        for idx in base_helix:
                            mapped = q_mult(q_mult(qL, centers[idx]), qR)
                            _, m_idx = tree.query(mapped)
                            rotated_helix.append(m_idx)

                        canonical = tuple(sorted(rotated_helix))
                        if canonical not in helices_set:
                            # Verify disjointness: the true 20 helices must perfectly partition the cells with zero overlap
                            overlap = False
                            for h in chains:
                                if len(set(h).intersection(set(rotated_helix))) > 0:
                                    overlap = True
                                    break

                            if not overlap:
                                helices_set.add(canonical)
                                chains.append(rotated_helix)
            else:
                visited = set()
                for i in range(len(centers)):
                    if i in visited:
                        continue

                    chain = []
                    curr = centers[i]
                    # Walk the orbit until it closes back on itself
                    for _ in range(len(centers) + 1):
                        distances = np.linalg.norm(centers - curr, axis=1)
                        idx = np.argmin(distances)
                        if idx in visited:
                            break

                        chain.append(idx)
                        visited.add(idx)
                        curr = q_mult(q_mult(L_quat, curr), R_quat)

                    chains.append(chain)

            self.num_chains = len(chains)
            self.cell_chains = []
            self.cells = cells

            # Pre-fill with white in case some cells are not visited (e.g. truncated models)
            default_color = [1.0, 1.0, 1.0, self.blend]
            cell_colors = [default_color] * len(cells)
            for fiber_id, chain in enumerate(chains):
                self.cell_chains.append(chain)
                color_name = COLOR_SEQUENCE[fiber_id % len(COLOR_SEQUENCE)]
                color_val = COLOR_VALUES[color_name] + [self.blend]

                for idx in chain:
                    sorted_tuple = tuple(sorted(list(cells[idx])))
                    self.cell_fibers[sorted_tuple] = fiber_id
                    cell_colors[idx] = color_val
        else:
            light_yellow = [1.0, 1.0, 0.5, self.blend]
            cell_colors = [light_yellow] * len(cells)

        chain_tris = {k: [] for k in range(self.num_chains)}
        chain_norms = {k: [] for k in range(self.num_chains)}
        chain_colors = {k: [] for k in range(self.num_chains)}

        for i, cell_v_indices in enumerate(cells):
            cell_v_indices = list(cell_v_indices)
            sorted_tuple = tuple(sorted(cell_v_indices))
            fiber_id = self.cell_fibers.get(sorted_tuple, 0)

            cell_verts_4d = vertices[cell_v_indices]
            cell_center = np.mean(cell_verts_4d, axis=0)

            # Apply cell contraction: Shrink the 3D cell towards its own center point
            # to visually separate adjacent 3D cells in the final 4D projection.
            contracted_verts = []
            for v in cell_verts_4d:
                contracted_verts.append(cell_center + (v - cell_center) * self.cell_contraction)

            # Map global vertex index to local contracted vertex index
            v_to_local = {global_idx: local_idx for local_idx, global_idx in enumerate(cell_v_indices)}

            # -------------------------------------------------------------------------
            # 2. Discover True 2D Faces (Ridges)
            # -------------------------------------------------------------------------
            # In a 4D strictly convex polytope, a 3D cell (facet) is bounded by 2D polygons (ridges).
            # By mathematical definition, a 2D ridge is the exact intersection of exactly two
            # adjacent 3D cells.
            #
            # Because we extracted the true 3D cells by grouping coplanar tetrahedra (in step 1),
            # any two cells that share 3 or more vertices are physically adjacent and share a 2D face!
            # (If they only shared 1 vertex, it would be a point intersection. If 2 vertices, an edge).
            # Therefore, the intersection of their vertex sets immediately yields the complete
            # vertex set of their shared 2D polygonal face.
            faces = []
            for j, other_cell in enumerate(cells):
                if i == j:
                    continue
                common = set(cell_v_indices).intersection(set(other_cell))
                if len(common) >= 3:
                    faces.append(list(common))

            cell_start_idx = len(t_verts)
            t_verts.extend(contracted_verts)

            # -------------------------------------------------------------------------
            # 3. Triangulate 2D Faces
            # -------------------------------------------------------------------------
            for face_v_indices in faces:
                # Get contracted coordinates for this face
                face_coords = [contracted_verts[v_to_local[v]] for v in face_v_indices]
                face_center = np.mean(face_coords, axis=0)

                face_center_idx = len(t_verts)
                t_verts.append(face_center)

                # To triangulate an arbitrary 3D/4D convex polygon (e.g., a pentagon),
                # we must order its vertices angularly around its center.
                # We perform SVD (Singular Value Decomposition) on the centered vertices.
                # SVD identifies the principal components (directions of maximum variance).
                # Since the vertices are precisely coplanar, the first two principal components
                # (V[0] and V[1]) perfectly define the orthogonal 2D basis plane of the polygon.
                centered = np.array(face_coords) - face_center
                U, S, V = np.linalg.svd(centered, full_matrices=False)
                u_vec = V[0]
                v_vec = V[1]

                # Calculate the 2D angle of each vertex in this local coordinate system
                # and sort them to form a continuous loop around the polygon's perimeter.
                angles = np.arctan2(np.dot(centered, v_vec), np.dot(centered, u_vec))
                sort_order = np.argsort(angles)

                if len(sort_order) == 3:
                    # If the face is already a triangle (e.g., in the 600-cell or 24-cell),
                    # we do not need to subdivide it into 3 smaller triangles via the center.
                    v1_local_idx = v_to_local[face_v_indices[sort_order[0]]]
                    v2_local_idx = v_to_local[face_v_indices[sort_order[1]]]
                    v3_local_idx = v_to_local[face_v_indices[sort_order[2]]]

                    tri = (cell_start_idx + v1_local_idx, cell_start_idx + v2_local_idx, cell_start_idx + v3_local_idx)
                    t_tris.append(tri)
                    if self.num_chains > 0: chain_tris[fiber_id].append(tri)

                    normal = face_center - cell_center
                    norm_length = np.linalg.norm(normal)
                    if norm_length > 1e-6:
                        normal = normal / norm_length
                    else:
                        normal = np.array([0.0, 0.0, 0.0, 0.0])

                    t_norms.append(normal)
                    t_colors.append(cell_colors[i])
                    if self.num_chains > 0:
                        chain_norms[fiber_id].append(normal)
                        chain_colors[fiber_id].append(cell_colors[i])
                else:
                    # For complex polygons (e.g., pentagons in the 120-cell),
                    # create triangles by connecting the face center to each sequential edge.
                    for k in range(len(sort_order)):
                        v1_local_idx = v_to_local[face_v_indices[sort_order[k]]]
                        v2_local_idx = v_to_local[face_v_indices[sort_order[(k+1)%len(sort_order)]]]

                        tri = (face_center_idx, cell_start_idx + v1_local_idx, cell_start_idx + v2_local_idx)
                        t_tris.append(tri)
                        if self.num_chains > 0: chain_tris[fiber_id].append(tri)

                        # The outward normal of the 2D face in the context of its 3D cell
                        # points from the 3D cell's center directly through the 2D face's center.
                        normal = face_center - cell_center
                        norm_length = np.linalg.norm(normal)
                        if norm_length > 1e-6:
                            normal = normal / norm_length
                        else:
                            normal = np.array([0.0, 0.0, 0.0, 0.0])

                        t_norms.append(normal)
                        t_colors.append(cell_colors[i])
                        if self.num_chains > 0:
                            chain_norms[fiber_id].append(normal)
                            chain_colors[fiber_id].append(cell_colors[i])

        self.triangle_vertices_4d = np.array(t_verts, dtype=np.float32)
        self.triangles = t_tris
        self.triangle_normals_4d = np.array(t_norms, dtype=np.float32)
        self.triangle_colors = np.array(t_colors, dtype=np.float32)

        self.triangles_by_chain = []
        if self.num_chains > 0:
            for k in range(self.num_chains):
                self.triangles_by_chain.append((
                    chain_tris[k],
                    np.array(chain_norms[k], dtype=np.float32),
                    np.array(chain_colors[k], dtype=np.float32)
                ))

            self._compute_chain_groupings(centers, chains)
        else:
            self.chain_groupings = {"Single": []}
            self.chain_grouping_names = ["Single"]

    def _compute_chain_groupings(self, centers, chains):
        """Executes internal logic."""
        # -------------------------------------------------------------------------
        # Topological Fibration Grouping (SVD & Principal Angles)
        # -------------------------------------------------------------------------
        # The discrete fibers of the 24-cell, 120-cell, and 600-cell fibrations perfectly
        # map onto the vertices of Platonic solids (Octahedron, Icosahedron, Dodecahedron)
        # on the S^2 base space of the Hopf map.
        #
        # We can computationally extract these structures by finding the exact 2D invariant
        # plane of each fiber using Singular Value Decomposition (SVD):
        # https://en.wikipedia.org/wiki/Singular_value_decomposition
        #
        # By calculating the principal angles between these 2D planes, we mathematically
        # discover the concentric, interlocked "Clifford tori" (Toroidal Bundles) and
        # orthogonal polar opposites (Antipodal Pairs).
        # https://en.wikipedia.org/wiki/Clifford_torus

        # 1. Compute the 2D plane spanning each chain using SVD
        chain_planes = []
        for chain in chains:
            pts = []
            for idx in chain:
                c = centers[idx]
                pts.append(c / np.linalg.norm(c))
            pts = np.array(pts)
            U, S, Vh = np.linalg.svd(pts)
            chain_planes.append(Vh[:2])

        # 2. Find Antipodal Pairs (planes that are perfectly orthogonal, 90 degrees)
        antipodal_pairs = []
        matched = set()
        for i in range(len(chains)):
            if i in matched: continue
            best_orthogonality = 1.0
            best_match = -1

            for j in range(len(chains)):
                if i == j: continue
                # Dot product matrix between basis vectors of the two planes
                dot_matrix = chain_planes[i] @ chain_planes[j].T
                orthogonality = np.linalg.norm(dot_matrix, ord=2)

                if orthogonality < best_orthogonality:
                    best_orthogonality = orthogonality
                    best_match = j

            # A perfect orthogonal pair will have orthogonality < 1e-5
            if best_orthogonality < 1e-2:
                antipodal_pairs.append([i, best_match])
                matched.add(i)
                matched.add(best_match)

        # 3. Find Toroidal Bundles relative to Chain 0 (North Pole)
        pole_plane = chain_planes[0]
        distances = []
        for i in range(len(chain_planes)):
            dot_matrix = pole_plane @ chain_planes[i].T
            U, S, Vh = np.linalg.svd(dot_matrix)
            angle = np.arccos(np.clip(S[0], -1.0, 1.0)) * 180 / np.pi
            distances.append((i, angle))

        distances.sort(key=lambda x: x[1])

        current_angle = -1
        bundle = []
        bundles = []
        for i, angle in distances:
            if abs(angle - current_angle) > 1.0:
                if bundle:
                    bundles.append(bundle)
                bundle = []
                current_angle = angle
            bundle.append(i)
        if bundle:
            bundles.append(bundle)

        self.chain_groupings = {
            "Single": [[i] for i in range(len(chains))],
            "Antipodal Pairs": antipodal_pairs,
            "Toroidal Bundles": bundles
        }
        self.chain_grouping_names = ["Single", "Antipodal Pairs", "Toroidal Bundles"]

    def _compute_vertex_colors_bfs(self):
        """Executes internal logic."""
        color_map = {}
        if not hasattr(self, 'start_vertices') or not self.start_vertices:
            return color_map

        for v, depth in self.vertex_depths.items():
            color_map[v] = self.color_sequence[depth % len(self.color_sequence)]

        return color_map

    def _compute_vertex_colors_distance(self):
        """Executes internal logic."""
        color_map = {}
        for v, depth in self.distance_depths.items():
            color_map[v] = self.color_sequence[depth % len(self.color_sequence)]
        return color_map

    def _compute_vertex_colors_hopf(self):
        """Executes internal logic."""
        color_map = {}
        for v, depth in self.hopf_depths.items():
            color_map[v] = self.color_sequence[depth % len(self.color_sequence)]
        return color_map

    def _compute_edge_colors_bfs(self):
        """Executes internal logic."""
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
        """Executes internal logic."""
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
        """Executes internal logic."""
        color_map = {}
        from quaternion import order10, q_mult
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
        """Executes internal logic."""
        color_map = {}
        if not hasattr(self, 'start_vertices') or not self.start_vertices:
            return color_map

        vertex_classes = {}
        for v in range(len(self.base_vertices_4d)):
            if getattr(self, 'vertex_depths', None) is None or v not in self.vertex_depths:
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
