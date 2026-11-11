import unittest
import sys
from unittest.mock import patch
from pathlib import Path
from streamlit.testing.v1 import AppTest
ROOT = Path(__file__).resolve().parents[1]

class AppTests(unittest.TestCase):
    def setUp(self):
        sys.path.insert(0, str(ROOT / "src"))
        self.login_patch = patch("auth_ui.require_login", return_value="test@example.com")
        self.login_patch.start()
        self.addCleanup(self.login_patch.stop)

    def test_separate_courses(self):
        app = AppTest.from_file(str(ROOT / "app/app.py")).run(timeout=30)
        app.sidebar.radio[0].set_value("G2").run(timeout=30)
        app.sidebar.selectbox[0].set_value(4).run(timeout=30)
        for code, name, first, second in [("IT101", "Programming", 3.5, 2.7), ("MA101", "Math", 2.0, 3.2)]:
            app.text_input(key="course_code").set_value(code)
            app.text_input(key="course_name").set_value(name)
            app.number_input[0].set_value(first)
            app.number_input[1].set_value(second)
            app.button[0].click().run(timeout=30)
            self.assertEqual(len(app.exception), 0)
        table = app.dataframe[0].value
        self.assertEqual(len(table), 2)
        self.assertEqual(table.iloc[0]["xep_loai_G2"], "B+")
        self.assertEqual(table.iloc[1]["xep_loai_G2"], "A")
        self.assertEqual(len(app.metric), 3)
        self.assertTrue(all("trung bình" not in item.label for item in app.metric))
        app.selectbox(key="selected_course").set_value("MA101").run(timeout=30)
        self.assertIn("3.20", app.metric[1].value)
        app.sidebar.text_input[0].set_value("HK2 2026-2027").run(timeout=30)
        self.assertEqual(len(app.metric), 0)
        self.assertEqual(len(app.exception), 0)
