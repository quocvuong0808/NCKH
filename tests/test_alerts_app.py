import sys
import unittest
from pathlib import Path
from unittest.mock import patch
from streamlit.testing.v1 import AppTest
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"src"))
class AlertAppTests(unittest.TestCase):
    def test_pasted_csv_flags_and_updates(self):
        with patch("auth_ui.require_login",return_value="test@example.com"):
            app=AppTest.from_file(str(ROOT/"app/app.py")).run(timeout=30)
            app.radio(key="gpa_entry").set_value("Dán CSV điểm học phần").run(timeout=30)
            csv="hoc_ky,ma_mon,ten_mon,so_tin_chi,diem_he10\nHK1 2026-2027,IT1,Programming,3,3.5\nHK1 2026-2027,MA1,Math,2,5.0\n"
            app.text_area(key="paste_gpa_HK1 2026-2027").set_value(csv).run(timeout=30)
            self.assertEqual(len(app.exception),0)
            result=app.dataframe[0].value
            self.assertEqual(result.muc_canh_bao.tolist(),[2,1])
            self.assertTrue(any("IT1" in item.value for item in app.error))
            csv=csv.replace(",3,3.5",",3,8.5")
            app.text_area(key="paste_gpa_HK1 2026-2027").set_value(csv).run(timeout=30)
            self.assertEqual(len(app.exception),0)
            self.assertEqual(app.dataframe[0].value.muc_canh_bao.tolist(),[0,1])
