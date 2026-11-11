"""Quy đổi cơ bản Điều 9–10 TT08/2021; chưa thay thế quy chế riêng UTH."""
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
import pandas as pd

SOURCE = "https://datafiles.chinhphu.vn/cpp/files/vbpq/2021/04/08-bgd.signed.pdf"
KINDS = ["TINH_GPA", "P", "I", "X", "R", "NGOAI_CT"]
GRADE_BANDS = [(Decimal("8.5"), "A", 4), (Decimal("7"), "B", 3), (Decimal("5.5"), "C", 2), (Decimal("4"), "D", 1), (Decimal("0"), "F", 0)]
RANKS = [(Decimal("3.6"), "Xuất sắc"), (Decimal("3.2"), "Giỏi"), (Decimal("2.5"), "Khá"), (Decimal("2"), "Trung bình"), (Decimal("1"), "Yếu"), (Decimal("0"), "Kém")]

def number(value, label):
    try:
        result = Decimal(str(value))
    except (InvalidOperation, ValueError):
        raise ValueError(f"{label}: phải là số hợp lệ.") from None
    if not result.is_finite():
        raise ValueError(f"{label}: không được trống hoặc vô hạn.")
    return result

def convert_score(value):
    score = number(value, "Điểm hệ 10")
    if not 0 <= score <= 10:
        raise ValueError("Điểm hệ 10 phải từ 0 đến 10.")
    rounded = score.quantize(Decimal("0.1"), rounding=ROUND_HALF_UP)
    for threshold, letter, points in GRADE_BANDS:
        if rounded >= threshold:
            return rounded, letter, points

def classify_gpa(value):
    gpa = number(value, "GPA")
    if not 0 <= gpa <= 4:
        raise ValueError("GPA phải từ 0 đến 4.")
    return next(label for threshold, label in RANKS if gpa >= threshold)

