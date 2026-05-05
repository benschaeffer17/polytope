
import numpy as np
from viz.style import Style

class Model:
    def __init__(self, blend=1.0, cell_contraction=1.0):
        self.vertices_4d = None
        self.edges = None
        self.colors = None
        self.style = Style()
        self.edge_colors = None
        self.edge_width_multipliers = None
        self.blend = blend
        self.cell_contraction = cell_contraction
        
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
            hull = ConvexHull(vertices)
            cells = hull.simplices
        except:
            self.triangle_vertices_4d = np.array([], dtype=np.float32)
            self.triangles = []
            self.triangle_normals_4d = np.array([], dtype=np.float32)
            self.triangle_colors = np.array([], dtype=np.float32)
            return

        t_verts = []
        t_tris = []
        t_norms = []
        t_colors = []
        
        light_yellow = [1.0, 1.0, 0.5, self.blend]

        idx_offset = 0
        for cell in cells:
            cell_verts = vertices[cell]
            center = np.mean(cell_verts, axis=0)
            
            contracted_verts = []
            for v in cell_verts:
                contracted_verts.append(center + (v - center) * self.cell_contraction)
            
            t_verts.extend(contracted_verts)
            
            # Ensure compatible winding order for the faces
            faces = [(1, 2, 3), (0, 2, 1), (0, 1, 3), (0, 3, 2)]
            
            for face in faces:
                v0, v1, v2 = face
                t_tris.append((idx_offset + v0, idx_offset + v1, idx_offset + v2))
                
                face_center = (contracted_verts[v0] + contracted_verts[v1] + contracted_verts[v2]) / 3.0
                normal = face_center - center
                norm_length = np.linalg.norm(normal)
                if norm_length > 1e-6:
                    normal = normal / norm_length
                else:
                    normal = np.array([0.0, 0.0, 0.0, 0.0])
                    
                t_norms.append(normal)
                t_colors.append(light_yellow)
                
            idx_offset += 4
            
        self.triangle_vertices_4d = np.array(t_verts, dtype=np.float32)
        self.triangles = t_tris
        self.triangle_normals_4d = np.array(t_norms, dtype=np.float32)
        self.triangle_colors = np.array(t_colors, dtype=np.float32)
