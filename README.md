# Polytope Visualizer

This project is a simple visualizer for 4D polytopes, specifically the 24-cell, using Python, OpenGL, and GLFW.

## Running the visualizer

1.  **Install dependencies:**

    You will need `numpy`, `PyOpenGL`, and `glfw`. You can install them using pip:

    ```
    pip install -r requirements.txt
    ```

2.  **Run the main script:**

    ```
    python polytope/main.py
    ```

## Interaction

-   **Rotate the 3D view:** Click and drag the left mouse button.
-   **Close the window:** Press the `ESC` key.

The 24-cell will also slowly rotate in 4D on its own.

## Project Structure

-   `polytope/main.py`: The main script that runs the application.
-   `polytope/viz/ui.py`: The `UserInterface` class for windowing and event handling.
-   `polytope/navigation/navigator.py`: The `Navigator` class for handling 3D rotation via mouse input.
-   `polytope/polytopes.py`: Contains the code to generate the 24-cell and project it from 4D to 3D.
-   `polytope/requirements.txt`: The python dependencies.
