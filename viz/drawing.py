
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



def draw(vertices, edges, colors, style, volume_dimension=4.0, fixed_vertices_indices=None, edge_colors=None, edge_width_multipliers=None):
    if fixed_vertices_indices is None:
        fixed_vertices_indices = set()

    if style.point_style.style == PointStyle.SPHERE or style.line_style.style == LineStyle.CYLINDER:
        glEnable(GL_LIGHTING)
    else:
        glDisable(GL_LIGHTING)

    # Draw points
    if style.point_style.style == PointStyle.POINT:
        glEnable(GL_POINT_SMOOTH)
        
        # Non-fixed points
        glPointSize(style.point_style.size)
        glBegin(GL_POINTS)
        for i, vertex in enumerate(vertices):
            if i not in fixed_vertices_indices:
                glColor4fv(colors[i])
                glVertex3fv(vertex)
        glEnd()
        # Fixed points
        glPointSize(style.point_style.size * 3)
        glBegin(GL_POINTS)
        for i in fixed_vertices_indices:
            glColor4fv(colors[i])
            glVertex3fv(vertices[i])
        glEnd()
        
        glDisable(GL_POINT_SMOOTH)

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

            glColor4fv(color)
            gluSphere(quad, radius, 16, 16)
            glPopMatrix()

    # Draw lines
    if style.line_style.style == LineStyle.LINE:
        for i, edge in enumerate(edges):
            p1_index, p2_index = edge
            width = style.line_style.width
            if edge_width_multipliers is not None:
                width *= edge_width_multipliers[i]
            glLineWidth(width)

            if edge_colors is not None:
                color = edge_colors[i]
                glBegin(GL_LINES)
                glColor4fv(color)
                glVertex3fv(vertices[p1_index])
                glVertex3fv(vertices[p2_index])
                glEnd()
            else:
                glBegin(GL_LINES)
                glColor4fv(colors[p1_index])
                glVertex3fv(vertices[p1_index])
                glColor4fv(colors[p2_index])
                glVertex3fv(vertices[p2_index])
                glEnd()
    elif style.line_style.style == LineStyle.CYLINDER:
        base_radius = style.line_style.relative_width * volume_dimension / 20.0
        for i, edge in enumerate(edges):
            p1 = vertices[edge[0]]
            p2 = vertices[edge[1]]
            
            radius = base_radius
            if edge_width_multipliers is not None:
                radius *= edge_width_multipliers[i]

            if edge_colors is not None:
                color = edge_colors[i]
            else:
                color = colors[edge[0]]

            glColor4fv(color)
            draw_cylinder(p1, p2, radius)

def draw_triangles(vertices, triangles, colors, normals=None):
    """
    Draws lit triangles for the cell faces using extremely fast Vertex Arrays.
    """
    if len(triangles) == 0:
        return

    # Convert inputs to numpy arrays
    vertices = np.asarray(vertices, dtype=np.float32)
    triangles = np.asarray(triangles, dtype=np.int32)
    colors = np.asarray(colors, dtype=np.float32)

    # Extract the actual 3D vertices for every triangle
    # Shape becomes (num_triangles, 3 vertices, 3 coordinates)
    tri_verts = vertices[triangles]

    # Duplicate the per-triangle color for each of its 3 vertices
    # Shape becomes (num_triangles, 3 vertices, 4 color_channels)
    tri_colors = np.repeat(colors[:, np.newaxis, :], 3, axis=1)

    if normals is not None:
        normals = np.asarray(normals, dtype=np.float32)
        # Duplicate the per-triangle normal for each of its 3 vertices
        tri_normals = np.repeat(normals[:, np.newaxis, :], 3, axis=1)
    else:
        # Fallback if normals aren't provided (vectorized cross product per triangle)
        vec1 = tri_verts[:, 1, :] - tri_verts[:, 0, :]
        vec2 = tri_verts[:, 2, :] - tri_verts[:, 0, :]
        calc_normals = np.cross(vec1, vec2)
        norms = np.linalg.norm(calc_normals, axis=1, keepdims=True)
        calc_normals = np.divide(calc_normals, norms, out=np.zeros_like(calc_normals), where=norms>1e-6)
        tri_normals = np.repeat(calc_normals[:, np.newaxis, :], 3, axis=1)

    # Flatten to contiguous C-arrays for PyOpenGL
    tri_verts_flat = np.ascontiguousarray(tri_verts.reshape(-1, 3))
    tri_colors_flat = np.ascontiguousarray(tri_colors.reshape(-1, 4))
    tri_normals_flat = np.ascontiguousarray(tri_normals.reshape(-1, 3))

    glEnable(GL_LIGHTING)
    
    # Enable Client States
    glEnableClientState(GL_VERTEX_ARRAY)
    glEnableClientState(GL_NORMAL_ARRAY)
    glEnableClientState(GL_COLOR_ARRAY)

    # Pass the entire arrays to the graphics card
    glVertexPointer(3, GL_FLOAT, 0, tri_verts_flat)
    glNormalPointer(GL_FLOAT, 0, tri_normals_flat)
    glColorPointer(4, GL_FLOAT, 0, tri_colors_flat)

    # Draw all triangles in a single massive driver call!
    glDrawArrays(GL_TRIANGLES, 0, len(tri_verts_flat))

    # Disable Client States to leave OpenGL state clean
    glDisableClientState(GL_VERTEX_ARRAY)
    glDisableClientState(GL_NORMAL_ARRAY)
    glDisableClientState(GL_COLOR_ARRAY)

