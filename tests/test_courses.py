import unittest
import sys
from pathlib import Path
import pandas as pd
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from core import analyze_courses

class CourseTests(unittest.TestCase):
    def frame(self):
        return pd.DataFrame({"hoc_ky": ["HK1", "HK1"], "ma_mon": ["IT1", "MA1"], "ten_mon": ["Programming", "Math"], "G1": [3.5, 2], "G2": [2.7, 3.2]})

    def test_course_independence(self):
        data = self.frame()
        before = analyze_courses(data, "G2", 4)
        data.loc[1, "G2"] = 0
        after = analyze_courses(data, "G2", 4)
        pd.testing.assert_series_equal(before.iloc[0], after.iloc[0])
        self.assertEqual(before.iloc[0].ma_mon, "IT1")
        self.assertEqual(before.iloc[0].xu_huong, "Giảm")
        self.assertEqual(before.iloc[1].xu_huong, "Tăng")

    def test_duplicate_course_rejected(self):
        data = self.frame()
        data.loc[1, "ma_mon"] = "IT1"
        with self.assertRaises(ValueError):
            analyze_courses(data, "G2", 4)
        data.loc[1, "hoc_ky"] = "HK2"
        self.assertEqual(len(analyze_courses(data, "G2", 4)), 2)

    def test_identifiers_required(self):
        data = self.frame()
        data.loc[0, "ten_mon"] = " "
        with self.assertRaises(ValueError):
            analyze_courses(data, "G2", 4)
