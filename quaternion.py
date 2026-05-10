
import numpy as np

# phi is the golden ratio, foundational to the icosahedral symmetry of the 600-cell and 120-cell
phi = (1 + np.sqrt(5)) / 2

# order6 is a quaternion of order 6 in the binary icosahedral group (order 3 in SO(4)).
# It represents a 120-degree rotation.
order6 = np.array([0.5, 0.5, 0.5, 0.5])

# order10 is a quaternion of order 10 in the binary icosahedral group (order 5 in SO(4)).
# It represents a 72-degree rotation, forming the foundational cycle of the 120-cell's dodecahedra rings.
order10 = np.array([phi / 2, 0.5, 1 / (2*phi), 0])

q_identity = np.array([1.0, 0.0, 0.0, 0.0])

# -------------------------------------------------------------------------
# Boerdijk-Coxeter Helix Generators (600-cell Hopf Fibration)
# -------------------------------------------------------------------------
# To generate a perfectly face-adjacent chain of 30 tetrahedra (a Boerdijk-Coxeter helix) 
# within the 600-cell, we use a specific 4D screw motion: c -> L * c * R.
# 
# hopf_600_L is an order-10 quaternion. It provides the "long" twist around the great circle.
hopf_600_L = np.array([(1/phi) / 2, 0.5, 0.0, -phi / 2])

# hopf_600_R is an order-6 quaternion. It provides the localized "corkscrew" twisting 
# that forces the path to cleanly enter and exit the alternating tetrahedral faces.
hopf_600_R = np.array([0.5, -0.5, 0.5, 0.5])

# hopf_24_R is the quaternion `i` (order 4). It generates the 4-cell rings of the 24-cell fibration.
hopf_24_R = np.array([0.0, 1.0, 0.0, 0.0])

def q_mult(q1, q2):
    """
    Multiplies two quaternions.
    """
    w1, x1, y1, z1 = q1
    w2, x2, y2, z2 = q2
    w = w1 * w2 - x1 * x2 - y1 * y2 - z1 * z2
    x = w1 * x2 + x1 * w2 + y1 * z2 - z1 * y2
    y = w1 * y2 - x1 * z2 + y1 * w2 + z1 * x2
    z = w1 * z2 + x1 * y2 - y1 * x2 + z1 * w2
    return np.array([w, x, y, z])

def q_conjugate(q):
    """
    Returns the conjugate of a quaternion.
    """
    w, x, y, z = q
    return np.array([w, -x, -y, -z])

def qv_mult(q, v):
    """
    Multiplies a quaternion by a vector.
    """
    q2 = np.array([0, v[0], v[1], v[2]])
    return q_mult(q_mult(q, q2), q_conjugate(q))[1:]
