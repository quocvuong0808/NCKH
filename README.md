# Theo dõi môn học và GPA học kỳ — UTH

Ứng dụng có hai phần: theo dõi từng môn trong kỳ bằng G1/G2; tổng kết học kỳ bằng điểm học phần chính thức hệ 10 và số tín chỉ. Điểm từng môn được phân tích riêng; GPA học kỳ được tính có trọng số tín chỉ.

## Đăng ký và đăng nhập

Mở web, chọn Đăng ký, nhập tên hiển thị, email, mật khẩu và xác nhận mật khẩu. Sau khi tạo tài khoản, đăng nhập bằng email/mật khẩu vừa tạo. Không gửi mã xác thực, không cần cấu hình SMTP hoặc secrets.toml. Mật khẩu từ 8 đến 128 ký tự, lưu bằng PBKDF2-SHA256 với salt ngẫu nhiên. Xem [hướng dẫn tài khoản](docs/09_dang_nhap_email.md).

## Chạy

```powershell
.\.venv-win\Scripts\python.exe -m streamlit run app/app.py
```

Cài trên máy mới:

```powershell
py -3.13 -m venv .venv-win
.\.venv-win\Scripts\python.exe -m pip install -r requirements.txt
```

## GPA và tổng kết học kỳ

Chọn học kỳ ở thanh bên, vào tab GPA & tổng kết học kỳ, thêm mã môn, tên môn, tín chỉ và điểm học phần hệ 10 hoặc tải CSV. Lựa chọn G1/G2 và thang 4/10 ở thanh bên chỉ áp dụng cho tab theo dõi trong kỳ.

```csv
hoc_ky,ma_mon,ten_mon,so_tin_chi,diem_he10,loai
HK1 2026-2027,IT101,Lập trình C/C++,3,8.5,TINH_GPA
HK1 2026-2027,MA101,Toán cao cấp,2,7.0,TINH_GPA
HK1 2026-2027,EN101,Tiếng Anh,2,5.5,TINH_GPA
```

Điểm nhập là điểm học phần đã tổng hợp các thành phần, không phải điểm bài thi cuối kỳ đơn lẻ. Mỗi mã môn chỉ một dòng, một người học, một học kỳ. Nhập lại cùng mã môn để cập nhật. Điểm học lại phải là điểm chính thức được xác định theo quy chế trường; không nhập lặp các lần học để cộng GPA.

Quy đổi cơ bản theo Điều 9–10 Thông tư 08/2021/TT-BGDĐT:

| Điểm hệ 10 sau làm tròn 1 chữ số | Điểm chữ | Điểm hệ 4 |
|---|---|---|
| 8,5–10 | A | 4 |
| 7,0–8,4 | B | 3 |
| 5,5–6,9 | C | 2 |
| 4,0–5,4 | D | 1 |
| Dưới 4,0 | F | 0 |

GPA = tổng (điểm hệ 4 × tín chỉ) / tổng tín chỉ tính GPA. Không lấy trung bình hệ 10 rồi chia 2,5. Môn F vẫn ở mẫu số. Điểm học phần làm tròn một chữ số theo cách 5 tăng lên; GPA xếp loại trước khi làm tròn hiển thị.

| GPA hệ 4 | Học lực |
|---|---|
| 3,6–4,0 | Xuất sắc |
| 3,2–dưới 3,6 | Giỏi |
| 2,5–dưới 3,2 | Khá |
| 2,0–dưới 2,5 | Trung bình |
| 1,0–dưới 2,0 | Yếu |
| Dưới 1,0 | Kém |

Cột loai có thể bỏ hoặc để trống: mặc định TINH_GPA. Các giá trị P, I, X, R, NGOAI_CT không được đưa vào tử/mẫu số GPA. I/X là chưa hoàn thiện; không thay điểm thiếu bằng 0. P là đạt không phân mức, điểm nhập nếu có phải từ 5 sau làm tròn. Để trống diem_he10 cho I/X/R. Số tín chỉ phải là số nguyên dương.

Chỉ nhập một số môn thì kết quả là tạm tính. Xác nhận đủ môn không biến kết quả thành kết quả học vụ chính thức. Hệ thống hiển thị điểm mạnh A/B, kế hoạch cải thiện C/D/F theo môn và tín chỉ, mục tiêu học lực kế tiếp và kịch bản tăng một bậc điểm chữ. Kịch bản không cam kết kết quả hoặc quyền học cải thiện.

Nguồn: https://vanban.chinhphu.vn/default.aspx?docid=203159&pageid=27160 ; bản gốc https://datafiles.chinhphu.vn/cpp/files/vbpq/2021/04/08-bgd.signed.pdf . Đây là bảng cơ bản của Thông tư, chưa đối chiếu quy chế chi tiết của UTH. Bảng A+/B+ do người dùng cung cấp trước đây chỉ còn dùng trong phần theo dõi hệ 4, không dùng tính GPA theo Thông tư.

## Theo dõi từng môn trong kỳ

G1/G2 là hai lần đánh giá của cùng môn, không phải hai học kỳ. CSV gồm hoc_ky,ma_mon,ten_mon,G1 (thêm G2 nếu có). Chọn hệ 10 hoặc 4 tương ứng. Không lấy G1/G2 làm điểm học phần chính thức hoặc dùng chúng để tính GPA học kỳ.

## Lưu dữ liệu và kiểm tra

Danh sách được giữ trong phiên trình duyệt; tải CSV/JSON để lưu trước khi đóng. Phản hồi tự nguyện lưu SQLite cục bộ. Có đăng ký và đăng nhập email/mật khẩu; chưa có phân quyền quản trị hoặc hồ sơ điểm lưu lâu dài theo tài khoản. Không đưa thông tin cá nhân hoặc bí mật kết nối lên kho mã công khai.

```powershell
.\.venv-win\Scripts\python.exe -m unittest discover -s tests -v
```

Các mô hình và báo cáo UCI cũ chỉ phục vụ thử nghiệm phương pháp, không tính GPA và không được dùng làm bằng chứng dự báo cho UTH. Nguồn UCI tại docs/06_nguon_du_lieu.md. Xem docs/08_gpa_theo_thong_tu_08.md để biết phạm vi áp dụng.

## Dấu cảnh báo tự động theo môn

Cả nhập tay, tải CSV và dán CSV đều tự phân tích sau khi lưu/nhận dữ liệu hợp lệ. Bảng hiển thị biểu tượng và tô dòng đỏ/cam: hệ 10 dưới 4 là đỏ, từ 4 đến dưới 5,5 là cam; ở phần theo dõi hệ 4, dưới 2 là đỏ và từ 2 đến dưới 2,5 là cam theo quy tắc ứng dụng. Đây không phải quy đổi hai thang hay cảnh báo học vụ chính thức. Môn P/I/X/R/NGOAI_CT trong bảng GPA hiển thị không đánh giá, không gán nguy cơ thấp. GPA dùng điểm đã làm tròn; phần theo dõi dùng điểm đánh giá hiện tại. Khi điểm được cập nhật, cảnh báo tự tính lại và có trong CSV xuất.
