"""Email OTP with server-side rate limits; no plaintext OTP storage."""
import hashlib
import hmac
import re
import secrets
import smtplib
import sqlite3
import ssl
import time
from contextlib import closing
from email.message import EmailMessage
from pathlib import Path

TTL = 300
COOLDOWN = 60
MAX_ATTEMPTS = 5
SESSION_TTL = 7200


def normalize_email(value):
    email = str(value).strip().lower()
    if len(email) > 254 or not re.fullmatch(r"[a-z0-9.!#$%&'*+/=?^_`{|}~-]+@[a-z0-9](?:[a-z0-9.-]*[a-z0-9])?\.[a-z]{2,63}", email):
        raise ValueError("Địa chỉ email không hợp lệ.")
    return email


def digest(secret, challenge, email, code):
    return hmac.new(secret.encode(), f"{challenge}|{email}|{code}".encode(), hashlib.sha256).hexdigest()


def connect(path):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(path, timeout=15)
    db.row_factory = sqlite3.Row
    db.execute("CREATE TABLE IF NOT EXISTS email_otp (email TEXT PRIMARY KEY, challenge TEXT, digest TEXT, expires REAL, sent REAL, tries INTEGER, locked REAL, window REAL, count INTEGER)")
    db.commit()
    return db


def send_email(config, recipient, code):
    message = EmailMessage()
    message["Subject"] = "Mã đăng nhập · Theo dõi học tập UTH"
    message["From"] = config.get("from_email") or config["username"]
    message["To"] = recipient
    message.set_content(f"Mã đăng nhập của bạn: {code}\n\nMã có hiệu lực 5 phút và chỉ dùng một lần. Không chia sẻ mã. Nếu không yêu cầu đăng nhập, hãy bỏ qua thư này.\n\nỨng dụng đồ án hỗ trợ học tập; không phải thông báo học vụ chính thức của UTH.")
    context = ssl.create_default_context()
    if config.get("security", "starttls") == "ssl":
        with smtplib.SMTP_SSL(config["host"], int(config["port"]), timeout=20, context=context) as smtp:
            smtp.login(config["username"], config["password"])
            smtp.send_message(message)
    else:
        with smtplib.SMTP(config["host"], int(config["port"]), timeout=20) as smtp:
            smtp.ehlo()
            smtp.starttls(context=context)
            smtp.ehlo()
            smtp.login(config["username"], config["password"])
            smtp.send_message(message)


def request_code(path, config, secret, email, sender=send_email, now=None):
    email = normalize_email(email)
    if len(secret) < 32:
        raise ValueError("Cần khóa auth.secret ngẫu nhiên dài ít nhất 32 ký tự.")
    now = time.time() if now is None else now
    challenge = secrets.token_urlsafe(32)
    code = f"{secrets.randbelow(1000000):06d}"
    with closing(connect(path)) as db, db:
        db.execute("BEGIN IMMEDIATE")
        row = db.execute("SELECT * FROM email_otp WHERE email=?", (email,)).fetchone()
        if row and row["locked"] > now:
            raise ValueError("Đã nhập sai quá nhiều lần. Vui lòng chờ 5 phút.")
        if row and now - row["sent"] < COOLDOWN:
            raise ValueError("Vui lòng chờ 60 giây giữa hai lần gửi mã.")
        window = row["window"] if row and now - row["window"] < 3600 else now
        count = row["count"] if row and now - row["window"] < 3600 else 0
        if count >= 5:
            raise ValueError("Email này đã đạt giới hạn 5 lần gửi trong một giờ.")
        global_count = db.execute("SELECT COALESCE(SUM(count),0) FROM email_otp WHERE window > ?", (now-3600,)).fetchone()[0]
        if global_count >= 100:
            raise ValueError("Hệ thống đang đạt giới hạn gửi thư. Vui lòng thử lại sau.")
        db.execute("INSERT OR REPLACE INTO email_otp VALUES (?,?,?,?,?,?,?,?,?)", (email, challenge, digest(secret, challenge, email, code), now+TTL, now, 0, 0, window, count+1))
        db.execute("DELETE FROM email_otp WHERE sent < ? AND locked < ?", (now-86400, now))
    try:
        sender(config, email, code)
    except Exception:
        # Keep send counters even on delivery failures, but invalidate the code.
        with closing(connect(path)) as db, db:
            db.execute("UPDATE email_otp SET digest='' WHERE email=? AND challenge=?", (email,challenge))
        raise ValueError("Chưa gửi được email. Kiểm tra cấu hình SMTP, mật khẩu ứng dụng và kết nối mạng; thử lại sau 60 giây.") from None
    return email, challenge


def verify_code(path, secret, email, challenge, code, now=None):
    email = normalize_email(email)
    now = time.time() if now is None else now
    valid = False
    with closing(connect(path)) as db, db:
        db.execute("BEGIN IMMEDIATE")
        row = db.execute("SELECT * FROM email_otp WHERE email=?", (email,)).fetchone()
        if row and row["challenge"] == challenge and row["digest"] and row["expires"] > now and row["locked"] <= now and row["tries"] < MAX_ATTEMPTS:
            valid = bool(re.fullmatch(r"[0-9]{6}", str(code))) and hmac.compare_digest(row["digest"], digest(secret, challenge, email, str(code)))
            if valid:
                db.execute("UPDATE email_otp SET digest='', expires=0 WHERE email=?", (email,))
            else:
                tries = row["tries"]+1
                db.execute("UPDATE email_otp SET tries=?, locked=? WHERE email=?", (tries, now+TTL if tries >= MAX_ATTEMPTS else 0, email))
    if not valid:
        raise ValueError("Mã không đúng, đã hết hạn hoặc đã bị khóa. Tối đa 5 lần thử; mã chỉ dùng được một lần.")
    return email
