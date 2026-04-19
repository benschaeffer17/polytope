import numpy as np

COLOR_VALUES = {
    "RED": [1.0, 0.0, 0.0],
    "BLUE": [0.0, 0.0, 1.0],
    "GREEN": [0.0, 1.0, 0.0],
    "YELLOW": [1.0, 1.0, 0.0],
    "PURPLE": [1.0, 0.0, 1.0],
    "CYAN": [0.0, 1.0, 1.0],
    "WHITE": [1.0, 1.0, 1.0],
    "BLACK": [0.0, 0.0, 0.0],
    "ORANGE": [1.0, 0.5, 0.0],
    "PINK": [1.0, 0.75, 0.8],
    "LIME": [0.75, 1.0, 0.0],
    "ROSE": [1.0, 0.0, 0.5]
}

COLOR_SEQUENCE = ["RED", "CYAN", "LIME", "PURPLE", "YELLOW", "BLUE", "ORANGE", "GREEN", "ROSE"]

COLOR_WIDTH_MULTIPLIERS = {}
for i, color_name in enumerate(COLOR_SEQUENCE):
    multiplier = 0.9 + i * (1.1 - 0.9) / max(1, len(COLOR_SEQUENCE) - 1)
    COLOR_WIDTH_MULTIPLIERS[color_name] = multiplier

def get_scaling_multiplier_by_color(color_rgb):
    """
    Takes a 3d color vector (or 4d vector with alpha) and returns a multiplier.
    Returns 1.0 if the color is not 'close' to one of the sequence colors.
    """
    color_rgb = np.array(color_rgb)[:3]
    for color_name in COLOR_SEQUENCE:
        rgb = np.array(COLOR_VALUES[color_name])
        if np.allclose(color_rgb, rgb, atol=1e-3):
            return COLOR_WIDTH_MULTIPLIERS[color_name]
    return 1.0

