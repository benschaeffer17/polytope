# Class Hierarchy

This document outlines the class hierarchy of the polytope visualization project.

## Core Classes

*   `main.App`: The main application class that orchestrates the entire visualization. It initializes and manages the UI, navigation, and the currently displayed polytope model.

*   `widgets.ui.UserInterface`: This class manages the application window, OpenGL context, and user input. It provides a run loop and allows registering callbacks for drawing and input events.

*   `navigation.navigator.Navigator`: This class handles 3D camera rotation based on mouse input.

*   `navigation.rotator.Rotator`: This class manages the 4D rotation of the polytope.

## Model Classes

These classes represent the polytopes themselves. They encapsulate the geometry (vertices, edges) and coloring information.

*   `models.model.Model`: The abstract base class for all polytope models. It defines the common interface for a model, including attributes for vertices, edges, colors, and style.

*   `models.cell_24_model.Cell24Model`: A concrete implementation of `Model` for the 24-cell polytope. It loads the geometry from `get_24_cell` and defines the specific coloring and style for this shape.

*   `models.cell_120_model.Cell120Model`: A concrete implementation of `Model` for the 120-cell polytope.

*   `models.cell_600_model.Cell600Model`: A concrete implementation of `Model` for the 600-cell polytope.

## Styling Classes

These classes are used to define the visual style of the rendered polytopes.

*   `viz.style.Style`: A container class that holds instances of `PointStyle` and `LineStyle`.

*   `viz.style.PointStyle`: Defines how vertices (points) of the polytope are rendered.

*   `viz.style.LineStyle`: Defines how the edges (lines) of the polytope are rendered.

## Widget Classes

*   `widgets.capture.Capture`: This widget allows capturing the current frame as an image file.
*   `widgets.ui.HeadsUpDisplay`: Displays text information on the screen.

## UML Diagrams

### Core Class Collaboration

```mermaid
graph TD
    subgraph Application
        A[main.App]
    end

    subgraph UI
        B[widgets.ui.UserInterface]
        F[widgets.ui.HeadsUpDisplay]
    end

    subgraph Navigation
        C[navigation.navigator.Navigator]
        G[navigation.rotator.Rotator]
    end

    subgraph Models
        D[models.Model]
        E((models.Cell*Model))
    end
    
    subgraph Data
        H[polytopes.py]
    end

    A -- "Uses" --> B
    A -- "Uses" --> C
    A -- "Uses" --> D
    A -- "Uses" --> F
    A -- "Uses" --> G
    A -- "Calls" --> H
    D <|-- E
    A -- "Creates" --> E
```