def analyze_semester(data):
    required = ["hoc_ky", "ma_mon", "ten_mon", "so_tin_chi", "diem_he10"]
    missing = sorted(set(required) - set(data.columns))
    if missing:
        raise ValueError("Thiếu cột: " + ", ".join(missing))
    if data.empty:
        raise ValueError("Chưa có môn học để tính GPA.")
    clean = data.copy().reset_index(drop=True)
    for key in ["hoc_ky", "ma_mon", "ten_mon"]:
        if clean[key].isna().any():
            raise ValueError(f"{key}: không được trống.")
        clean[key] = clean[key].astype(str).str.strip()
        if clean[key].eq("").any():
            raise ValueError(f"{key}: không được trống.")
    if clean.hoc_ky.nunique() != 1:
        raise ValueError("Chỉ tính một học kỳ mỗi lần; không gộp điểm các học kỳ.")
    if clean.duplicated(["hoc_ky", "ma_mon"]).any():
        raise ValueError("Trùng mã môn. Chỉ nhập điểm chính thức của mỗi môn một lần, không cộng các lần học lại.")
    if "loai" not in clean:
        clean["loai"] = "TINH_GPA"
    clean["loai"] = clean["loai"].fillna("TINH_GPA").astype(str).str.strip().str.upper().replace("", "TINH_GPA")
    if not clean.loai.isin(KINDS).all():
        raise ValueError("loai chỉ nhận: " + ", ".join(KINDS))
    rows, total, weighted, weighted10, failed = [], Decimal(0), Decimal(0), Decimal(0), Decimal(0)
    for _, row in clean.iterrows():
        credits = number(row.so_tin_chi, f"Tín chỉ môn {row.ma_mon}")
        if credits <= 0 or credits != credits.to_integral_value():
            raise ValueError("Số tín chỉ phải là số nguyên dương.")
        included = row.loai == "TINH_GPA"
        # Excluded grades are explicit statuses, never zero-filled grades.
        score, letter, points = None, row.loai, None
        original = row.diem_he10
        has_score = not pd.isna(original) and str(original).strip() != ""
        if included or has_score:
            score, numeric_letter, numeric_points = convert_score(original)
            if included:
                letter, points = numeric_letter, numeric_points
        if row.loai == "P" and score is not None and score < 5:
            raise ValueError("Điểm P là loại đạt không phân mức; điểm đã nhập phải từ 5,0 sau làm tròn.")
        if included:
            total += credits
            weighted += credits * points
            weighted10 += credits * score
            if points == 0:
                failed += credits
            feedback = {
                "A": ("Điểm mạnh", "Kết quả rất tốt! Duy trì cách học đang hiệu quả, luyện bài nâng cao và chia sẻ cách ôn tập với bạn học."),
                "B": ("Điểm mạnh", "Bạn có nền tảng tốt. Giữ nhịp học đều và rà soát các lỗi để hướng tới mức A."),
                "C": ("Cần củng cố", "Đã đạt học phần nhưng còn khoảng cải thiện. Chọn hai nội dung thường sai, ôn hai buổi mỗi tuần và tự kiểm tra lại."),
                "D": ("Ưu tiên cải thiện", "Đã đạt theo mức cơ bản nhưng điểm còn thấp. Ôn lại kiến thức nền, hỏi giảng viên phần chưa hiểu; tìm hiểu quy định học cải thiện của trường."),
                "F": ("Chưa đạt", "Ưu tiên xử lý học phần chưa đạt: kiểm tra quy định học lại, trao đổi giảng viên và lập lịch ôn từng chủ đề. Kết quả hiện tại có thể cải thiện bằng kế hoạch cụ thể."),
            }
            status, advice = feedback[letter]
            next_band = {"F": (4, 1), "D": (5.5, 2), "C": (7, 3), "B": (8.5, 4)}.get(letter)
            target = f"Hướng tới {next_band[0]:g}/10" if next_band else "Duy trì từ 8,5/10"
        else:
            status, advice, target, next_band = "Không tính GPA", "Không đưa học phần này vào tử số hoặc mẫu số GPA. Với I/X, cần hoàn thiện điểm trước khi tổng kết đầy đủ.", "—", None
        rows.append({"hoc_ky": row.hoc_ky, "ma_mon": row.ma_mon, "ten_mon": row.ten_mon, "so_tin_chi": int(credits), "diem_he10": float(score) if score is not None else None, "loai": row.loai, "diem_chu": letter, "diem_he4": points, "tinh_gpa": included, "nhan_xet": status, "goi_y": advice, "muc_tieu_mon": target, "tang_diem_he4_gia_dinh": (next_band[1] - points) if next_band else 0})
    result = pd.DataFrame(rows)
    gpa = weighted / total if total else None
    result["muc_tang_gpa_gia_dinh"] = result.apply(lambda r: float(Decimal(int(r.so_tin_chi)) * int(r.tang_diem_he4_gia_dinh) / total) if total and r.tinh_gpa else 0.0, axis=1)
    result = result.drop(columns="tang_diem_he4_gia_dinh")
    summary = {"hoc_ky": clean.hoc_ky.iloc[0], "gpa": float(gpa) if gpa is not None else None, "gpa_exact": str(gpa) if gpa is not None else None, "xep_loai": classify_gpa(gpa) if gpa is not None else "Chưa đủ dữ liệu", "tong_tin_chi_gpa": int(total), "tong_diem_tin_chi": float(weighted), "trung_binh_he10": float(weighted10 / total) if total else None, "tin_chi_khong_dat": int(failed), "so_mon_khong_tinh": int((~result.tinh_gpa).sum()), "so_mon_chua_hoan_thien": int(clean.loai.isin(["I", "X"]).sum())}
    higher = [(threshold, label) for threshold, label in RANKS if gpa is not None and threshold > gpa]
    if higher:
        target, label = min(higher)
        summary["muc_tieu_gpa_tiep_theo"] = {"gpa": float(target), "xep_loai": label, "khoang_cach": float(target - gpa)}
    else:
        summary["muc_tieu_gpa_tiep_theo"] = None
    return result, summary

def semester_feedback(result, summary):
    included = result[result.tinh_gpa]
    strong = included[included.diem_chu.isin(["A", "B"])]
    weak = included[included.diem_chu.isin(["C", "D", "F"])].copy()
    weak["priority"] = weak.diem_chu.map({"F": 0, "D": 1, "C": 2})
    weak = weak.sort_values(["priority", "so_tin_chi"], ascending=[True, False])
    strengths = "; ".join(f"{r.ten_mon} ({r.diem_chu}, {r.so_tin_chi} tín chỉ)" for _, r in strong.iterrows()) or "Chưa có môn A/B trong danh sách; hãy bắt đầu bằng những mục tiêu cải thiện nhỏ."
    actions = [f"{r.ten_mon} · {r.so_tin_chi} tín chỉ · {r.muc_tieu_mon}. {r.goi_y}" for _, r in weak.iterrows()]
    if summary["gpa"] is None:
        message = "Chưa có học phần đủ điều kiện tính GPA. Hãy bổ sung điểm chính thức."
    elif summary["gpa"] >= 3.2:
        message = "Chúc mừng bạn đã đạt mức học lực tốt trên danh sách đã nhập! Duy trì cách học hiệu quả và vẫn ưu tiên xử lý các môn điểm thấp nếu có."
    elif summary["gpa"] >= 2:
        message = "Bạn có cơ sở để tiến bộ. Ưu tiên các môn chưa đạt hoặc điểm thấp, đặc biệt môn nhiều tín chỉ, rồi duy trì lịch ôn đều."
    else:
        message = "Kết quả hiện tại cần được hỗ trợ thêm. Hãy trao đổi với cố vấn học tập, chọn khối lượng học phù hợp và ưu tiên khắc phục các môn chưa đạt."
    return strengths, actions, message
