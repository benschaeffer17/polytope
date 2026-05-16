"""Module for encapsulating UI State Variables and routing logic."""

from typing import List, Callable, Any, Optional

class UIAction:
    """Encapsulates a stateless UI action (e.g., zoom, speed up)."""
    def __init__(self, key: int, key_name: str, help_text: str, on_action: Callable[[], None]):
        self.name = help_text
        self.key = key
        self.key_name = key_name
        self.help_text = help_text
        self.on_action = on_action

    def toggle(self):
        """Executes the action."""
        if self.on_action:
            self.on_action()

    def format_hud(self) -> str:
        return ""

class UIStateVariable:
    """Encapsulates a single configurable UI setting."""
    def __init__(self,
                 name: str,
                 options: List[Any],
                 key: int,
                 key_name: str,
                 help_text: str,
                 default_index: int = 0,
                 on_change: Optional[Callable[[], None]] = None,
                 hud_formatter: Optional[Callable[[Any], str]] = None):
        """Initializes the UI state variable."""
        self.name = name
        self.options = options
        self.current_index = default_index
        self.key = key
        self.key_name = key_name
        self.help_text = help_text
        self.on_change = on_change
        self.hud_formatter = hud_formatter

    def toggle(self):
        """Advances the state to the next option and triggers callback."""
        if not self.options:
            return
        self.current_index = (self.current_index + 1) % len(self.options)
        if self.on_change:
            self.on_change()

    def get_value(self) -> Any:
        """Returns the currently selected option value."""
        if not self.options:
            return None
        return self.options[self.current_index]

    def set_index(self, index: int):
        """Manually sets the state index and triggers callback."""
        if 0 <= index < len(self.options):
            self.current_index = index
            if self.on_change:
                self.on_change()

    def format_hud(self) -> str:
        """Formats the current value for the HUD."""
        val = self.get_value()
        if self.hud_formatter:
            return self.hud_formatter(val)
        return str(val)

class UIStateManager:
    """Manages a registry of UI State Variables and handles key routing."""
    def __init__(self):
        """Initializes the UI State Manager."""
        self.variables = []
        self._key_map = {}

    def register(self, variable: UIStateVariable):
        """Registers a new UI State Variable."""
        self.variables.append(variable)
        if variable.key is not None:
            self._key_map[variable.key] = variable

    def handle_keypress(self, key: int) -> bool:
        """Routes a keypress to the appropriate variable. Returns True if handled."""
        if key in self._key_map:
            self._key_map[key].toggle()
            return True
        return False

    def get_help_lines(self) -> List[str]:
        """Generates the dynamic help screen lines."""
        lines = [
            "POLYTOPE VISUALIZER KEYBOARD CONTROLS",
            ""
        ]
        for var in self.variables:
            if var.key_name and var.help_text:
                lines.append(f"{var.key_name}: {var.help_text}")
        return lines

    def get_variable(self, name: str) -> Optional[UIStateVariable]:
        """Retrieves a variable by its name."""
        for var in self.variables:
            if var.name == name:
                return var
        return None
