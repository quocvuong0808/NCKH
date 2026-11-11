import sys
import tempfile
import sqlite3
from contextlib import closing
import unittest
from pathlib import Path
import pandas as pd
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from core import validate, advice, save_feedback

class CoreTests(unittest.TestCase):
    def test_reject_invalid_or_unknown(self):
        for frame in [pd.DataFrame({"G1": [None]}), pd.DataFrame({"G1": [21]}), pd.DataFrame({"G1": ["abc"]}), pd.DataFrame({"G2": [10]}), pd.DataFrame(columns=["G1"])]:
            with self.assertRaises(ValueError):
                validate(frame, "G1")

    def test_future_grade_excluded(self):
        frame = pd.DataFrame({"G1": [12], "G2": [8], "G3": [0], "absences": [40]})
        self.assertEqual(list(validate(frame, "G1").columns), ["G1"])
        self.assertEqual(list(validate(frame, "G2").columns), ["G1", "G2"])

    def test_decline_advice(self):
        reasons, actions = advice({"G1": 15, "G2": 8}, "G2")
        self.assertIn("thấp hơn", reasons)
        self.assertIn("lịch", actions)

    def test_feedback_parameterized(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "feedback.db"
            save_feedback(path, "G1", 5, "'; DROP TABLE feedback; --")
            with closing(sqlite3.connect(path)) as db, db:
                self.assertEqual(db.execute("SELECT COUNT(*) FROM feedback").fetchone()[0], 1)

if __name__ == "__main__":
    unittest.main()
