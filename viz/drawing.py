
from OpenGL.GL import *
from OpenGL.GLU import *
import numpy as np
from .style import PointStyle, LineStyle

# Create a reusable quadric object
quad = gluNewQuadric()

def draw_cylinder(p1, p2, radius, slices=16):
    v = p2 - p1
    mag = np.linalg.norm(v)
    if mag < 1e-6:
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
    
    if np.linalg.norm(rot_axis) > 1e-6:
        glRotatef(angle, rot_axis[0], rot_axis[1], rot_axis[2])
    
    gluCylinder(quad, radius, radius, mag, slices, 1)
    glPopMatrix()


def draw(vertices, edges, colors, style, volume_dimension=4.0):
    if style.point_style.style == PointStyle.SPHERE or style.line_style.style == LineStyle.CYLINDER:
        glEnable(GL_LIGHTING)
    else:
        glDisable(GL_LIGHTING)

    # Draw points
    if style.point_style.style == PointStyle.POINT:
        glPointSize(style.point_style.size)
        glBegin(GL_POINTS)
        for i, vertex in enumerate(vertices):
            glColor3fv(colors[i])
            glVertex3fv(vertex)
        glEnd()
    elif style.point_style.style == PointStyle.SPHERE:
        radius = style.point_style.relative_size * volume_dimension / 20.0
        for i, vertex in enumerate(vertices):
            glPushMatrix()
            glTranslatef(vertex[0], vertex[1], vertex[2])
            glColor3fv(colors[i])
            gluSphere(quad, radius, 16, 16)
            glPopMatrix()

    # Draw lines
    if style.line_style.style == LineStyle.LINE:
        glLineWidth(style.line_style.width)
        glBegin(GL_LINES)
        for i, edge in enumerate(edges):
            p1_index, p2_index = edge
            glColor3fv(colors[p1_index])
            glVertex3fv(vertices[p1_index])
            glColor3fv(colors[p2_index])
            glVertex3fv(vertices[p2_index])
        glEnd()
    elif style.line_style.style == LineStyle.CYLINDER:
        radius = style.line_style.relative_width * volume_dimension / 20.0
        for edge in edges:
            p1 = vertices[edge[0]]
            p2 = vertices[edge[1]]
            # Use the color of the first vertex for the cylinder
            glColor3fv(colors[edge[0]])
            draw_cylinder(p1, p2, radius)
