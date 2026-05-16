# A dictionary of test configurations for visual regression testing.
# We test about 10-12 configurations per model, covering different planes, slicing, and topological states.

CONFIGS = {
    # ---------------- 600-Cell Tests ----------------
    "600_cell_wireframe_xy_45deg": {
        "shape_name": "600-cell", "angle_4d": 45.0, "rotation_plane": 0, "draw_triangles": False
    },
    "600_cell_toroidal_bundles": {
        "shape_name": "600-cell", "angle_4d": 0.0, "rotation_plane": 1, "draw_triangles": True,
        "chain_grouping_mode": 2, "cell_chain": 2
    },
    "600_cell_antipodal_pairs": {
        "shape_name": "600-cell", "angle_4d": 15.0, "rotation_plane": 2, "draw_triangles": True,
        "chain_grouping_mode": 1, "cell_chain": 1
    },
    "600_cell_single_chain": {
        "shape_name": "600-cell", "angle_4d": 30.0, "rotation_plane": 3, "draw_triangles": True,
        "chain_grouping_mode": 0, "cell_chain": 5
    },
    "600_cell_vertex_partition_slice": {
        "shape_name": "600-cell", "angle_4d": 0.0, "rotation_plane": 4, "draw_triangles": False,
        "vertex_mode_index": 0, "slice_mode_index": 1
    },
    "600_cell_edge_hopf_blend": {
        "shape_name": "600-cell", "angle_4d": 75.0, "rotation_plane": 5, "draw_triangles": True,
        "edge_mode_index": 2, "blend_index": 5
    },
    "600_cell_contracted_cells": {
        "shape_name": "600-cell", "angle_4d": 10.0, "rotation_plane": 0, "draw_triangles": True,
        "cell_contraction_index": 4, "cell_chain": 1
    },
    "600_cell_perspective_shift": {
        "shape_name": "600-cell", "angle_4d": 20.0, "rotation_plane": 1, "draw_triangles": False,
        "d_index": 7 # High perspective
    },
    "600_cell_points_filtering": {
        "shape_name": "600-cell", "angle_4d": 90.0, "rotation_plane": 2, "draw_triangles": False,
        "points_mode_index": 2
    },
    "600_cell_point_set_dfs": {
        "shape_name": "600-cell", "angle_4d": 45.0, "rotation_plane": 3, "draw_triangles": True,
        "point_set_index": 0
    },

    # ---------------- 120-Cell Tests ----------------
    "120_cell_wireframe_xz": {
        "shape_name": "120-cell", "angle_4d": 30.0, "rotation_plane": 1, "draw_triangles": False
    },
    "120_cell_solid_yw": {
        "shape_name": "120-cell", "angle_4d": 60.0, "rotation_plane": 4, "draw_triangles": True
    },
    "120_cell_vertex_bfs_slice_exact": {
        "shape_name": "120-cell", "angle_4d": 45.0, "rotation_plane": 2, "draw_triangles": False,
        "vertex_mode_index": 1, "slice_mode_index": 1
    },
    "120_cell_edge_icosi_blend": {
        "shape_name": "120-cell", "angle_4d": 15.0, "rotation_plane": 5, "draw_triangles": True,
        "edge_mode_index": 1, "blend_index": 4
    },
    "120_cell_contracted_cells": {
        "shape_name": "120-cell", "angle_4d": 25.0, "rotation_plane": 0, "draw_triangles": True,
        "cell_contraction_index": 2
    },
    "120_cell_perspective_shift": {
        "shape_name": "120-cell", "angle_4d": 70.0, "rotation_plane": 3, "draw_triangles": False,
        "d_index": 6
    },
    "120_cell_points_filtering": {
        "shape_name": "120-cell", "angle_4d": 90.0, "rotation_plane": 1, "draw_triangles": False,
        "points_mode_index": 8
    },
    "120_cell_point_set_distance": {
        "shape_name": "120-cell", "angle_4d": 10.0, "rotation_plane": 2, "draw_triangles": True,
        "point_set_index": 1
    },
    "120_cell_slice_echo": {
        "shape_name": "120-cell", "angle_4d": 33.0, "rotation_plane": 0, "draw_triangles": False,
        "slice_mode_index": 3
    },
    "120_cell_edge_zome": {
        "shape_name": "120-cell", "angle_4d": 88.0, "rotation_plane": 4, "draw_triangles": True,
        "edge_mode_index": 3
    },

    # ---------------- 24-Cell Tests ----------------
    "24_cell_solid_xy": {
        "shape_name": "24-cell", "angle_4d": 45.0, "rotation_plane": 0, "draw_triangles": True
    },
    "24_cell_wireframe_xz": {
        "shape_name": "24-cell", "angle_4d": 15.0, "rotation_plane": 1, "draw_triangles": False
    },
    "24_cell_solid_xw": {
        "shape_name": "24-cell", "angle_4d": 30.0, "rotation_plane": 2, "draw_triangles": True
    },
    "24_cell_wireframe_yz": {
        "shape_name": "24-cell", "angle_4d": 60.0, "rotation_plane": 3, "draw_triangles": False
    },
    "24_cell_solid_yw": {
        "shape_name": "24-cell", "angle_4d": 75.0, "rotation_plane": 4, "draw_triangles": True
    },
    "24_cell_wireframe_zw": {
        "shape_name": "24-cell", "angle_4d": 90.0, "rotation_plane": 5, "draw_triangles": False
    },
    "24_cell_contracted_solid": {
        "shape_name": "24-cell", "angle_4d": 20.0, "rotation_plane": 0, "draw_triangles": True,
        "cell_contraction_index": 5
    },
    "24_cell_blend_transparent": {
        "shape_name": "24-cell", "angle_4d": 40.0, "rotation_plane": 1, "draw_triangles": True,
        "blend_index": 2
    },
    "24_cell_perspective": {
        "shape_name": "24-cell", "angle_4d": 10.0, "rotation_plane": 2, "draw_triangles": False,
        "d_index": 8
    },
    "24_cell_default": {
        "shape_name": "24-cell", "angle_4d": 0.0, "rotation_plane": 0, "draw_triangles": False
    }
}
