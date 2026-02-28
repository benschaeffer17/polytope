
class PointStyle:
    # Point drawing styles
    POINT = 1
    SPHERE = 2

    def __init__(self, style=POINT, size=5.0, relative_size=0.1):
        self.style = style
        self.size = size # for POINT style
        self.relative_size = relative_size # for SPHERE style

class LineStyle:
    # Line drawing styles
    LINE = 1
    CYLINDER = 2

    def __init__(self, style=LINE, width=1.0, relative_width=0.05):
        self.style = style
        self.width = width # for LINE style
        self.relative_width = relative_width # for CYLINDER style

class Style:
    def __init__(self, point_style=None, line_style=None):
        self.point_style = point_style if point_style else PointStyle()
        self.line_style = line_style if line_style else LineStyle()

    def toggle_style(self):
        if self.point_style.style == PointStyle.POINT:
            self.point_style.style = PointStyle.SPHERE
            self.line_style.style = LineStyle.CYLINDER
        else:
            self.point_style.style = PointStyle.POINT
            self.line_style.style = LineStyle.LINE
