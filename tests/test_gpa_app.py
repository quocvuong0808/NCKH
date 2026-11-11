import unittest
import sys
from unittest.mock import patch
from pathlib import Path
from streamlit.testing.v1 import AppTest
ROOT=Path(__file__).resolve().parents[1]
class GPAAppTests(unittest.TestCase):
    def setUp(self):
        sys.path.insert(0, str(ROOT / "src"))
        self.login_patch = patch("auth_ui.require_login", return_value="test@example.com")
        self.login_patch.start()
        self.addCleanup(self.login_patch.stop)

    def test_manual_courses_and_semester_gpa(self):
        app=AppTest.from_file(str(ROOT/"app/app.py")).run(timeout=30)
        for code, name, credits, score in [("IT1","Programming",3,8.5),("MA1","Math",2,7.0)]:
            app.text_input(key="gpa_code").set_value(code)
            app.text_input(key="gpa_name").set_value(name)
            app.number_input(key="gpa_credits").set_value(credits)
            app.number_input(key="gpa_score").set_value(score)
            next(b for b in app.button if b.label.startswith("Lưu điểm")).click().run(timeout=30)
            self.assertEqual(len(app.exception),0)
        gpa=next(m for m in app.metric if m.label=="GPA hệ 4")
        rank=next(m for m in app.metric if m.label.startswith("Xếp loại học lực"))
        self.assertEqual(gpa.value,"3.600")
        self.assertEqual(rank.value,"Xuất sắc")
        self.assertEqual(len(app.session_state["official_courses_HK1 2026-2027"]),2)
