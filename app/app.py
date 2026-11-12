from pathlib import Path
import io
import json
import sys
import joblib
import pandas as pd
import streamlit as st
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from core import FEATURES, analyze_courses, save_feedback
from auth_ui import require_login
from alerts import style_alert_rows
from gpa import SOURCE, KINDS, analyze_semester, semester_feedback

def show_course_alerts(table):
    red = table[table.muc_canh_bao == 2]
    amber = table[table.muc_canh_bao == 1]
    if not red.empty:
        st.error("🔴 Điểm thấp cần ưu tiên: " + "; ".join(red.ma_mon + " · " + red.ten_mon))
    if not amber.empty:
        st.warning("🟠 Môn cần chú ý: " + "; ".join(amber.ma_mon + " · " + amber.ten_mon))
    st.caption("Dấu màu là nhắc nhở theo quy tắc điểm của ứng dụng, không phải quyết định cảnh báo học vụ của trường. Đỏ: hệ 10 < 4 hoặc hệ 4 < 2; cam: hệ 10 từ 4 đến dưới 5,5 hoặc hệ 4 từ 2 đến dưới 2,5. Các ngưỡng hệ 4 theo dõi riêng, không phải quy đổi tuyến tính từ hệ 10. GPA dùng điểm học phần sau làm tròn; theo dõi trong kỳ dùng điểm tại mốc đang chọn.")


st.set_page_config(page_title="UTH | Theo dõi học tập", page_icon="🎓", layout="wide")
st.markdown("""<style>
:root {--uth:#008789;--ink:#353044;}
.stApp {background:#fff;color:var(--ink);}
[data-testid="stHeader"] {background:rgba(255,255,255,.96);}
[data-testid="stSidebar"] {background:#f6f7f9;border-right:1px solid #e5e7eb;}
h1,h2,h3 {color:var(--ink)!important;}
[data-testid="stMainBlockContainer"] {padding-top:2rem;max-width:1450px;}
.uth-header {display:flex;align-items:center;gap:24px;padding:8px 0 24px;border-bottom:1px solid #e2e6e8;margin-bottom:30px;}
.uth-wordmark {font-family:Georgia,serif;font-weight:bold;font-size:56px;color:#008789;letter-spacing:-3px;line-height:1;}
.uth-school {font-size:17px;font-weight:700;line-height:1.5;}
.uth-sub {font-size:12px;color:#76818a;font-weight:400;letter-spacing:.8px;}
.hero {background:#f0f9f8;border:1px solid #d3e9e7;border-radius:20px;padding:26px 30px;margin-bottom:24px;}
.hero h1 {font-size:30px;margin:4px 0 10px;}
.hero p {color:#63747c;margin:0;line-height:1.7;}
.eyebrow {color:#008789;font-weight:700;font-size:12px;letter-spacing:1.5px;}
[data-testid="stMetric"] {background:#fff;border:1px solid #e0e6e8;border-radius:16px;padding:20px;}
[data-testid="stMetricValue"] {color:#008789;}
.stButton>button[kind="primary"] {background:#008789;border-color:#008789;border-radius:9px;}
.stDownloadButton>button {border:1px solid #008789;color:#007879;border-radius:9px;}
button[data-baseweb="tab"] {font-weight:600;}
button[aria-selected="true"][data-baseweb="tab"] {color:#008789;}
[data-baseweb="tab-highlight"] {background:#008789;}
.footer {border-top:4px solid #008789;margin-top:40px;padding:20px 0;color:#7c878d;font-size:12px;}
@media(max-width:640px) {.uth-header{gap:14px}.uth-wordmark{font-size:40px}.uth-school{font-size:13px}.hero{padding:20px}.hero h1{font-size:24px}}
</style>""", unsafe_allow_html=True)
st.markdown('<div class="uth-header"><div class="uth-wordmark">UTH</div><div class="uth-school">TRƯỜNG ĐẠI HỌC GIAO THÔNG VẬN TẢI<br>THÀNH PHỐ HỒ CHÍ MINH<div class="uth-sub">HỆ THỐNG HỖ TRỢ THEO DÕI HỌC TẬP · ĐỒ ÁN NCKH</div></div></div>', unsafe_allow_html=True)
st.markdown('<div class="hero"><div class="eyebrow">KHÔNG GIAN HỌC TẬP</div><h1>Theo dõi tiến độ, chủ động cải thiện</h1><p>Xem điểm, nhận biết thay đổi và lên kế hoạch học tập phù hợp với bạn.</p></div>', unsafe_allow_html=True)
require_login()
with st.sidebar:
    st.markdown("### Tổng quan học tập")
    st.caption("Theo dõi từng môn trong một học kỳ")
    semester = st.text_input("Học kỳ", value="HK1 2026-2027").strip()
    stage = st.radio("Mốc dữ liệu đã có", ["G1", "G2"], format_func=lambda x: {"G1": "Lần đánh giá 1 · G1", "G2": "Lần đánh giá 2 · G2"}[x])
    scale = st.selectbox("Thang điểm", [10, 4], format_func=lambda x: f"Thang điểm {x}")
    st.divider()
    st.markdown("**Hướng dẫn nhanh**")
    st.caption("1. Chọn thang điểm và mốc đánh giá.\n2. Nhập điểm hoặc tải CSV.\n3. Xem kết quả và gợi ý.")
    st.caption("G1/G2 và lựa chọn thang điểm chỉ áp dụng cho tab theo dõi trong kỳ. Tab GPA dùng điểm học phần chính thức hệ 10 và số tín chỉ.")

