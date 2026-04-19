import unittest
import numpy as np
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from models.color_constants import get_scaling_multiplier_by_color, COLOR_SEQUENCE, COLOR_VALUES

class TestColorConstants(unittest.TestCase):
    def test_get_scaling_multiplier_by_color(self):
        """
        Test that scaling multiplier correctly interpolates from 0.9 to 1.1 across the color sequence.
        """
        # Test first and last color in sequence specifically
        first_color = COLOR_SEQUENCE[0]
        last_color = COLOR_SEQUENCE[-1]
        
        mult_first = get_scaling_multiplier_by_color(COLOR_VALUES[first_color])
        self.assertAlmostEqual(mult_first, 0.9, places=5, msg=f"First color {first_color} should have multiplier 0.9")
        
        mult_last = get_scaling_multiplier_by_color(COLOR_VALUES[last_color])
        self.assertAlmostEqual(mult_last, 1.1, places=5, msg=f"Last color {last_color} should have multiplier 1.1")
        
        # Ensure it increases monotonically
        previous_mult = 0.0
        for color_name in COLOR_SEQUENCE:
            mult = get_scaling_multiplier_by_color(COLOR_VALUES[color_name])
            self.assertTrue(mult > previous_mult, f"Multiplier {mult} for {color_name} should be greater than previous {previous_mult}")
            previous_mult = mult

    def test_get_scaling_multiplier_unmatched_color(self):
        """
        Test that scaling multiplier falls back to 1.0 for unmatched colors.
        """
        # An arbitrary color not in the sequence (e.g. gray)
        gray = [0.5, 0.5, 0.5]
        self.assertAlmostEqual(get_scaling_multiplier_by_color(gray), 1.0)
        
        # Test 4D vector handling (RGBA) for a color not in sequence
        transparent_gray = [0.5, 0.5, 0.5, 0.5]
        self.assertAlmostEqual(get_scaling_multiplier_by_color(transparent_gray), 1.0)

    def test_get_scaling_multiplier_with_alpha(self):
        """
        Test that a sequence color with an alpha channel still matches.
        """
        # RED with alpha channel
        red_rgba = COLOR_VALUES["RED"] + [0.5]
        self.assertAlmostEqual(get_scaling_multiplier_by_color(red_rgba), 0.9)

if __name__ == '__main__':
    unittest.main()
