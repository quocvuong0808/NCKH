# Đăng ký và đăng nhập tài khoản

Phiên bản hiện tại dùng email và mật khẩu, không xác thực email và không gửi OTP. Không cần làm theo cấu hình SMTP cũ, không cần secrets.toml. Các tệp mã OTP và secrets.example.toml cũ nếu còn tồn tại không được luồng đăng nhập hiện tại sử dụng.

## Cách dùng

1. Chạy web bằng lệnh bên dưới.
2. Chọn Đăng ký, nhập tên hiển thị, email, mật khẩu và nhập lại mật khẩu.
3. Bấm Tạo tài khoản. Mật khẩu cần 8–128 ký tự, hai lần nhập giống nhau.
4. Đăng nhập bằng email và mật khẩu vừa tạo. Email không phân biệt hoa/thường.
5. Chọn Đăng xuất ở thanh bên khi dùng xong. Tải CSV trước khi đăng xuất để giữ kết quả.

```powershell
.\.venv-win\Scripts\python.exe -m streamlit run app/app.py
```

Nếu web đang chạy, tải lại trang; có thể dừng bằng Ctrl+C và chạy lại lệnh trên.

## Lưu trữ và phạm vi

Tài khoản lưu trong bảng accounts của data/auth.sqlite3. Mật khẩu không lưu nguyên văn: PBKDF2-HMAC-SHA256, salt ngẫu nhiên 16 byte, 600.000 vòng; mỗi tài khoản có salt riêng. Tài khoản tồn tại sau khi khởi động lại máy chủ nếu còn file database. Database được loại khỏi Git.

Sau 5 lần nhập sai, tài khoản tạm khóa 5 phút. Phiên đăng nhập tối đa 2 giờ. Đăng xuất xóa toàn bộ dữ liệu phiên. Điểm vẫn chưa lưu thành hồ sơ lâu dài theo tài khoản; hiện chưa có chức năng quên/đổi mật khẩu.

Email chỉ là tên đăng nhập chưa xác minh, không chứng minh người dùng sở hữu hộp thư hoặc là sinh viên UTH. Không tự tạo lại tài khoản cùng email. Không xóa database để xử lý quên mật khẩu vì sẽ làm mất tất cả tài khoản.

Trước khi đưa công khai cần HTTPS và giới hạn lưu lượng tại hosting. Hiện là bản cục bộ cho đồ án, chưa có phân quyền quản trị và quản lý tài khoản đầy đủ.
