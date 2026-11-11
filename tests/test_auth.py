import sqlite3
from contextlib import closing
import sys
import tempfile
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from auth import request_code, verify_code, normalize_email

class AuthTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path=Path(self.tmp.name)/"auth.sqlite3"
        self.secret="x"*64
        self.mail=[]
    def send(self, config, email, code):
        self.mail.append((email,code))
    def request(self, now=10000):
        return request_code(self.path,{},self.secret,"Student@example.com",sender=self.send,now=now)
    def test_success_and_single_use(self):
        email,ch=self.request()
        code=self.mail[-1][1]
        self.assertEqual(verify_code(self.path,self.secret,email,ch,code,now=10001),email)
        with self.assertRaises(ValueError): verify_code(self.path,self.secret,email,ch,code,now=10002)
    def test_expiration(self):
        email,ch=self.request()
        with self.assertRaises(ValueError): verify_code(self.path,self.secret,email,ch,self.mail[-1][1],now=10300)
    def test_resend_and_cross_session(self):
        email,ch=self.request()
        with self.assertRaises(ValueError): self.request(10030)
        email,ch2=self.request(10061)
        with self.assertRaises(ValueError): verify_code(self.path,self.secret,email,ch,self.mail[0][1],now=10062)
        self.assertEqual(verify_code(self.path,self.secret,email,ch2,self.mail[-1][1],now=10063),email)
    def test_attempt_lock_cannot_be_reset_by_resending(self):
        email,ch=self.request()
        wrong="000000" if self.mail[-1][1]!="000000" else "111111"
        for n in range(5):
            with self.assertRaises(ValueError): verify_code(self.path,self.secret,email,ch,wrong,now=10001+n)
        with self.assertRaises(ValueError): verify_code(self.path,self.secret,email,ch,self.mail[-1][1],now=10006)
        with self.assertRaises(ValueError): self.request(10070)
    def test_hourly_limit(self):
        for n in range(5): self.request(10000+n*61)
        with self.assertRaises(ValueError): self.request(10400)
    def test_no_plaintext_code_and_failed_delivery(self):
        email,ch=self.request()
        with closing(sqlite3.connect(self.path)) as db:
            row=db.execute("SELECT digest FROM email_otp").fetchone()
        self.assertNotEqual(self.mail[-1][1],row[0])
        self.assertEqual(len(row[0]),64)
        def fail(*args): raise RuntimeError("SMTP_SECRET_MUST_NOT_LEAK")
        with self.assertRaises(ValueError) as error:
            request_code(self.path,{},self.secret,"other@example.com",sender=fail,now=10000)
        self.assertNotIn("SMTP_SECRET",str(error.exception))
    def test_invalid_email(self):
        for value in ["", "user", "user@example.com\nBcc:bad@example.com"]:
            with self.assertRaises(ValueError): normalize_email(value)
