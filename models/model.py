
from viz.style import Style

class Model:
    def __init__(self, blend=1.0):
        self.vertices_4d = None
        self.edges = None
        self.colors = None
        self.style = Style()
        self.edge_colors = None
        self.edge_width_multipliers = None
        self.blend = blend
