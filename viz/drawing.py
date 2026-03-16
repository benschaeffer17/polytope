
from OpenGL.GL import *
from OpenGL.GLU import *
import numpy as np
from .style import PointStyle, LineStyle

# Create a reusable quadric object
quad = gluNewQuadric()

def draw_cylinder(p1, p2, radius, slices=16):
    v = p2 - p1
    mag = np.linalg.norm(v)
    if mag < 1e-9: # A very small constant
        return

    v = v / mag
    
    # The axis of the cylinder
    axis = np.array([0.0, 0.0, 1.0])
    
    # The rotation axis is the cross product of the cylinder axis and the vector v
    rot_axis = np.cross(axis, v)
    
    # The angle of rotation
    dot_product = np.dot(axis, v)
    angle = np.rad2deg(np.arccos(dot_product))

    glPushMatrix()
    glTranslatef(p1[0], p1[1], p1[2])
    
    # If the vector is anti-parallel to the axis, the cross product is zero.
    # In this case, we need to choose an arbitrary rotation axis.
    if dot_product < -0.99999:
        glRotatef(180, 1.0, 0.0, 0.0) # Rotate 180 degrees around x-axis
    elif np.linalg.norm(rot_axis) > 1e-6:
        glRotatef(angle, rot_axis[0], rot_axis[1], rot_axis[2])
    
    gluCylinder(quad, radius, radius, mag, slices, 1)
    glPopMatrix()


def get_color_scale(color):
    r, g, b = color
    if r > 0.9 and g < 0.1 and b < 0.1: # Red
        return 1.2
    elif r < 0.1 and g > 0.9 and b < 0.1: # Green
        return 1.15
    elif r < 0.1 and g < 0.1 and b > 0.9: # Blue
        return 1.1
    elif r > 0.9 and g > 0.9 and b < 0.1: # Yellow
        return 1.05
    elif r > 0.9 and g < 0.1 and b > 0.9: # Purple
        return 1.0
    return 1.0

def draw(vertices, edges, colors, style, volume_dimension=4.0, fixed_vertices_indices=None, edge_colors=None):
    if fixed_vertices_indices is None:
        fixed_vertices_indices = set()

    if style.point_style.style == PointStyle.SPHERE or style.line_style.style == LineStyle.CYLINDER:
        glEnable(GL_LIGHTING)
    else:
        glDisable(GL_LIGHTING)

    # Draw points
    if style.point_style.style == PointStyle.POINT:
        # Non-fixed points
        glPointSize(style.point_style.size)
        glBegin(GL_POINTS)
        for i, vertex in enumerate(vertices):
            if i not in fixed_vertices_indices:
                glColor3fv(colors[i])
                glVertex3fv(vertex)
        glEnd()
        # Fixed points
        glPointSize(style.point_style.size * 3)
        glBegin(GL_POINTS)
        for i in fixed_vertices_indices:
            glColor3fv(colors[i])
            glVertex3fv(vertices[i])
        glEnd()

    elif style.point_style.style == PointStyle.SPHERE:
        default_radius = style.point_style.relative_size * volume_dimension / 20.0
        for i, vertex in enumerate(vertices):
            glPushMatrix()
            glTranslatef(vertex[0], vertex[1], vertex[2])

            if i in fixed_vertices_indices:
                radius = default_radius * 3
                color = colors[i]
            else:
                radius = default_radius
                color = colors[i]

            glColor3fv(color)
            gluSphere(quad, radius, 16, 16)
            glPopMatrix()

    # Draw lines
    if style.line_style.style == LineStyle.LINE:
        for i, edge in enumerate(edges):
            p1_index, p2_index = edge
            if edge_colors is not None:
                color = edge_colors[i]
                scale = get_color_scale(color)
                glLineWidth(style.line_style.width * scale)
                glBegin(GL_LINES)
                glColor3fv(color)
                glVertex3fv(vertices[p1_index])
                glVertex3fv(vertices[p2_index])
                glEnd()
            else:
                scale = get_color_scale(colors[p1_index])
                glLineWidth(style.line_style.width * scale)
                glBegin(GL_LINES)
                glColor3fv(colors[p1_index])
                glVertex3fv(vertices[p1_index])
                glColor3fv(colors[p2_index])
                glVertex3fv(vertices[p2_index])
                glEnd()
    elif style.line_style.style == LineStyle.CYLINDER:
        radius = style.line_style.relative_width * volume_dimension / 20.0
        for i, edge in enumerate(edges):
            p1 = vertices[edge[0]]
            p2 = vertices[edge[1]]
            if edge_colors is not None:
                color = edge_colors[i]
            else:
                color = colors[edge[0]]
            scale = get_color_scale(color)
            glColor3fv(color)
            draw_cylinder(p1, p2, radius * scale)
