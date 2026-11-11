import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from streamlit.testing.v1 import AppTest
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"src"))

class AuthUITests(unittest.TestCase):
    def setUp(self):
        self.folder=tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        self.db_patch=patch("auth_ui.DB",Path(self.folder.name)/"auth.sqlite3")
        self.db_patch.start()
        self.addCleanup(self.db_patch.stop)
    def test_anonymous_blocked_without_smtp(self):
        app=AppTest.from_file(str(ROOT/"app/app.py")).run(timeout=30)
        self.assertEqual(len(app.exception),0)
        self.assertEqual(len(app.tabs),0)
        self.assertEqual(app.radio(key="account_mode").value,"Đăng nhập")
    def test_register_login_logout(self):
        app=AppTest.from_file(str(ROOT/"app/app.py")).run(timeout=30)
        app.radio(key="account_mode").set_value("Đăng ký").run(timeout=30)
        app.text_input(key="register_name").set_value("Student")
        app.text_input(key="register_email").set_value("student@example.com")
        app.text_input(key="register_password").set_value("good-pass-123")
        app.text_input(key="register_confirm").set_value("good-pass-123")
        app.button[0].click().run(timeout=30)
        self.assertEqual(len(app.exception),0)
        app.text_input(key="login_email").set_value("student@example.com")
        app.text_input(key="login_password").set_value("good-pass-123")
        app.button[0].click().run(timeout=30)
        self.assertEqual(len(app.exception),0)
        self.assertEqual(len(app.tabs),4)
        app.session_state["private_test_data"]="must disappear"
        app.button(key="logout").click().run(timeout=30)
        self.assertEqual(len(app.tabs),0)
        with self.assertRaises(KeyError): app.session_state["private_test_data"]
