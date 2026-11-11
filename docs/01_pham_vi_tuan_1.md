# Phạm vi nghiên cứu dự thảo

## Hướng nghiên cứu
Dùng dữ liệu điểm theo giai đoạn để đánh giá khả năng nhận diện trường hợp có điểm cuối kỳ thấp. Hướng này chỉ được gọi là dự báo khi biến đầu vào được ghi nhận trước kết quả cuối kỳ.

## Câu hỏi nghiên cứu
1. Điểm giai đoạn trước và các đặc trưng có sẵn giúp nhận diện nguy cơ điểm cuối kỳ thấp đến mức nào?
2. Logistic Regression và Decision Tree có cải thiện so với baseline dự đoán lớp đa số không?
3. Các mô hình bỏ sót bao nhiêu trường hợp điểm thấp và tạo ra bao nhiêu cảnh báo sai?

## Dữ liệu đề xuất cho bản thử nghiệm
UCI Student Performance, ưu tiên tệp Portuguese (`student-por.csv`), gồm hồ sơ học sinh trung học ở hai trường tại Bồ Đào Nha. Có G1 (điểm kỳ 1), G2 (điểm kỳ 2), G3 (điểm cuối năm), thang 0–20. UCI mô tả 649 quan sát, 30 đặc trưng, không có giá trị thiếu; giấy phép CC BY 4.0. Nguồn và trích dẫn trong `docs/06_nguon_du_lieu.md`.

**Giới hạn phạm vi:** Bộ dữ liệu là học sinh trung học Bồ Đào Nha, không phải sinh viên năm nhất ngành Hệ thống Thông tin Quản lý tại Việt Nam. Vì vậy đây là dữ liệu thử nghiệm phương pháp và dashboard, không đủ để kết luận mô hình áp dụng được cho sinh viên đại học Việt Nam. Nếu đề tài bắt buộc đúng đối tượng ban đầu, cần thay bằng dữ liệu đại học phù hợp trước khi báo cáo kết quả như phát hiện chính.

## Thiết kế dự đoán ban đầu
- Mốc dự đoán: sau kỳ 2, khi G2 đã có; mục tiêu là G3.
- Nhãn nhị phân: `G3 < 10` trên thang 0–20 (tương đương dưới 5/10). Nhóm cần xác nhận ngưỡng này với GVHD và quy định đánh giá phù hợp; giữ G3 liên tục để có thể phân tích thêm.
- Không dùng G3 làm đầu vào. G1/G2 là biến trước thời điểm dự đoán, nhưng G2 tương quan mạnh với G3 theo ghi chú UCI; báo cáo rõ đây là kịch bản dự đoán cuối giai đoạn, không phải cảnh báo sớm từ đầu năm.
- Baseline: DummyClassifier theo lớp đa số. Mô hình: Logistic Regression và Decision Tree, tiền xử lý trong Pipeline.
- Chia train/test phân tầng 80/20 với seed cố định. UCI không cung cấp mã định danh học sinh, nên không thể kiểm tra trùng lặp cá nhân hoặc chia theo nhóm; nêu đây là hạn chế.
- Báo cáo precision, recall, F1, confusion matrix; ROC-AUC nếu hai lớp có mặt trong tập kiểm tra. Quan tâm recall lớp nguy cơ và số cảnh báo sai.

## Câu hỏi cần GVHD xác nhận
1. Có chấp nhận dùng UCI làm dữ liệu thử nghiệm dù khác đối tượng sinh viên đại học không?
2. Có chấp nhận ngưỡng `G3 < 10/20` làm nhãn nguy cơ không?
3. Đề tài cần dự báo từ giữa kỳ (G1) hay chấp nhận mốc sau kỳ 2 (G2)?

## Đạo đức và cách diễn giải
Chỉ dùng dữ liệu công khai theo giấy phép và ghi công nguồn. Không xem mô hình là công cụ quyết định học vụ; điểm rủi ro chỉ phục vụ minh họa/hỗ trợ tham khảo. Không đưa ra kết luận nhân quả từ tầm quan trọng đặc trưng.