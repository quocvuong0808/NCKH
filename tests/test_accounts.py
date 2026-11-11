import sqlite3
import sys
import tempfile
import unittest
from contextlib import closing
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"src"))
from accounts import register_account, login_account

class AccountTests(unittest.TestCase):
    def setUp(self):
        self.folder=tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        self.db=Path(self.folder.name)/"accounts.sqlite3"
    def register(self,email="student@example.com"):
        return register_account(self.db,email,"Student","good-pass-123","good-pass-123")
    def test_registration_and_login(self):
        self.register("Student@Example.com")
        self.assertEqual(login_account(self.db,"STUDENT@example.com","good-pass-123")["email"],"student@example.com")
        with self.assertRaises(ValueError): self.register()
    def test_validation(self):
        for email,name,pw,confirmation in [("bad","Name","password","password"),("a@example.com","","password","password"),("a@example.com","Name","short","short"),("a@example.com","Name","password","different")]:
            with self.assertRaises(ValueError): register_account(self.db,email,name,pw,confirmation)
    def test_hash_and_unique_salt(self):
        self.register()
        self.register("other@example.com")
        with closing(sqlite3.connect(self.db)) as db:
            rows=db.execute("SELECT salt,password_hash FROM accounts").fetchall()
        self.assertNotEqual(rows[0][0],rows[1][0])
        self.assertNotEqual(rows[0][1],rows[1][1])
        self.assertNotEqual(rows[0][1],"good-pass-123")
    def test_failed_login_lock_and_recovery(self):
        self.register()
        for n in range(5):
            with self.assertRaises(ValueError): login_account(self.db,"student@example.com","incorrect",now=1000+n)
        with self.assertRaises(ValueError): login_account(self.db,"student@example.com","good-pass-123",now=1006)
        self.assertEqual(login_account(self.db,"student@example.com","good-pass-123",now=1400)["name"],"Student")
        with self.assertRaises(ValueError): login_account(self.db,"missing@example.com","good-pass-123")
