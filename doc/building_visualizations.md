# Building Visualization Applications

This document describes how to use the classes and functions in this project to build your own polytope visualization applications. The `main.py` file serves as a good example of how to do this.

## Core Components

The visualization system is built around a few core components:

*   **`UserInterface`**: Creates the window and handles user input.
*   **`Navigator`**: Handles 3D rotation of the scene with the mouse.
*   **`Rotator`**: Handles 4D rotation of the polytope.
*   **`Model` Classes**: The `models` directory contains classes that represent the polytopes. These classes encapsulate the 4D vertex and edge data, as well as the coloring and styling information.
*   **Projection**: The `project_4d_to_3d` function projects the 4D data into 3D space that can be rendered.
*   **Drawing**: The `draw` function in `viz.drawing` handles the actual OpenGL rendering of the points and lines.
*   **Widgets**: The `widgets` directory contains additional components that can be added to the visualization, such as a frame capture tool and a heads-up display.

## Steps to Build a Visualization

Here is a step-by-step guide to creating a visualization application.

### 1. Create an Application Class

Create a main class to hold your application's state and logic.

```python
class App:
    def __init__(self):
        # ... initialization ...

    def draw(self):
        # ... rendering ...

    def run(self):
        # ... main loop ...
```

### 2. Initialize Core Components

In the `__init__` method of your `App` class, you should:

*   Create an instance of `UserInterface`.
*   Create an instance of `Navigator`, passing it the `UserInterface` instance.
*   Register your `draw` method with the `UserInterface` instance.
*   Create an instance of a `Model` subclass (e.g., `Cell24Model`).
*   Initialize any desired widgets, such as the `Capture` widget.

```python
from widgets.ui import UserInterface
from navigation.navigator import Navigator
from models import Cell24Model
from widgets.capture import Capture

class App:
    def __init__(self):
        self.ui = UserInterface(title="My Visualizer")
        self.nav = Navigator(self.ui)
        self.ui.register_draw_function(self.draw)
        
        self.model = Cell24Model()
        self.capture = Capture(self.ui)
```

### 3. Implement the `draw` method

The `draw` method is where all the rendering happens. It will be called on every frame. In this method, you should:

*   Apply the rotation from the `Navigator`.
*   Project your 4D vertices into 3D space.
*   Call the `drawing.draw` function to render the polytope.

```python
import viz.drawing as drawing
from polytopes import project_4d_to_3d

# ... inside the App class ...
    def draw(self):
        # Apply 3D rotation from mouse
        self.nav.apply_rotation()
        
        # Get projected 3D vertices
        projected_vertices = project_4d_to_3d(self.model.vertices_4d, self.angle_4d)
        
        # Draw the polytope
        drawing.draw(projected_vertices, self.model.edges, self.model.colors, self.model.style)
```

### 4. Implement the `run` method

The `run` method should perform any initial OpenGL setup and then start the main loop by calling the `run` method of your `UserInterface` instance.

```python
from OpenGL.GL import *

# ... inside the App class ...
    def run(self):
        # Initial OpenGL setup
        glEnable(GL_DEPTH_TEST)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        glOrtho(-2, 2, -2, 2, -10, 10)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        
        self.ui.run()
```

### 5. Run the Application

Finally, create an instance of your `App` class and call its `run` method.

```python
if __name__ == '__main__':
    app = App()
    app.run()
```

## Customization

You can customize the appearance of the visualization by modifying the `Style` object on the `model`. For example, you can register a keyboard callback to toggle the drawing style:

```python
# In __init__
self.ui.register_keyboard_callback(glfw.KEY_V, self.toggle_style)

# A new method in your App class
def toggle_style(self, *args):
    self.model.style.toggle_style()
```
Now, pressing the 'V' key will switch between simple points and lines, and lit spheres and cylinders. You can also use widgets to add functionality. For example, the `Capture` widget saves a screenshot when a key is pressed.
