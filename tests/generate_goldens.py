"""
Utility script to generate the golden visual regression baseline images.
"""

import os
import sys
import glfw
from OpenGL.GL import glClear, GL_COLOR_BUFFER_BIT, GL_DEPTH_BUFFER_BIT

# Add parent directory to path so we can import from main project
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from visual_configs import CONFIGS
from main import App

GOLDEN_DIR = os.path.join(os.path.dirname(__file__), "goldens")

def generate_goldens():
    """Generates and saves the baseline 'golden' images for all configs."""
    if not os.path.exists(GOLDEN_DIR):
        os.makedirs(GOLDEN_DIR)

    # Initialize headless app
    app = App(headless=True)
    app.setup_gl()

    width, height = glfw.get_window_size(app.ui.window)

    for name, config in CONFIGS.items():
        print(f"Generating golden for {name}...")

        # Apply config
        for key, value in config.items():
            setattr(app, key, value)

        app.load_shape()

        # Clear buffer
        # pylint: disable=unsupported-binary-operation
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        # pylint: enable=unsupported-binary-operation

        # Disable help text for goldens
        app.show_help = False

        # Render
        app.draw()
        glfw.swap_buffers(app.ui.window)
        glfw.poll_events()

        # Extract pixels
        image = app.ui.get_pixels(width, height)

        # Save golden
        image_path = os.path.join(GOLDEN_DIR, f"{name}.png")
        image.save(image_path)
        print(f"Saved: {image_path}")

    # Cleanup
    glfw.terminate()

if __name__ == "__main__":
    generate_goldens()
