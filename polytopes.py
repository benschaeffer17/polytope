
import numpy as np
from itertools import permutations, combinations
from scipy.spatial import ConvexHull

def get_600_cell_vertices():
    """
    Returns the 120 vertices of a 600-cell.
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
                
    return np.array(list(vertices), dtype=np.float32)

def get_600_cell_cells(vertices=None):
    """
    Returns the cells (facets) of the 600-cell using a convex hull.
    """
    if vertices is None:
        vertices = get_600_cell_vertices()
    hull = ConvexHull(vertices)
    return hull.simplices

def project_4d_to_3d(vertices, rotation_matrix=None, d=2.0):
    """
    Projects 4D vertices to 3D after applying a rotation.
    """
    if rotation_matrix is None:
        rotation_matrix = np.identity(4)

    rotated_vertices = vertices @ rotation_matrix.T
    
    projected_vertices = []
    for v in rotated_vertices:
        w = v[3]
        # Stereographic projection
        # We can play with this later. For now, a simple perspective projection.
        # Let's assume the eye is at (0,0,0,d) and the projection hyperplane is w=0.
        # A point (x,y,z,w) is projected to d * (x,y,z) / (d-w)
        if d - w != 0:
            projected_vertices.append( (d * v[0:3]) / (d - w) )
        else:
            projected_vertices.append(v[0:3] * 1e9) # Avoid division by zero
            
    return np.array(projected_vertices, dtype=np.float32)
