import time
from pathlib import Path
import streamlit as st
from accounts import SESSION_TTL, register_account, login_account
ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data/auth.sqlite3"


def clear_session():
    for key in list(st.session_state):
        del st.session_state[key]


def require_login():
    user = st.session_state.get("authenticated_user")
    if user and user.get("method") == "password" and user["expires"] > time.time():
        with st.sidebar:
            st.caption("Tài khoản đang đăng nhập")
            st.write(user["name"])
            st.caption(user["email"])
            if st.button("Đăng xuất", key="logout"):
                clear_session()
                st.rerun()
        return user["email"]
    if user:
        clear_session()
        st.info("Vui lòng đăng nhập lại.")
    st.subheader("Tài khoản học tập")
    st.caption("Đăng ký bằng email và mật khẩu. Không gửi thư hoặc yêu cầu mã xác thực.")
    mode = st.radio("Tài khoản", ["Đăng nhập", "Đăng ký"], horizontal=True, key="account_mode")
    if mode == "Đăng ký":
        with st.form("register_account"):
            name = st.text_input("Tên hiển thị", max_chars=100, key="register_name")
            email = st.text_input("Email", key="register_email", placeholder="ban@example.com")
            password = st.text_input("Mật khẩu", type="password", max_chars=128, key="register_password")
            confirm = st.text_input("Nhập lại mật khẩu", type="password", max_chars=128, key="register_confirm")
            st.caption("Mật khẩu từ 8 đến 128 ký tự. Email dùng làm tên đăng nhập, chưa xác minh quyền sở hữu.")
            submitted = st.form_submit_button("Tạo tài khoản", type="primary")
        if submitted:
            try:
                register_account(DB, email, name, password, confirm)
                clear_session()
                st.session_state["registration_success"] = True
                st.rerun()
            except ValueError as exc:
                st.error(str(exc))
    else:
        if st.session_state.pop("registration_success", False):
            st.success("Đăng ký thành công. Hãy đăng nhập bằng email và mật khẩu vừa tạo.")
        with st.form("login_account"):
            email = st.text_input("Email", key="login_email", placeholder="ban@example.com")
            password = st.text_input("Mật khẩu", type="password", max_chars=128, key="login_password")
            submitted = st.form_submit_button("Đăng nhập", type="primary")
        if submitted:
            try:
                verified = login_account(DB, email, password)
                clear_session()
                st.session_state["authenticated_user"] = {**verified, "expires": time.time()+SESSION_TTL, "method": "password"}
                st.rerun()
            except ValueError as exc:
                st.error(str(exc))
    st.caption("Tài khoản lưu trên máy chủ ứng dụng. Điểm vẫn lưu trong phiên trình duyệt, chưa thành hồ sơ lâu dài theo tài khoản; tải CSV trước khi đăng xuất. Hiện chưa có chức năng quên mật khẩu.")
    st.stop()
