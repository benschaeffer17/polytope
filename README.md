# 4D Polytope Topological Visualizer

This project is an advanced, high-performance visualizer for 4D polytopes (24-cell, 120-cell, and 600-cell) using Python, OpenGL, and GLFW. It is uniquely designed to mathematically extract and visualize the discrete [Hopf Fibration](https://en.wikipedia.org/wiki/Hopf_fibration), rendering the spectacular intertwined geometries of 4D space down to 3D.

## Architecture Documentation Gateway
For an in-depth understanding of the engine's structure and how to build upon it, please consult the core documentation:
- **[Class Hierarchy](doc/class_hierarchy.md)**: A complete UML breakdown of the `UIStateManager`, `Model` geometries, and `viz` pipelines.
- **[Building Visualizations](doc/building_visualizations.md)**: A guide to constructing new 4D polytope visualizer apps using the decoupled engine components.

## The Mathematics of the 4D Hopf Fibration

In topology, the continuous Hopf fibration describes how the 3-sphere ($S^3$) can be perfectly partitioned into a bundle of non-intersecting great circles (fibers) that map onto a 2-sphere ($S^2$). Because the regular 4-polytopes tile the surface of the 3-sphere, their discrete cells can be linked together into physical "chains" that represent a rigid, discrete analog of the continuous Hopf fibration.

### Discrete Fiber Bundles
This visualizer dynamically discovers these fibers by orchestrating [Clifford translations](https://en.wikipedia.org/wiki/Clifford_translation) (isoclinic rotations). By applying a specific order-10 and order-6 quaternion screw motion ($v \mapsto L \cdot v \cdot R$), the visualizer perfectly segments the cells:
- **24-Cell**: Partitions into 6 distinct chains of 4 octahedra.
- **120-Cell**: Partitions into 12 distinct chains of 10 dodecahedra.
- **600-Cell**: Partitions into 20 disjoint, mathematically perfect [Boerdijk-Coxeter helices](https://en.wikipedia.org/wiki/Boerdijk%E2%80%93Coxeter_helix) (each consisting of 30 face-adjacent tetrahedra)!

### Topological Structure (SVD Groupings)
The discrete fibers of these polytopes perfectly map onto the vertices of Platonic solids (Octahedron, Icosahedron, Dodecahedron) on the $S^2$ base space. 

During geometry generation, the visualizer uses [Singular Value Decomposition (SVD)](https://en.wikipedia.org/wiki/Singular_value_decomposition) to mathematically extract the 2D invariant plane defining each fiber in $\mathbb{R}^4$. By calculating the principal angles between these planes, it automatically discovers the macroscopic structure of the fibration:
- **Toroidal Bundles**: The visualizer groups fibers by their isoclinic angles, revealing them as interlocked, concentric [Clifford tori](https://en.wikipedia.org/wiki/Clifford_torus).
- **Antipodal Pairs**: The visualizer perfectly pairs chains that are mathematically orthogonal ($90^{\circ}$ apart in 4D space), representing the opposite poles of the fibration map.

## Installation & Running

1. **Install dependencies:**
   You will need `numpy`, `PyOpenGL`, and `glfw`. 
   ```bash
   pip install -r requirements.txt
   ```
2. **Run the main script:**
   ```bash
   python main.py
   ```

## Advanced Visualization Features

- **Topological Isolation**: Render the massive structures as a whole, or isolate single Boerdijk-Coxeter helices to view their chiral twist.
- **Topological Grouping**: Toggle the grouping mode to instantly render orthogonal Antipodal Pairs or massive concentric Toroidal Bundles.
- **Dynamic Slicing & Truncation**: Recursively slice the vertices to reveal the hidden underlying core geometry, or shrink individual 3D cells to expose the inner structures.
- **Vertex & Edge Coloring**: Apply Depth-First Search (DFS) or distance-based algorithms to map the geometry via color spectrums.

## Interactive Controls

Press **`/`** at any time while the application is running to view the interactive Help Screen overlay.

| Key | Action |
|:---|:---|
| **Click & Drag** | Rotate the 3D camera projection |
| **P** | Pause/Resume the automatic 4D rotation |
| **< / >** | Cycle through the 4D rotation planes (XY, YZ, XZ, XW, YW, ZW) |
| **+ / -** | Increase or decrease the speed of the 4D rotation |
| **K / M** | Zoom the 3D camera Out / In |
| **8** | Toggle Vertex coloring mode |
| **9** | Toggle Edge coloring mode |
| **0** | Toggle Points mode (vertex truncation filtering) |
| **S** | Toggle Slice mode (spatial cutting planes) |
| **F** | Toggle Point Set (DFS generation mapping) |
| **Q** | Toggle Face Opacity (translucent blend) |
| **B** | Toggle drawing of solid 3D cell faces |
| **G** | Toggle 3D Cell Contraction (shrinks individual cells to reveal gaps) |
| **H** | Toggle Topological Grouping Mode (Single, Antipodal Pairs, Toroidal Bundles) |
| **N** | Cycle through the isolated fibers/groups in the active Topological mode |
| **/** | Toggle the interactive Help Screen overlay |
| **ESC** | Quit the visualizer |

## Project Architecture

- `main.py`: The main script that runs the application state and render loop.
- `models/model.py`: The heavy-lifting mathematical engine. It handles 3D cell triangulation, Hopf fiber generation, SVD plane extraction, and pre-segments OpenGL flat arrays for strict 60 FPS performance.
- `quaternion.py`: Foundational SO(4) rotation generators mapping the geometry.
- `viz/drawing.py`: OpenGL immediate-mode and array rendering backend.
- `widgets/ui.py`: Manages the GLFW window, HUD, and the event-interception overlay logic.