tab1, gpa_tab, tab2, tab3 = st.tabs(["Theo dõi từng môn", "GPA & tổng kết học kỳ", "Thang điểm & nghiên cứu", "Góp ý hệ thống"])
with tab1:
    st.subheader("Các môn học trong học kỳ")
    st.caption("Mỗi dòng là một môn của bạn. Kết quả, thay đổi điểm và gợi ý được tính độc lập cho từng môn; không tính tổng điểm hoặc GPA học kỳ.")
    dataset_key = f"courses_{semester}_{stage}_{scale}"
    left, right = st.columns([2, 1], gap="large")
    data = None
    with left:
        mode = st.radio("Cách nhập", ["Thêm / cập nhật từng môn", "Tải CSV", "Dán CSV"], horizontal=True)
        if mode == "Thêm / cập nhật từng môn":
            with st.form(f"input_{stage}_{scale}"):
                course_code = st.text_input("Mã môn", placeholder="Ví dụ: IT101", key="course_code")
                course_name = st.text_input("Tên môn", placeholder="Ví dụ: Lập trình C/C++", key="course_name")
                values = {col: st.number_input(f"Điểm {col} / {scale}", min_value=0.0, max_value=float(scale), value=round(scale * .7, 2), step=0.1, format="%.2f", key=f"grade_{stage}_{scale}_{col}") for col in FEATURES[stage]}
                submitted = st.form_submit_button("Lưu và phân tích môn", type="primary")
            if submitted:
                row = pd.DataFrame([{"hoc_ky": semester, "ma_mon": course_code.strip(), "ten_mon": course_name.strip(), **values}])
                old = st.session_state.get(dataset_key, pd.DataFrame(columns=row.columns))
                old = old[~old["ma_mon"].eq(course_code.strip())]
                data = pd.concat([old, row], ignore_index=True)
        elif mode == "Tải CSV":
            upload = st.file_uploader(f"CSV danh sách môn · hệ {scale}", type="csv", key=f"upload_{stage}_{scale}_{semester}")
            if upload:
                try:
                    data = pd.read_csv(io.BytesIO(upload.getvalue()), sep=None, engine="python", dtype={"hoc_ky": str, "ma_mon": str, "ten_mon": str})
                except Exception as exc:
                    st.error(f"Không đọc được CSV: {exc}")
        else:
            csv_text = st.text_area("Dán CSV danh sách môn", key=f"paste_courses_{stage}_{scale}_{semester}", height=160)
            if csv_text.strip():
                try:
                    data = pd.read_csv(io.StringIO(csv_text), sep=None, engine="python", dtype={"hoc_ky": str, "ma_mon": str, "ten_mon": str})
                except Exception as exc:
                    st.error(f"Không đọc được CSV: {exc}")
    with right:
        with st.container(border=True):
            st.markdown("#### Mẫu danh sách môn")
            sample = pd.DataFrame({"hoc_ky": [semester, semester], "ma_mon": ["IT101", "MA101"], "ten_mon": ["Lập trình C/C++", "Toán cao cấp"], **{col: [round(scale * .8, 2), round(scale * .6, 2)] for col in FEATURES[stage]}})
            st.code(sample.to_csv(index=False), language="text")
            st.download_button("Tải CSV mẫu", sample.to_csv(index=False).encode("utf-8-sig"), f"mau_mon_he{scale}_{stage}.csv", "text/csv")
            st.caption("CSV của một người học; bắt buộc hoc_ky, ma_mon, ten_mon và điểm. Mã môn không trùng trong cùng học kỳ. Điểm chưa có thì chọn mốc G1 thay vì điền 0. Một tệp dùng cùng thang điểm.")
    if data is not None:
        try:
            analyze_courses(data, stage, scale)
            st.session_state[dataset_key] = data.reset_index(drop=True)
        except ValueError as exc:
            st.error(str(exc) + " Dữ liệu mới chưa được lưu.")
    saved = st.session_state.get(dataset_key)
    if saved is not None and not saved.empty:
        all_results = analyze_courses(saved, stage, scale)
        result = all_results[all_results.hoc_ky == semester]
        if result.empty:
            st.info("Tệp không có môn thuộc học kỳ đang chọn. Đổi học kỳ ở thanh bên hoặc kiểm tra cột hoc_ky.")
        else:
            st.divider()
            st.subheader(f"Danh sách môn · {semester}")
            show_course_alerts(result)
            st.dataframe(style_alert_rows(result), width="stretch", hide_index=True)
            selected_code = st.selectbox("Xem phân tích riêng một môn", result.ma_mon.tolist(), key="selected_course", format_func=lambda code: f"{code} · {result.loc[result.ma_mon == code, 'ten_mon'].iloc[0]}")
            course = result[result.ma_mon == selected_code].iloc[0]
            st.markdown("#### " + course.ten_mon)
            cols = st.columns(3)
            cols[0].metric("Điểm G1 của môn", f"{course.G1:.2f} / {scale}")
            if stage == "G2":
                cols[1].metric("Điểm G2 của môn", f"{course.G2:.2f} / {scale}", delta=f"{course.chenh_lech:+.2f}")
            else:
                cols[1].metric("Xu hướng", "Chưa đủ dữ liệu")
            cols[2].metric("Xếp loại điểm hiện tại", course[f"xep_loai_{stage}"] if scale == 4 else "Chưa quy đổi")
            st.info(course.goi_y)
            points = pd.DataFrame({"Lần đánh giá": FEATURES[stage], "Điểm môn học": [course[col] for col in FEATURES[stage]]}).set_index("Lần đánh giá")
            st.bar_chart(points, color="#008789")
            st.caption("Biểu đồ chỉ gồm các điểm của môn đang chọn. Chênh lệch giữa hai bài không khẳng định sa sút vì có thể khác nội dung và độ khó. Chưa dự báo kết quả cuối môn khi chưa có dữ liệu phù hợp.")
            st.download_button("Tải phân tích từng môn", result.to_csv(index=False).encode("utf-8-sig"), f"phan_tich_mon_he{scale}.csv", "text/csv")
            if st.button("Xóa môn đang chọn khỏi danh sách phiên này"):
                st.session_state[dataset_key] = saved[~((saved.hoc_ky == semester) & (saved.ma_mon == selected_code))].reset_index(drop=True)
                st.rerun()
        st.caption("Danh sách nhập tay được giữ trong phiên trình duyệt, tách theo học kỳ, mốc và thang điểm. Đổi mốc chưa tự chuyển dữ liệu. Hãy tải CSV để lưu lại trước khi đóng phiên.")
    else:
        st.info("Chưa có môn học. Thêm lần lượt các môn hoặc tải danh sách CSV để bắt đầu.")
