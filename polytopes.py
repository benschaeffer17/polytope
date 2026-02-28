
import numpy as np
from itertools import permutations, combinations

def get_24_cell():
    """
    Returns the vertices and edges of a 24-cell.
    """
    vertices = set()
    for p in permutations([1, 1, 0, 0]):
        for i in range(1 << 2): # 2 is the number of non-zero elements
            signs = [(i >> j) & 1 for j in range(2)]
            v = list(p)
            k = 0
            for j in range(4):
                if v[j] != 0:
                    if signs[k] == 1:
                        v[j] *= -1
                    k += 1
            vertices.add(tuple(v))
    
    vertices = np.array(list(vertices), dtype=np.float32)

    edges = []
    for i, j in combinations(range(len(vertices)), 2):
        v1 = vertices[i]
        v2 = vertices[j]
        if np.linalg.norm(v1 - v2) < 1.5: # sqrt(2) is approx 1.414
            edges.append((i, j))
            
    return vertices, edges

def project_4d_to_3d(vertices, angle_4d=0):
    """
    Projects 4D vertices to 3D using a rotation in the xw plane.
    """
    
    # Rotation matrix for the 4th dimension
    rotation_matrix = np.array([
        [np.cos(angle_4d), 0, 0, -np.sin(angle_4d)],
        [0, 1, 0, 0],
        [0, 0, 1, 0],
        [np.sin(angle_4d), 0, 0, np.cos(angle_4d)]
    ])
    
    rotated_vertices = vertices @ rotation_matrix.T
    
    projected_vertices = []
    for v in rotated_vertices:
        w = v[3]
        # Stereographic projection
        # We can play with this later. For now, a simple perspective projection.
        # Let's assume the eye is at (0,0,0,d) and the projection hyperplane is w=0.
        # A point (x,y,z,w) is projected to d * (x,y,z) / (d-w)
        d = 2.0
        if d - w != 0:
            projected_vertices.append( (d * v[0:3]) / (d - w) )
        else:
            projected_vertices.append(v[0:3] * 1e9) # Avoid division by zero
            
    return np.array(projected_vertices, dtype=np.float32)

if __name__ == '__main__':
    vertices, edges = get_24_cell()
    print("Number of vertices:", len(vertices))
    print("Number of edges:", len(edges))
    
    projected_vertices = project_4d_to_3d(vertices)
    
    # print("Vertices:")
    # print(vertices)
    # print("\nEdges:")
    # print(edges)
    # print("\nProjected Vertices:")
    # print(projected_vertices)
