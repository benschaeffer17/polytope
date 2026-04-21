
import numpy as np

class Rotator:
    def __init__(self):
        self.modes = [
            [(0, 1, 1.0)],                      # 1: xy
            [(0, 3, 1.0)],                      # 2: xw
            [(0, 1, 1.0), (2, 3, 1.0)],         # 3: xy+zw
            [(0, 1, 1.0), (2, 3, -1.0)],        # 4: xy-zw
            [(0, 1, 1.0), (2, 3, 2.0)],         # 5: xy+2zw
            [(0, 1, 1.0), (2, 3, -2.0)]         # 6: xy-2zw
        ]
        self.mode_names = ["xy", "xw", "xy+zw", "xy-zw", "xy+2zw", "xy-2zw"]

    def get_rotation_matrix(self, mode_index, angle):
        if mode_index < 0 or mode_index >= len(self.modes):
            raise ValueError("Invalid mode index")

        R = np.identity(4)
        for i, j, speed in self.modes[mode_index]:
            c, s = np.cos(angle * speed), np.sin(angle * speed)
            
            R_part = np.identity(4)
            R_part[i, i] = c
            R_part[i, j] = -s
            R_part[j, i] = s
            R_part[j, j] = c
            
            R = R @ R_part
            
        return R

    def get_plane_name(self, mode_index):
        if mode_index < 0 or mode_index >= len(self.modes):
            raise ValueError("Invalid mode index")
        return self.mode_names[mode_index]