with gpa_tab:
    st.subheader(f"GPA và học lực · {semester}")
    st.caption("Từng môn được phân tích riêng; tổng kết học kỳ dùng điểm học phần chính thức và trọng số tín chỉ theo bảng cơ bản của Thông tư 08/2021/TT-BGDĐT.")
    st.info("Không nhập điểm thi cuối kỳ đơn lẻ hoặc G1/G2 vào đây. Nhập điểm học phần đã tổng hợp các thành phần theo đề cương. Đây là GPA học kỳ, không phải GPA tích lũy hoặc xếp hạng tốt nghiệp.")
    key = f"official_courses_{semester}"
    gpa_data = None
    entry = st.radio("Nhập điểm chính thức", ["Thêm / cập nhật môn học", "Tải CSV điểm học phần", "Dán CSV điểm học phần"], horizontal=True, key="gpa_entry")
    if entry == "Thêm / cập nhật môn học":
        with st.form("gpa_form"):
            c1, c2 = st.columns(2)
            code = c1.text_input("Mã môn", key="gpa_code")
            name = c2.text_input("Tên môn", key="gpa_name")
            credits = c1.number_input("Số tín chỉ", min_value=1, max_value=100, value=3, step=1, key="gpa_credits")
            score = c2.number_input("Điểm học phần hệ 10", min_value=0.0, max_value=10.0, value=7.0, step=0.1, format="%.2f", key="gpa_score")
            kind = st.selectbox("Loại học phần / trạng thái", KINDS, format_func=lambda x: {"TINH_GPA": "Tính GPA · điểm A/B/C/D/F", "P": "P · đạt không phân mức, không tính GPA", "I": "I · điểm chưa hoàn thiện do hoãn", "X": "X · chưa đủ dữ liệu", "R": "R · miễn học, công nhận tín chỉ", "NGOAI_CT": "Ngoài yêu cầu chương trình đào tạo"}[x], key="gpa_kind")
            st.caption("Với I/X/R/NGOAI_CT, ô điểm được bỏ qua. Với P, nhập điểm từ 5,0 trở lên. Môn F vẫn tính vào GPA với điểm hệ 4 bằng 0.")
            submit = st.form_submit_button("Lưu điểm học phần", type="primary")
        if submit:
            row = pd.DataFrame([{"hoc_ky": semester, "ma_mon": code.strip(), "ten_mon": name.strip(), "so_tin_chi": credits, "diem_he10": score if kind in ["TINH_GPA", "P"] else None, "loai": kind}])
            old = st.session_state.get(key, pd.DataFrame(columns=row.columns))
            old = old[~old.ma_mon.eq(code.strip())]
            gpa_data = pd.concat([old, row], ignore_index=True)
    elif entry == "Tải CSV điểm học phần":
        uploaded = st.file_uploader("CSV điểm chính thức và tín chỉ", type="csv", key=f"gpa_upload_{semester}")
        if uploaded:
            try:
                gpa_data = pd.read_csv(io.BytesIO(uploaded.getvalue()), sep=None, engine="python", dtype={"hoc_ky": str, "ma_mon": str, "ten_mon": str})
                if "hoc_ky" not in gpa_data:
                    raise ValueError("Thiếu cột hoc_ky.")
                if not gpa_data.hoc_ky.astype(str).str.strip().eq(semester).all():
                    raise ValueError("CSV phải chỉ chứa học kỳ đang chọn ở thanh bên.")
            except Exception as exc:
                st.error(f"Không đọc được danh sách: {exc}")
                gpa_data = None
    else:
        csv_text = st.text_area("Dán CSV điểm học phần", height=180, key=f"paste_gpa_{semester}")
        if csv_text.strip():
            try:
                gpa_data = pd.read_csv(io.StringIO(csv_text), sep=None, engine="python", dtype={"hoc_ky": str, "ma_mon": str, "ten_mon": str})
                if "hoc_ky" not in gpa_data or not gpa_data.hoc_ky.astype(str).str.strip().eq(semester).all():
                    raise ValueError("CSV phải có hoc_ky và chỉ chứa học kỳ đang chọn.")
            except Exception as exc:
                st.error(f"Không đọc được CSV: {exc}")
                gpa_data = None
    with st.expander("CSV mẫu và hướng dẫn", expanded=False):
        sample = pd.DataFrame({"hoc_ky": [semester] * 3, "ma_mon": ["IT101", "MA101", "EN101"], "ten_mon": ["Lập trình C/C++", "Toán cao cấp", "Tiếng Anh"], "so_tin_chi": [3, 2, 2], "diem_he10": [8.5, 7, 5.5], "loai": ["TINH_GPA"] * 3})
        st.code(sample.to_csv(index=False), language="text")
        st.download_button("Tải CSV mẫu GPA", sample.to_csv(index=False).encode("utf-8-sig"), "mau_gpa_hoc_ky.csv", "text/csv")
        st.caption("loai có thể bỏ cột hoặc để trống: mặc định TINH_GPA. P/I/X/R/NGOAI_CT không tính vào GPA. Dòng TINH_GPA thiếu điểm sẽ bị từ chối, không tự gán 0. Chỉ nhập một điểm chính thức cho mỗi mã môn; không nhập lặp các lần học lại. CSV dùng dấu chấm cho số thập phân.")
    if gpa_data is not None:
        try:
            analyze_semester(gpa_data)
            st.session_state[key] = gpa_data.reset_index(drop=True)
        except ValueError as exc:
            st.error(str(exc) + " Danh sách mới chưa được lưu.")
    official = st.session_state.get(key)
    if official is not None and not official.empty:
        table, summary = analyze_semester(official)
        complete = st.checkbox("Tôi đã nhập đủ các học phần thuộc học kỳ này và kiểm tra điểm chính thức", key=f"complete_{semester}_{int(pd.util.hash_pandas_object(official.fillna('').astype(str), index=True).sum())}")
        heading = "Tổng kết trên danh sách đã nhập" if complete and not summary["so_mon_chua_hoan_thien"] else "GPA tạm tính trên danh sách đã nhập"
        st.markdown("#### " + heading)
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("GPA hệ 4", f"{summary['gpa']:.3f}" if summary["gpa"] is not None else "Chưa có")
        c2.metric("Xếp loại học lực", summary["xep_loai"])
        c3.metric("Tín chỉ tính GPA", summary["tong_tin_chi_gpa"])
        c4.metric("Tín chỉ chưa đạt (F)", summary["tin_chi_khong_dat"])
        st.caption("GPA = Σ(điểm hệ 4 từng môn × số tín chỉ) / Σ(tín chỉ tính GPA). Xếp loại theo giá trị chưa làm tròn; GPA hiển thị 3 chữ số thập phân. Kết quả sát ngưỡng cần xem giá trị đầy đủ bên dưới.")
        target = summary["muc_tieu_gpa_tiep_theo"]
        if target:
            st.write(f"Mức tiếp theo: **{target['xep_loai']}** từ **{target['gpa']:.1f}/4** · khoảng cách hiện tại **{target['khoang_cach']:.4f} GPA**.")
        elif summary["gpa"] is not None:
            st.write("Bạn đang ở mức Xuất sắc. Hãy duy trì các môn mạnh và hỗ trợ thêm cho môn còn thấp nếu có.")
        if summary["so_mon_chua_hoan_thien"]:
            st.warning(f"Còn {summary['so_mon_chua_hoan_thien']} môn I/X chưa hoàn thiện. Đây chưa phải tổng kết đầy đủ của học kỳ.")
        strengths, actions, message = semester_feedback(table, summary)
        if summary["gpa"] is not None and summary["gpa"] >= 3.2:
            st.success(message)
        else:
            st.info(message)
        st.markdown("##### Điểm mạnh theo kết quả môn học")
        st.write(strengths)
        st.markdown("##### Nội dung cần cải thiện và kế hoạch")
        if actions:
            for i, action in enumerate(actions, 1):
                st.write(f"{i}. {action}")
        else:
            st.write("Chưa có môn C/D/F trong danh sách. Tiếp tục duy trì lịch học và luyện tập nâng cao.")
        st.caption("Nhận xét dựa trên điểm, không kết luận về năng lực hay nguyên nhân cá nhân. Ưu tiên môn F, sau đó D/C và môn nhiều tín chỉ. Gợi ý học cải thiện phải đối chiếu quy định trường.")
        show_course_alerts(table)
        st.dataframe(style_alert_rows(table), hide_index=True, width="stretch")
        chosen = st.selectbox("Chi tiết và mục tiêu từng môn", table.ma_mon.tolist(), key=f"gpa_selected_{semester}", format_func=lambda code: f"{code} · {table.loc[table.ma_mon == code, 'ten_mon'].iloc[0]}")
        course = table[table.ma_mon == chosen].iloc[0]
        st.write(f"**{course.ten_mon}** · {course.so_tin_chi} tín chỉ · Điểm chữ {course.diem_chu}")
        st.write(course.goi_y)
        if course.tinh_gpa:
            st.write(f"Mục tiêu tham khảo: {course.muc_tieu_mon}.")
            st.caption(f"Nếu môn này tăng lên một bậc điểm chữ và tín chỉ, các điểm khác được giữ nguyên: GPA tăng khoảng {course.muc_tang_gpa_gia_dinh:.3f}. Đây là kịch bản giả định, không phải dự đoán hay cam kết được học cải thiện.")
        st.download_button("Tải phân tích môn và gợi ý", table.to_csv(index=False).encode("utf-8-sig"), "phan_tich_gpa.csv", "text/csv")
        payload = {**summary, "pham_vi": heading, "da_xac_nhan_du_mon": complete, "nguon": SOURCE, "diem_manh": strengths, "ke_hoach": actions, "dong_vien": message}
        st.download_button("Tải tổng kết học kỳ JSON", json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8"), "tong_ket_hoc_ky.json", "application/json")
        with st.expander("Chi tiết phép tính và xếp loại"):
            st.json(summary)
        if st.button("Xóa môn đã chọn trong bảng GPA", key="gpa_delete"):
            st.session_state[key] = official[~official.ma_mon.eq(chosen)].reset_index(drop=True)
            st.rerun()
        st.caption("Dữ liệu giữ trong phiên hiện tại. Tải kết quả để lưu trước khi đóng phiên. Xếp loại này không tự động xác nhận cảnh báo học vụ hoặc xếp hạng tốt nghiệp.")
    else:
        st.info("Thêm các môn với điểm học phần và số tín chỉ để xem GPA, xếp loại và gợi ý.")
    st.markdown(f"Căn cứ: [Điều 9–10, Thông tư 08/2021/TT-BGDĐT]({SOURCE}). Đang áp dụng bảng cơ bản; quy chế UTH có thể quy định mức điểm chữ chi tiết hơn.")
with tab2:
    st.subheader("Bảng quy đổi cơ bản theo Thông tư 08/2021")
    st.table(pd.DataFrame({"Điểm học phần hệ 10 (sau làm tròn 1 chữ số)": ["8,5 – 10", "7,0 – 8,4", "5,5 – 6,9", "4,0 – 5,4", "Dưới 4,0"], "Điểm chữ": ["A", "B", "C", "D", "F"], "Điểm hệ 4": [4, 3, 2, 1, 0]}))
    st.table(pd.DataFrame({"GPA hệ 4": ["3,6 – 4,0", "3,2 – dưới 3,6", "2,5 – dưới 3,2", "2,0 – dưới 2,5", "1,0 – dưới 2,0", "Dưới 1,0"], "Học lực": ["Xuất sắc", "Giỏi", "Khá", "Trung bình", "Yếu", "Kém"]}))
    st.markdown(f"[Văn bản gốc, Điều 9–10]({SOURCE}). GPA không được tính bằng cách lấy điểm trung bình hệ 10 rồi chia 2,5. P/I/X/R và môn ngoài yêu cầu chương trình không tính GPA.")
    st.caption("Làm tròn điểm học phần một chữ số theo cách 5 tăng lên; xếp loại GPA theo giá trị chưa làm tròn. Khi sử dụng thực tế cần đối chiếu quy định chi tiết của UTH, bao gồm quy tắc học lại/cải thiện.")
    st.subheader("Bảng tùy chỉnh cũ — chỉ dùng cho theo dõi trong kỳ")
    st.caption("Áp dụng các ngưỡng bạn cung cấp cho đồ án; chưa đối chiếu với quy chế chính thức của trường.")
    st.table(pd.DataFrame({"Khoảng điểm hệ 4": ["3.50 – 4.00", "3.20 – dưới 3.50", "2.70 – dưới 3.20", "2.50 – dưới 2.70", "2.00 – dưới 2.50", "0.00 – dưới 2.00"], "Xếp loại": ["A+", "A", "B+", "B", "C", "D"]}))
    st.caption("Bảng A+/B+ phía trên không dùng để tính GPA theo Thông tư. Tab theo dõi trong kỳ giữ điểm đánh giá riêng; tab GPA nhận điểm học phần chính thức.")
    with st.expander("Báo cáo thử nghiệm trên dữ liệu UCI"):
        path = ROOT / "reports/metrics.json"
        if path.exists():
            report = json.loads(path.read_text(encoding="utf-8"))
            info = report["stages"][stage]
            st.caption("Số liệu dưới đây thuộc dữ liệu UCI gốc hệ 20, không phải kết quả đánh giá trên sinh viên UTH.")
            st.write("Mô hình chọn bằng CV:", info["selected_by_training_cv"])
            st.dataframe(pd.DataFrame(info["test_results"]).T.drop(columns=["confusion_matrix"]), width="stretch")
            st.download_button("Tải báo cáo nghiên cứu", path.read_bytes(), "metrics.json", "application/json")
        else:
            st.info("Chưa có báo cáo thử nghiệm.")
with tab3:
    st.subheader("Góp ý để cải thiện trải nghiệm")
    st.caption("Lưu phản hồi cục bộ bằng SQLite. Không nhập thông tin nhận diện cá nhân.")
    with st.form("feedback"):
        consent = st.checkbox("Tôi đồng ý lưu phản hồi để đánh giá bản thử nghiệm")
        rating = st.slider("Mức phù hợp của gợi ý", 1, 5, 3)
        comment = st.text_area("Điểm cần cải thiện", max_chars=2000)
        send = st.form_submit_button("Lưu phản hồi", type="primary")
    if send:
        if consent:
            save_feedback(ROOT / "data/feedback.sqlite3", stage, rating, f"[He {scale}] {comment}")
            st.success("Đã lưu phản hồi.")
        else:
            st.info("Cần đồng ý trước khi lưu phản hồi.")
st.markdown('<div class="footer">UTH · Đồ án nghiên cứu khoa học · Bản thử nghiệm hỗ trợ học tập, không thay thế hệ thống học vụ chính thức.</div>', unsafe_allow_html=True)
