
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

def get_120_cell():
    """
    Returns the vertices and edges of a 120-cell.
    """
    phi = (1 + np.sqrt(5)) / 2
    
    vertices = set()

    # Generate vertices
    base_coords = [
        (2, 2, 0, 0),
        (np.sqrt(5), 1, 1, 1),
        (phi, phi, phi, 1/phi**2),
        (phi**2, 1/phi, 1/phi, 1/phi)
    ]

    for coords in base_coords:
        for p in set(permutations(coords)):
            for i in range(16): # signs
                v = list(p)
                if (i >> 0) & 1: v[0] *= -1
                if (i >> 1) & 1: v[1] *= -1
                if (i >> 2) & 1: v[2] *= -1
                if (i >> 3) & 1: v[3] *= -1
                vertices.add(tuple(v))
    
    vertices = np.array(list(vertices), dtype=np.float32)

    # Generate edges
    edges = []
    edge_length_sq = (3 - np.sqrt(5))**2
    for i, j in combinations(range(len(vertices)), 2):
        v1 = vertices[i]
        v2 = vertices[j]
        dist_sq = np.sum((v1 - v2)**2)
        if np.isclose(dist_sq, edge_length_sq, atol=1e-3):
            edges.append((i, j))
            
    return vertices, edges

def get_600_cell():
    """
    Returns the vertices and edges of a 600-cell.
    The vertices are the 120 elements of the binary icosahedral group.
    """
    phi = (1 + np.sqrt(5)) / 2
    vertices = set()

    # 8 vertices of the form (±1, 0, 0, 0)
    for p in set(permutations([1, 0, 0, 0])):
        v = list(p)
        vertices.add(tuple(v))
        v[0] *= -1
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
        if np.isclose(dist_sq, edge_length_sq, atol=1e-3):
            edges.append((i, j))

    return vertices, edges

def project_4d_to_3d(vertices, rotation_matrix=None):
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
