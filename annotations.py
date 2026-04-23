class Annotation:
    """Holds position, style, and type data for a single drawn shape or text label."""

    def __init__(self, type, start, end, color=(1, 0, 0), width=2, text=""):
        self.type = type    # 'rect', 'arrow', 'text', 'ellipse', 'draw', 'highlight'
        self.start = start  # (x, y) origin
        self.end = end      # (x, y) opposite corner / endpoint
        self.color = color
        self.width = width
        self.text = text
        self.angle = 0      # rotation in radians
        self.points = []    # freehand path points for 'draw' type
        self.sx = 1.0       # user-applied horizontal scale
        self.sy = 1.0       # user-applied vertical scale
