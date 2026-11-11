"""Logic dùng chung; chỉ sử dụng điểm đã có tại mốc dự đoán."""
import sqlite3
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path
import pandas as pd

FEATURES = {"G1": ["G1"], "G2": ["G1", "G2"]}

def validate(data, stage, target=False):
    required = FEATURES[stage] + (["G3"] if target else [])
    missing = sorted(set(required) - set(data.columns))
    if missing:
        raise ValueError("Thiếu cột: " + ", ".join(missing))
    if data.empty:
        raise ValueError("Tệp không có bản ghi.")
    result = data[required].copy()
    for col in required:
        values = pd.to_numeric(result[col], errors="coerce")
        if values.isna().any() or (~values.between(0, 20)).any():
            raise ValueError(f"{col}: cần điểm số từ 0 đến 20, không để trống.")
        result[col] = values
    return result

def advice(row, stage):
    reasons, actions = [], []
    if row[stage] < 10:
        reasons.append(f"Điểm {stage} dưới ngưỡng minh họa 10/20")
        actions.append("Rà soát nội dung chưa hiểu, chọn hai chủ đề để luyện tập và trao đổi với giảng viên.")
    if stage == "G2" and row["G2"] < row["G1"]:
        reasons.append("Điểm G2 thấp hơn G1; hai kỳ có thể khác độ khó")
        actions.append("So sánh các lỗi trong hai lần đánh giá và lập lịch ôn tập trong tuần.")
    if not actions:
        actions.append("Duy trì lịch học và kiểm tra tiến độ trước lần đánh giá tiếp theo.")
    return "; ".join(reasons) or "Chưa có dấu hiệu theo quy tắc điểm", " ".join(actions)

def predict(data, model, stage, threshold=0.5):
    clean = validate(data, stage)
    result = clean.copy()
    result["diem_mo_hinh_chua_hieu_chinh"] = model.predict_proba(clean)[:, list(model.classes_).index(1)]
    result["canh_bao_mo_hinh"] = result["diem_mo_hinh_chua_hieu_chinh"] >= threshold
    result["canh_bao_quy_tac"] = clean[stage] < 10
    notes = [advice(row, stage) for _, row in clean.iterrows()]
    result["dau_hieu_quan_sat"] = [x[0] for x in notes]
    result["goi_y"] = [x[1] for x in notes]
    return result

def save_feedback(path, stage, rating, comment):
    if stage not in FEATURES or rating not in range(1, 6):
        raise ValueError("Mốc hoặc mức đánh giá không hợp lệ.")
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with closing(sqlite3.connect(path)) as db, db:
        db.execute("CREATE TABLE IF NOT EXISTS feedback (created_at TEXT, stage TEXT, rating INTEGER, comment TEXT)")
        db.execute("INSERT INTO feedback VALUES (?, ?, ?, ?)", (datetime.now(timezone.utc).isoformat(), stage, rating, comment[:2000]))


def letter_grade(score):
    """Các ngưỡng do người dùng cung cấp; không quy đổi từ thang 10."""
    if not 0 <= score <= 4:
        raise ValueError("Điểm hệ 4 phải nằm trong khoảng 0–4.")
    for minimum, letter in [(3.5, "A+"), (3.2, "A"), (2.7, "B+"), (2.5, "B"), (2.0, "C")]:
        if score >= minimum:
            return letter
    return "D"


def analyze_grades(data, stage, scale):
    if scale not in (4, 10):
        raise ValueError("Chỉ hỗ trợ thang điểm 10 và 4.")
    result = validate(data, stage)
    for col in FEATURES[stage]:
        if (result[col] > scale).any():
            raise ValueError(f"{col}: điểm phải từ 0 đến {scale}.")
        if scale == 4:
            result[f"xep_loai_{col}"] = result[col].map(letter_grade)
    if stage == "G2":
        result["chenh_lech"] = result.G2 - result.G1
        result["xu_huong"] = result.chenh_lech.map(lambda x: "Tăng" if x > 0 else "Giảm" if x < 0 else "Ổn định")
    result["goi_y"] = [
        "Rà soát phần kiến thức còn yếu và trao đổi với giảng viên để lập kế hoạch ôn tập."
        if (scale == 4 and row[stage] < 2) or (stage == "G2" and row.G2 < row.G1)
        else "Duy trì kế hoạch học tập và theo dõi lần đánh giá tiếp theo."
        for _, row in result.iterrows()
    ]
    return result


def analyze_courses(data, stage, scale):
    """Một dòng = một môn của một người học trong một học kỳ."""
    keys = ["hoc_ky", "ma_mon", "ten_mon"]
    missing = [key for key in keys if key not in data.columns]
    if missing:
        raise ValueError("Thiếu cột: " + ", ".join(missing))
    identity = data[keys].copy().reset_index(drop=True)
    for key in keys:
        if identity[key].isna().any():
            raise ValueError(f"{key}: không được để trống.")
        identity[key] = identity[key].astype(str).str.strip()
        if identity[key].eq("").any():
            raise ValueError(f"{key}: không được để trống.")
    if identity.duplicated(["hoc_ky", "ma_mon"]).any():
        raise ValueError("Trùng mã môn trong cùng học kỳ. Mỗi môn chỉ có một dòng; hãy cập nhật điểm trên dòng đó.")
    grades = analyze_grades(data.reset_index(drop=True), stage, scale)
    result = pd.concat([identity, grades], axis=1)
    result["goi_y"] = [f"{name}: {note}" for name, note in zip(result.ten_mon, result.goi_y)]
    return result
