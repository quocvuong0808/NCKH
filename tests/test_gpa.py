import unittest
import sys
from pathlib import Path
from decimal import Decimal
import pandas as pd
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from gpa import convert_score, classify_gpa, analyze_semester, semester_feedback

class GPATests(unittest.TestCase):
    def data(self):
        return pd.DataFrame({"hoc_ky": ["HK1"]*3, "ma_mon": ["A1", "B1", "F1"], "ten_mon": ["Programming", "Math", "English"], "so_tin_chi": [3, 2, 1], "diem_he10": [8.5, 7, 3.9]})

    def test_conversion_boundaries_and_rounding(self):
        for score, letter, points in [(0,"F",0),(3.9,"F",0),(4,"D",1),(5.4,"D",1),(5.5,"C",2),(6.9,"C",2),(7,"B",3),(8.4,"B",3),(8.5,"A",4),(10,"A",4),(8.45,"A",4),(3.95,"D",1)]:
            with self.subTest(score=score):
                self.assertEqual(convert_score(score)[1:], (letter,points))

    def test_all_rank_boundaries(self):
        for score, rank in [(4,"Xuất sắc"),(3.6,"Xuất sắc"),(3.5999,"Giỏi"),(3.2,"Giỏi"),(3.1999,"Khá"),(2.5,"Khá"),(2.4999,"Trung bình"),(2,"Trung bình"),(1.9999,"Yếu"),(1,"Yếu"),(.9999,"Kém"),(0,"Kém")]:
            self.assertEqual(classify_gpa(score), rank)

    def test_weighted_and_failed_in_denominator(self):
        table, info = analyze_semester(self.data())
        self.assertEqual(info["gpa"], 3.0)
        self.assertEqual(info["tong_tin_chi_gpa"], 6)
        self.assertEqual(info["tin_chi_khong_dat"], 1)
        self.assertEqual(info["xep_loai"], "Khá")
        self.assertEqual(table.iloc[2].diem_he4, 0)
        strengths, actions, msg = semester_feedback(table, info)
        self.assertIn("Programming", strengths)
        self.assertIn("English", actions[0])

    def test_exclusions_and_no_eligible(self):
        for kind in ["P", "I", "X", "R", "NGOAI_CT"]:
            data = self.data()
            data["loai"] = ["TINH_GPA", "TINH_GPA", kind]
            data.loc[2, "diem_he10"] = 5 if kind == "P" else None
            _, info = analyze_semester(data)
            self.assertEqual(info["gpa"], 3.6)
            self.assertEqual(info["tong_tin_chi_gpa"], 5)
        data["loai"] = "X"
        data["diem_he10"] = None
        _, info = analyze_semester(data)
        self.assertIsNone(info["gpa"])
        self.assertEqual(info["xep_loai"], "Chưa đủ dữ liệu")

    def test_reject_invalid(self):
        for col, value in [("so_tin_chi",0),("so_tin_chi",-1),("so_tin_chi",1.5),("diem_he10",None),("diem_he10",11),("diem_he10",float("inf")),("ma_mon","")]:
            data = self.data().astype(object)
            data.loc[0,col] = value
            with self.subTest(col=col,value=value), self.assertRaises(ValueError):
                analyze_semester(data)
        data=self.data()
        data.loc[1,"ma_mon"]="A1"
        with self.assertRaises(ValueError): analyze_semester(data)
        data=self.data()
        data.loc[1,"hoc_ky"]="HK2"
        with self.assertRaises(ValueError): analyze_semester(data)

    def test_course_analysis_independent_of_other_scores(self):
        data=self.data()
        before,_=analyze_semester(data)
        data.loc[1,"diem_he10"]=0
        after,_=analyze_semester(data)
        self.assertEqual(before.iloc[0].diem_chu,after.iloc[0].diem_chu)
        self.assertEqual(before.iloc[0].goi_y,after.iloc[0].goi_y)
