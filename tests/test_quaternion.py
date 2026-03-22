
import unittest
import numpy as np
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from quaternion import q_mult, order6, order10

class TestQuaternion(unittest.TestCase):

    def test_order6_pow_6_is_one(self):
        """
        Tests that for q = order6, q^6 is (1,0,0,0).
        """
        q = order6
        q_pow = np.copy(q)
        for _ in range(5):
            q_pow = q_mult(q_pow, q)
        
        expected = np.array([1.0, 0.0, 0.0, 0.0])
        # Let's check the norm of q_pow to see if it is 1.
        norm_q_pow = np.linalg.norm(q_pow)
        self.assertAlmostEqual(norm_q_pow, 1.0, places=5, msg="q^6 should be a unit quaternion")
        self.assertTrue(np.allclose(q_pow, expected), f"q^6 is {q_pow}, expected {expected}")

    def test_order10_pow_10_is_one(self):
        """
        Tests that for q = order10, q^10 is (1,0,0,0).
        """
        q = order10
        q_pow = np.copy(q)
        for _ in range(9):
            q_pow = q_mult(q_pow, q)
        
        expected = np.array([1.0, 0.0, 0.0, 0.0])
        # Let's check the norm of q_pow to see if it is 1.
        norm_q_pow = np.linalg.norm(q_pow)
        self.assertAlmostEqual(norm_q_pow, 1.0, places=5, msg="q^10 should be a unit quaternion")
        self.assertTrue(np.allclose(q_pow, expected), f"q^10 is {q_pow}, expected {expected}")

if __name__ == '__main__':
    unittest.main()
