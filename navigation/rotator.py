
import numpy as np

class Rotator:
    def __init__(self):
        self.planes = [
            (0, 1), # xy
            (0, 2), # xz
            (0, 3), # xw
            (1, 2), # yz
            (1, 3), # yw
            (2, 3)  # zw
        ]
        self.plane_names = ["xy", "xz", "xw", "yz", "yw", "zw"]

    def get_rotation_matrix(self, plane_index, angle):
        if plane_index < 0 or plane_index >= len(self.planes):
            raise ValueError("Invalid plane index")

        i, j = self.planes[plane_index]
        
        c, s = np.cos(angle), np.sin(angle)
        
        R = np.identity(4)
        R[i, i] = c
        R[i, j] = -s
        R[j, i] = s
        R[j, j] = c
        
        return R

    def get_plane_name(self, plane_index):
        if plane_index < 0 or plane_index >= len(self.planes):
            raise ValueError("Invalid plane index")
        return self.plane_names[plane_index]
