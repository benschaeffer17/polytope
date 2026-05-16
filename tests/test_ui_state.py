"""Unit tests for UI State Management without OpenGL dependencies."""

import pytest
from widgets.state import UIStateVariable, UIStateManager

def test_ui_state_variable_toggle():
    var = UIStateVariable("color", ["red", "green", "blue"], key=1, key_name="1", help_text="Color", default_index=0)
    assert var.get_value() == "red"
    
    var.toggle()
    assert var.get_value() == "green"
    
    var.toggle()
    assert var.get_value() == "blue"
    
    var.toggle()
    assert var.get_value() == "red"  # Wraps around

def test_ui_state_variable_callback():
    callback_fired = False
    
    def on_change():
        nonlocal callback_fired
        callback_fired = True
        
    var = UIStateVariable("color", ["red", "green"], key=1, key_name="1", help_text="Color", default_index=0, on_change=on_change)
    var.toggle()
    
    assert callback_fired is True

def test_ui_state_variable_format_hud():
    var = UIStateVariable("color", ["red", "green"], key=1, key_name="1", help_text="Color", default_index=0, hud_formatter=lambda x: f"C:{x.upper()}")
    assert var.format_hud() == "C:RED"

def test_ui_state_manager_register_and_route():
    manager = UIStateManager()
    var = UIStateVariable("color", ["red", "green"], key=42, key_name="C", help_text="Change Color", default_index=0)
    
    manager.register(var)
    assert manager.get_variable("color") == var
    
    # Send wrong key
    assert manager.handle_keypress(99) is False
    assert var.get_value() == "red"
    
    # Send correct key
    assert manager.handle_keypress(42) is True
    assert var.get_value() == "green"

def test_ui_state_manager_help_lines():
    manager = UIStateManager()
    manager.register(UIStateVariable("color", ["red", "green"], key=42, key_name="C", help_text="Change Color", default_index=0))
    manager.register(UIStateVariable("size", [1, 2], key=43, key_name="S", help_text="Change Size", default_index=0))
    
    lines = manager.get_help_lines()
    assert "POLYTOPE VISUALIZER KEYBOARD CONTROLS" in lines[0]
    assert "C: Change Color" in lines
    assert "S: Change Size" in lines
