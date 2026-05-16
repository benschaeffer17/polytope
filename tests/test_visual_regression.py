import os
import sys
import pytest
import numpy as np
from PIL import Image
import glfw
from OpenGL.GL import glClear, GL_COLOR_BUFFER_BIT, GL_DEPTH_BUFFER_BIT

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from main import App

GOLDEN_DIR = os.path.join(os.path.dirname(__file__), "goldens")

from visual_configs import CONFIGS

@pytest.fixture(scope="session")
def app_instance():
    """Provides a single headless App instance for all tests to save GL initialization time."""
    app = App(headless=True)
    app.setup_gl()
    yield app
    glfw.terminate()

@pytest.mark.parametrize("config_name,config", CONFIGS.items())
def test_visual_regression(app_instance, config_name, config):
    golden_path = os.path.join(GOLDEN_DIR, f"{config_name}.png")

    assert os.path.exists(golden_path), f"Golden image {golden_path} not found. Run generate_goldens.py first."

    golden_image = Image.open(golden_path)
    golden_array = np.array(golden_image)

    # Apply configuration
    for key, value in config.items():
        setattr(app_instance, key, value)

    app_instance.load_shape()
    app_instance.show_help = False

    width, height = glfw.get_window_size(app_instance.ui.window)

    # Render
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    app_instance.draw()
    glfw.swap_buffers(app_instance.ui.window)
    glfw.poll_events()

    # Capture pixels
    current_image = app_instance.ui.get_pixels(width, height)
    current_array = np.array(current_image)

    # Compare
    assert current_array.shape == golden_array.shape, "Generated image dimensions do not match golden."

    # Calculate Mean Squared Error (MSE) to allow minor OS-level anti-aliasing differences
    mse = np.mean((current_array.astype(float) - golden_array.astype(float)) ** 2)
    assert mse < 1.0, f"Visual regression detected for {config_name}. MSE: {mse}"
