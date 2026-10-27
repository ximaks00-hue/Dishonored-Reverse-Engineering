import pathlib
import sys
import unittest

sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/"tools"))
from native_review_queue import address,rank_candidates

def candidate(addr, edges, size, methods=None):
    import json
    return {"address":addr,"name":"FUN_"+addr,"size_bytes":str(size),
            "pointer_target_edge_count":str(edges),
            "source_class_methods_json":json.dumps(methods or [{"uelib_function":"Function'Engine.X.Y'"}])}

class NativeReviewQueueTests(unittest.TestCase):
    def test_address_variants(self):
        self.assertEqual(address("0x0040cf20"),address("0040CF20"))
    def test_prioritizes_fanin_and_excludes_reviews(self):
        rows=rank_candidates([candidate("0040CF20",1,100),candidate("0040CF30",8,100),
                              candidate("0040CF40",2,100)],[{"address":"0x0040CF40"}])
        self.assertEqual([r["address"] for r in rows],["0040CF30","0040CF20"])
        self.assertTrue(all(r["review_status"]=="candidate_not_body_reviewed" for r in rows))
    def test_duplicate_fails(self):
        with self.assertRaises(ValueError):
            rank_candidates([candidate("0040CF20",1,10),candidate("0x0040cf20",1,10)],[])
    def test_invalid_method_json_fails(self):
        row=candidate("0040CF20",1,10)
        row["source_class_methods_json"]="not-json"
        with self.assertRaises(ValueError):
            rank_candidates([row],[])
    def test_negative_count_fails(self):
        with self.assertRaises(ValueError):
            rank_candidates([candidate("0040CF20",-1,10)],[])
