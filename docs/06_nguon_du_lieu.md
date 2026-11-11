# Nguồn dữ liệu và ghi công

## UCI Student Performance
- Nguồn chính thức: https://archive.ics.uci.edu/dataset/320/student%2Bperformance
- DOI: https://doi.org/10.24432/C5TG7T
- Tác giả dữ liệu: Paulo Cortez (2008).
- Trích dẫn: Cortez, P. (2008). *Student Performance* [Dataset]. UCI Machine Learning Repository. https://doi.org/10.24432/C5TG7T.
- Giấy phép theo UCI: Creative Commons Attribution 4.0 International (CC BY 4.0); cần ghi công khi chia sẻ hoặc điều chỉnh.
- Nội dung: hai tệp môn Toán và tiếng Bồ Đào Nha; nhóm chọn `student-por.csv` cho bản thử nghiệm. UCI mô tả dữ liệu là thành tích học sinh trung học tại hai trường ở Bồ Đào Nha.
- Biến thời gian: G1 là điểm kỳ 1, G2 kỳ 2, G3 điểm cuối năm. UCI lưu ý G1 và G2 tương quan mạnh với G3.
- Lưu ý về ngoại suy: dữ liệu không đại diện sinh viên đại học Việt Nam. Chỉ dùng để thử quy trình nếu GVHD chấp thuận.

## Cách lấy dữ liệu
Tải `student.zip` từ trang UCI ở trên, giải nén và đặt `student-por.csv` vào `data/raw/`. Tệp CSV dùng dấu chấm phẩy (`;`). Không sửa dữ liệu gốc; ghi lại mọi bước xử lý.

## Cách ghi nguồn trong báo cáo
Ghi trích dẫn UCI trong tài liệu tham khảo và mô tả nguồn, giấy phép, đối tượng, số quan sát, biến, ngưỡng nhãn, cùng giới hạn ngoại suy trong phần dữ liệu/phương pháp.