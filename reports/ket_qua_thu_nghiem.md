# Kết quả thử nghiệm ngày 11/11/2026

Dữ liệu UCI student-por.csv: 649 bản ghi, 100 nhãn G3 < 10/20. Tập kiểm tra gồm 130 bản ghi, trong đó 20 trường hợp điểm thấp. Chia ngẫu nhiên phân tầng 80/20, seed 42; cùng bản ghi cho hai mốc. Mô hình được chọn bằng CV trên tập huấn luyện.

| Mốc | Phương pháp | Precision | Recall | F1 | Cảnh báo sai | Bỏ sót |
|---|---|---:|---:|---:|---:|---:|
| G1 | rule_grade_below_10 | 0.447 | 0.850 | 0.586 | 21 | 3 |
| G1 | majority | 0.000 | 0.000 | 0.000 | 0 | 20 |
| G1 | logistic | 0.447 | 0.850 | 0.586 | 21 | 3 |
| G1 | tree | 0.447 | 0.850 | 0.586 | 21 | 3 |
| G2 | rule_grade_below_10 | 0.621 | 0.900 | 0.735 | 11 | 2 |
| G2 | majority | 0.000 | 0.000 | 0.000 | 0 | 20 |
| G2 | logistic | 0.562 | 0.900 | 0.692 | 14 | 2 |
| G2 | tree | 0.545 | 0.900 | 0.679 | 15 | 2 |

Ở cả hai mốc CV chọn Logistic Regression. Tại G1, các phương pháp có cùng nhãn dự đoán trên tập kiểm tra. Tại G2, quy tắc có F1 cao hơn Logistic Regression và ít cảnh báo sai hơn với cùng Recall. Không đổi mô hình sau khi xem test để tránh biến test thành tập chọn mô hình. Đây là một lần chia dữ liệu, chưa đủ để khẳng định khác biệt có ý nghĩa thống kê.

Các kết quả này chỉ áp dụng cho thiết kế thử trên dữ liệu học sinh trung học Bồ Đào Nha. Chưa kiểm định cho sinh viên Việt Nam; chưa có khảo sát người dùng hay bằng chứng cải thiện điểm. Xem metrics.json để kiểm tra số liệu đầy đủ và SHA256 dữ liệu.