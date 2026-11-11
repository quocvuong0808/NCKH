"""Local accounts; email is a login identifier, not a verified identity."""
import hashlib
import hmac
import secrets
import sqlite3
import time
from contextlib import closing
from pathlib import Path
from auth import normalize_email

SESSION_TTL = 7200
ITERATIONS = 600000


def connect(path):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(path, timeout=15)
    db.row_factory = sqlite3.Row
    db.execute("CREATE TABLE IF NOT EXISTS accounts (email TEXT PRIMARY KEY, name TEXT NOT NULL, salt TEXT NOT NULL, password_hash TEXT NOT NULL, iterations INTEGER NOT NULL, created REAL NOT NULL, failures INTEGER NOT NULL DEFAULT 0, locked REAL NOT NULL DEFAULT 0)")
    db.commit()
    return db


def password_hash(password, salt, iterations=ITERATIONS):
    return hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), bytes.fromhex(salt), iterations).hex()


def register_account(path, email, name, password, confirmation):
    email = normalize_email(email)
    name = str(name).strip()
    if not name or len(name) > 100:
        raise ValueError("Tên hiển thị cần từ 1 đến 100 ký tự.")
    if not isinstance(password, str) or not 8 <= len(password) <= 128:
        raise ValueError("Mật khẩu cần từ 8 đến 128 ký tự.")
    if password != confirmation:
        raise ValueError("Mật khẩu nhập lại không khớp.")
    salt = secrets.token_hex(16)
    hashed = password_hash(password, salt)
    try:
        with closing(connect(path)) as db, db:
            db.execute("INSERT INTO accounts (email,name,salt,password_hash,iterations,created) VALUES (?,?,?,?,?,?)", (email, name, salt, hashed, ITERATIONS, time.time()))
    except sqlite3.IntegrityError:
        raise ValueError("Email này đã được đăng ký. Vui lòng đăng nhập hoặc dùng email khác.") from None
    return {"email": email, "name": name}


def login_account(path, email, password, now=None):
    email = normalize_email(email)
    if not isinstance(password, str) or not 1 <= len(password) <= 128:
        raise ValueError("Email hoặc mật khẩu không đúng.")
    now = time.time() if now is None else now
    user = None
    with closing(connect(path)) as db, db:
        db.execute("BEGIN IMMEDIATE")
        row = db.execute("SELECT * FROM accounts WHERE email=?", (email,)).fetchone()
        if row is None:
            password_hash(password, "0"*32)  # Comparable work for unknown accounts.
        elif row["locked"] <= now:
            if hmac.compare_digest(row["password_hash"], password_hash(password, row["salt"], row["iterations"])):
                db.execute("UPDATE accounts SET failures=0,locked=0 WHERE email=?", (email,))
                user = {"email": row["email"], "name": row["name"]}
            else:
                failures = (0 if row["locked"] else row["failures"]) + 1
                db.execute("UPDATE accounts SET failures=?,locked=? WHERE email=?", (failures, now+300 if failures >= 5 else 0, email))
    if user is None:
        raise ValueError("Email hoặc mật khẩu không đúng, hoặc tài khoản đang tạm khóa. Sau 5 lần sai, chờ 5 phút rồi thử lại.")
    return user
