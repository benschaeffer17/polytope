
import numpy as np

phi = (1 + np.sqrt(5)) / 2
order6 = np.array([0.5, 0.5, 0.5, 0.5])
order10 = np.array([phi / 2, 0.5, 1 / (2*phi), 0])

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
