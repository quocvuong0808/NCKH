"""Application-level course flags, separate from official academic probation."""
import pandas as pd


def attach_alerts(data, score_column, scale, eligible=None):
    result = data.copy()
    if eligible is None:
        eligible = pd.Series(True, index=result.index)
    low, watch = (4.0, 5.5) if scale == 10 else (2.0, 2.5)
    levels, labels, reasons = [], [], []
    for index, row in result.iterrows():
        score = row[score_column]
        if not eligible.loc[index] or pd.isna(score):
            level, label, reason = -1, "⚪ Không đánh giá", "Môn không tính GPA hoặc chưa có điểm phù hợp; không gán nguy cơ thấp."
        elif score < low:
            level, label, reason = 2, "🔴 Cảnh báo điểm thấp", f"Điểm {score:g}/{scale} dưới ngưỡng {low:g}/{scale} của quy tắc ứng dụng."
        elif score < watch:
            level, label, reason = 1, "🟠 Cần chú ý", f"Điểm {score:g}/{scale} trong khoảng {low:g} đến dưới {watch:g}; nên ưu tiên củng cố."
        else:
            level, label, reason = 0, "🟢 Chưa chạm ngưỡng", f"Điểm {score:g}/{scale} không thấp hơn ngưỡng chú ý {watch:g}; vẫn theo dõi tiến độ."
        levels.append(level)
        labels.append(label)
        reasons.append(reason)
    result["muc_canh_bao"] = levels
    result["canh_bao"] = labels
    result["ly_do_canh_bao"] = reasons
    return result


def style_alert_rows(data):
    def color(row):
        background, foreground = {2: ("#fef2f2", "#991b1b"), 1: ("#fffbeb", "#92400e")}.get(row["muc_canh_bao"], ("", ""))
        return [f"background-color: {background}; color: {foreground}" if background else "" for _ in row]
    columns = ["canh_bao"] + [col for col in data.columns if col != "canh_bao"]
    return data[columns].style.apply(color, axis=1)
