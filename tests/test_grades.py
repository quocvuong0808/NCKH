import unittest
import sys
from pathlib import Path
import pandas as pd
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from core import letter_grade, analyze_grades

class GradeTests(unittest.TestCase):
    def test_boundaries(self):
        cases = [(4, "A+"), (3.5, "A+"), (3.499, "A"), (3.2, "A"), (3.199, "B+"), (2.7, "B+"), (2.699, "B"), (2.5, "B"), (2.499, "C"), (2, "C"), (1.999, "D"), (0, "D")]
        for score, expected in cases:
            with self.subTest(score=score):
                self.assertEqual(letter_grade(score), expected)

    def test_scale_validation(self):
        for value in [-1, 4.01, float("nan")]:
            with self.assertRaises(ValueError):
                analyze_grades(pd.DataFrame({"G1": [value]}), "G1", 4)
        with self.assertRaises(ValueError):
            analyze_grades(pd.DataFrame({"G1": [10.01]}), "G1", 10)

    def test_no_invented_conversion(self):
        result = analyze_grades(pd.DataFrame({"G1": [8], "G2": [9]}), "G2", 10)
        self.assertNotIn("xep_loai_G2", result)
        self.assertEqual(result.iloc[0]["chenh_lech"], 1)
