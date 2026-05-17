# ADR 0001: UI State Manager Encapsulation

**Status:** Accepted
**Date:** 2026-05-17

## Context: The "Triple Maintenance" Anti-Pattern

As the Polytope Visualizer grew in complexity (adding topological grouping, depth-first search colors, and perspective slicing), the `main.py` application file became heavily bloated. 

The core issue was a lack of separation of concerns. The application suffered from the **Triple Maintenance Anti-Pattern**, where introducing a single new interactive feature (e.g., face opacity) required modifying the code in three tightly coupled locations:
1. **The Application State:** Defining the variable array (`[0.2, 0.4, 0.6, 0.8, 1.0]`) and tracking the index.
2. **The Key Callback Route:** Writing a hardcoded `toggle_opacity()` method and mapping it to the GLFW `UserInterface` dictionary.
3. **The HUD / Help Screen:** Manually updating strings in the `render_help()` function to explain the keybind to the user.

This imperative paradigm made the UI completely untestable in a Headless (pure Python) environment, as the state was inextricably bound to the active GLFW OpenGL context.

## Options Considered

1. **Continue Imperative Growth:** Leave the state in `main.py` but move the toggle functions to a helper file. *Rejected: Did not solve the Triple Maintenance issue or enable unit testing.*
2. **Adopt an External UI Framework:** Integrate DearPyGui or PyQt to handle state. *Rejected: Overkill for a lightweight, high-performance visualization tool relying on raw OpenGL.*
3. **Declarative State Encapsulation (Chosen):** Implement the Observer Pattern and centralized Registry Pattern to decouple the "What" from the "How".

## Decision: Declarative UIStateManager

We implemented a centralized `UIStateManager` (`widgets.state`) that utilizes a declarative **Registry Pattern**. 

Instead of writing custom methods for every feature, developers now register a `UIStateVariable` object. The `UIStateVariable` encapsulates its own bounds-checking, its value arrays, and its description.

```python
# The declarative definition automatically handles the array wrapping, 
# keybind routing, and Help Menu generation.
self.state.register(UIStateVariable("blend", [0.2, 0.4, 0.6, 0.8, 1.0], glfw.KEY_Q, "Q", "Toggle face opacity", default_index=4))
```

## Consequences

*   **100% Headless Testability:** Because the `UIStateManager` is decoupled from GLFW, the UI logic can now be subjected to lightning-fast, pure-Python unit tests (`test_ui_state.py`). We can mathematically prove the UI state wraps and triggers callbacks correctly without spinning up an OpenGL window.
*   **Single Source of Truth:** Adding a new visual parameter requires exactly one line of code. The `UIStateManager` automatically inspects the registry to generate the Heads Up Display text and the interactive Help screen overlay. 
*   **Reduced Blast Radius:** The `main.py` controller dropped by over 130 lines of boilerplate imperative code, raising the overall project Pylint score to an 8.57/10. Future geometry models are entirely insulated from UI rendering logic.
