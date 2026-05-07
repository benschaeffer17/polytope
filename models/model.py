
import numpy as np
from viz.style import Style

class Model:
    def __init__(self, blend=1.0, cell_contraction=1.0, cell_coloring="default", hopf_generator=None):
        self.vertices_4d = None
        self.edges = None
        self.colors = None
        self.style = Style()
        self.edge_colors = None
        self.edge_width_multipliers = None
        self.blend = blend
        self.cell_contraction = cell_contraction
        self.cell_coloring = cell_coloring
        self.hopf_generator = hopf_generator
        self.cell_fibers = {}
        
        self.triangle_vertices_4d = None
        self.triangles = None
        self.triangle_normals_4d = None
        self.triangle_colors = None
        
    def _generate_triangles(self):
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
        # If hopf cell coloring is enabled, we map the center of each 3D cell
        # to S^2 using the Hopf map h(q) = q * V * q_conjugate. 
        # Cells that map to the same point on S^2 belong to the same fiber.
        cell_colors = []
        if self.cell_coloring == "hopf":
            from quaternion import q_mult, q_conjugate
            from .color_constants import COLOR_SEQUENCE, COLOR_VALUES
            
            # Use provided generator or fallback to `i` axis
            if self.hopf_generator is not None:
                gen = self.hopf_generator
                v_quat = np.array([0.0, gen[1], gen[2], gen[3]])
                norm = np.linalg.norm(v_quat)
                v_quat = v_quat / norm if norm > 1e-6 else np.array([0.0, 1.0, 0.0, 0.0])
            else:
                v_quat = np.array([0.0, 1.0, 0.0, 0.0])
                
            mapped_centers = []
            for cell_v_indices in cells:
                c = np.mean(vertices[list(cell_v_indices)], axis=0)
                c_norm = np.linalg.norm(c)
                c = c / c_norm if c_norm > 1e-6 else np.array([1.0, 0.0, 0.0, 0.0])
                mapped = q_mult(q_mult(c, v_quat), q_conjugate(c))[1:]
                mapped_centers.append(mapped)
                
            mapped_centers = np.array(mapped_centers)
            rounded = np.round(mapped_centers, 3)
            unique_pts, inverse = np.unique(rounded, axis=0, return_inverse=True)
            
            # Map each cell to its fiber ID and assign a color
            for i, fiber_id in enumerate(inverse):
                sorted_tuple = tuple(sorted(list(cells[i])))
                self.cell_fibers[sorted_tuple] = fiber_id
                
                color_name = COLOR_SEQUENCE[fiber_id % len(COLOR_SEQUENCE)]
                color_val = COLOR_VALUES[color_name] + [self.blend]
                cell_colors.append(color_val)
        else:
            light_yellow = [1.0, 1.0, 0.5, self.blend]
            cell_colors = [light_yellow] * len(cells)

        for i, cell_v_indices in enumerate(cells):
            cell_v_indices = list(cell_v_indices)
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
            # 2. Discover True 2D Faces
            # -------------------------------------------------------------------------
            # In a 4D strictly convex polytope, every 2D face (ridge) is the mathematical 
            # intersection of exactly two adjacent 3D cells (facets). By calculating the 
            # intersection of the vertex sets of adjacent 3D cells, any intersection 
            # containing 3 or more vertices mathematically forms a legitimate 2D polygon.
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
                    
                    t_tris.append((cell_start_idx + v1_local_idx, cell_start_idx + v2_local_idx, cell_start_idx + v3_local_idx))
                    
                    normal = face_center - cell_center
                    norm_length = np.linalg.norm(normal)
                    if norm_length > 1e-6:
                        normal = normal / norm_length
                    else:
                        normal = np.array([0.0, 0.0, 0.0, 0.0])
                        
                    t_norms.append(normal)
                    t_colors.append(cell_colors[i])
                else:
                    # For complex polygons (e.g., pentagons in the 120-cell),
                    # create triangles by connecting the face center to each sequential edge.
                    for k in range(len(sort_order)):
                        v1_local_idx = v_to_local[face_v_indices[sort_order[k]]]
                        v2_local_idx = v_to_local[face_v_indices[sort_order[(k+1)%len(sort_order)]]]
                        
                        t_tris.append((face_center_idx, cell_start_idx + v1_local_idx, cell_start_idx + v2_local_idx))
                        
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

        self.triangle_vertices_4d = np.array(t_verts, dtype=np.float32)
        self.triangles = t_tris
        self.triangle_normals_4d = np.array(t_norms, dtype=np.float32)
        self.triangle_colors = np.array(t_colors, dtype=np.float32)
