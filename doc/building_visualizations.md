# Building Visualization Applications

This document explains the architectural principles of the Polytope Visualizer engine and demonstrates how developers can leverage its decoupled subsystems to build custom 4D rendering applications. 

Rather than tightly coupling mathematics, rendering, and state, the engine relies on strict separation of concerns. This design ensures that mathematical models remain pure, rendering loops remain blisteringly fast, and user interface state remains 100% testable.

## Core Architectural Subsystems (The "What" and the "Why")

The Polytope engine isolates its subsystems into specific layers. By keeping these boundaries strict, developers can write pure-Python unit tests for application state without initializing a heavyweight OpenGL context.

*   **`UserInterface` (Native Layer)**: Wraps the raw GLFW window and OpenGL context. It captures hardware input (mouse, keyboard) but contains no business logic.
*   **`UIStateManager` (Controller Layer)**: The heart of the application state. It acts as a central registry, translating raw native keystrokes into declarative `UIStateVariable` modifications. **Why decouple this?** By extracting state from the GLFW window, the application logic becomes fully headless. You can unit test a 4D rotation sequence in milliseconds.
*   **`Navigator` and `Rotator` (Kinematic Layer)**: Independent modules that manage the $SO(3)$ camera angles and $SO(4)$ hyper-rotations, entirely insulated from the geometry they manipulate.
*   **`Model` Geometries (Data Layer)**: The `models` directory houses the mathematical engines (e.g., `Cell120Model`). These classes encapsulate massive 4D vertex arrays and topological structures but remain blissfully unaware of how they are rendered or controlled.

## Constructing a Custom Visualizer

The following tutorial demonstrates how to orchestrate these decoupled layers into a functioning application.

### 1. Establish the Controller and Native Window

Begin by instantiating the core infrastructure. The `UIStateManager` requires a reference to the `UserInterface` so it can proxy the raw hardware events into its pure-Python state machine.

```python
import glfw
from widgets.ui import UserInterface
from widgets.state import UIStateManager, UIStateVariable
from navigation.navigator import Navigator
from models import Cell24Model
from widgets.capture import Capture

class App:
    def __init__(self):
        # 1. Initialize the native GLFW window wrapping
        self.ui = UserInterface(title="My Custom Visualizer")
        
        # 2. Initialize the Headless State Controller
        self.state = UIStateManager(self.ui)
        
        # 3. Attach Kinematics
        self.nav = Navigator(self.ui)
        
        # 4. Register the Main Render Loop
        self.ui.register_draw_function(self.draw)
```

### 2. Declarative State Registration (The Registry Pattern)

Instead of scattering `toggle_X()` methods across your application, register configuration variables directly into the `UIStateManager`. 

**Why use the Registry Pattern?** Defining state declaratively solves the "Triple Maintenance Problem." A single `register()` call automatically tracks the variable bounds, binds the hardware key, and dynamically injects the command into the interactive HUD Help Menu.

```python
        # Register an isolated state variable for face opacity
        self.state.register(UIStateVariable(
            name="blend", 
            values=[0.2, 0.4, 0.6, 0.8, 1.0], 
            keybind=glfw.KEY_Q, 
            key_name="Q", 
            description="Toggle face opacity (blend)", 
            default_index=4
        ))
        
        # Inject the state into the pure mathematical model
        self.model = Cell24Model(blend=self.state.get_variable("blend").get_value())
        self.capture = Capture(self.ui)
```

### 3. The Pure Render Loop

The `draw` method executes every frame. Because the state and math are decoupled, this loop remains highly optimized. You pull the current rotation, project the pure 4D data into 3D, and hand it to the stateless `drawing.py` backend.

```python
import viz.drawing as drawing
from polytopes import project_4d_to_3d

    def draw(self):
        # Apply 3D rotation from the Navigator
        self.nav.apply_rotation()
        
        # Project 4D vertices down to 3D space
        projected_vertices = project_4d_to_3d(self.model.vertices_4d, self.angle_4d)
        
        # Dispatch to the stateless OpenGL backend
        drawing.draw(projected_vertices, self.model.edges, self.model.colors, self.model.style)
        
        # Handle Topological Groupings (if SVD has extracted the Hopf fibers)
        if self.model.triangle_vertices_4d is not None and len(self.model.triangle_vertices_4d) > 0:
            projected_tris = project_4d_to_3d(self.model.triangle_vertices_4d, self.angle_4d)
            
            if hasattr(self.model, 'chain_groupings'):
                # Dynamically poll the UIStateManager for the active topological mode
                group_name = self.model.chain_grouping_names[self.state.get_variable("grouping_mode").get_value()]
                active_group = self.model.chain_groupings[group_name][self.state.get_variable("cell_chain").get_value() - 1]
                
                for chain_idx in active_group:
                    tris_to_draw, _, colors_to_draw = self.model.triangles_by_chain[chain_idx]
                    drawing.draw_triangles(projected_tris, tris_to_draw, colors_to_draw, normals=None)
            else:
                drawing.draw_triangles(projected_tris, self.model.triangles, self.model.triangle_colors, normals=None)
```

### 4. Application Execution

Initialize the OpenGL context settings, and surrender control to the `UserInterface` event loop.

```python
from OpenGL.GL import *

    def run(self):
        # Establish base OpenGL properties
        glEnable(GL_DEPTH_TEST)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        glOrtho(-2, 2, -2, 2, -10, 10)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        
        # Trigger the GLFW blocking loop
        self.ui.run()

if __name__ == '__main__':
    app = App()
    app.run()
```

## Architectural Summary

By pushing side effects (window generation, hardware polling) to the absolute edges of the architecture, the Polytope engine ensures that its core—the mathematical extraction of the Hopf fibration—remains stable, testable, and deeply extensible.
