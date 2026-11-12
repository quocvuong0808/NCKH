import sys
import unittest
from pathlib import Path
import pandas as pd
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"src"))
from alerts import attach_alerts
from core import analyze_courses
from gpa import analyze_semester

class AlertTests(unittest.TestCase):
    def test_exact_thresholds(self):
        for scale, scores in [(10,[3.9,4,5.4,5.5]),(4,[1.9,2,2.4,2.5])]:
            result=attach_alerts(pd.DataFrame({"score":scores}),"score",scale)
            self.assertEqual(result.muc_canh_bao.tolist(),[2,1,1,0])
    def test_official_rounding_and_exclusions(self):
        data=pd.DataFrame({"hoc_ky":["HK1"]*4,"ma_mon":["A","B","C","D"],"ten_mon":["A","B","C","D"],"so_tin_chi":[3]*4,"diem_he10":[3.9,3.95,5.45,None],"loai":["TINH_GPA"]*3+["X"]})
        result,_=analyze_semester(data)
        self.assertEqual(result.muc_canh_bao.tolist(),[2,1,0,-1])
    def test_recompute_on_update(self):
        data=pd.DataFrame({"hoc_ky":["HK1"],"ma_mon":["IT1"],"ten_mon":["Programming"],"G1":[3.0]})
        self.assertEqual(analyze_courses(data,"G1",10).iloc[0].muc_canh_bao,2)
        data.loc[0,"G1"]=8
        self.assertEqual(analyze_courses(data,"G1",10).iloc[0].muc_canh_bao,0)
