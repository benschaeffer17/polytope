
import numpy as np
from itertools import permutations, combinations

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
