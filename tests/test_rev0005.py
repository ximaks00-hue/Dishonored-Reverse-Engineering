import copy
import json
import sys
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"tools"))
import validate_selection_report as rev

class ReportIndexTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.valid=json.loads((ROOT/"research/triage/EXP-0021-0022-report-index.json").read_text(encoding="utf-8"))
    def test_index(self):
        self.assertTrue(rev.validate(self.valid))
        self.assertIn("0x007CD800",rev.summarize(self.valid))
    def test_class_slots_are_independent(self):
        d=copy.deepcopy(self.valid)
        d["classes"][0]["slot_va"]="0x01161C08"
        with self.assertRaises(ValueError):rev.validate(d)
    def test_cannot_claim_movement(self):
        d=copy.deepcopy(self.valid)
        d["gameplay_position_update_confirmed"]=True
        with self.assertRaises(ValueError):rev.validate(d)
    def test_ui_conversion_cannot_be_overgeneralized(self):
        d=copy.deepcopy(self.valid)
        d["known_mappings"][0]["scope"]="Global Blink _iPower mapping"
        with self.assertRaises(ValueError):rev.validate(d)
    def test_external_count_not_measured(self):
        d=copy.deepcopy(self.valid)
        d["function_counts"]["external_number_measured"]=True
        with self.assertRaises(ValueError):rev.validate(d)
    def test_family_uniqueness(self):
        d=copy.deepcopy(self.valid)
        d["blink_family"][1]["function_va"]=d["blink_family"][0]["function_va"]
        with self.assertRaises(ValueError):rev.validate(d)
if __name__=="__main__":unittest.main()
