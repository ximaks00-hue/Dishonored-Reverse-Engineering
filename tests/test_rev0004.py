import json,sys,copy,unittest
from pathlib import Path
from tempfile import TemporaryDirectory
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"tools"))
import review_vtable_candidates as vt
import compare_function_indexes as idx
class ReviewTests(unittest.TestCase):
    def setUp(self):
        self.rec=json.loads((ROOT/"research/triage/EXP-0017-candidates.json").read_text(encoding="utf-8"))
    def test_report(self):
        self.assertTrue(vt.validate(self.rec))
        text=vt.report(self.rec)
        self.assertIn("488",text)
        self.assertIn("0x00CB4C48",text)
    def test_roles_are_separate(self):
        x=copy.deepcopy(self.rec)
        x["roles"]["powerwheel"]["slot_offset"]="0x560"
        with self.assertRaises(AssertionError):vt.validate(x)
    def test_report_exclusion_needs_owner(self):
        x=copy.deepcopy(self.rec)
        x["candidates"][-1]["reported_owner"]=None
        with self.assertRaises(AssertionError):vt.validate(x)
    def test_duplicate_va(self):
        x=copy.deepcopy(self.rec)
        x["candidates"][1]["table_va"]=x["candidates"][0]["table_va"]
        with self.assertRaises(AssertionError):vt.validate(x)
    def test_index_set_diff(self):
        with TemporaryDirectory() as folder:
            a,b=Path(folder)/"a.txt",Path(folder)/"b.txt"
            a.write_text("0x00401000\n0x00402000\n")
            b.write_text("0x00402000\n0x00403000\n")
            result=idx.compare(idx.load(a),idx.load(b))
            self.assertEqual(result["shared_count"],1)
            self.assertEqual(result["only_first"],["0x00401000"])
            self.assertEqual(result["only_second"],["0x00403000"])
if __name__=="__main__":unittest.main()
