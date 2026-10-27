import csv
import hashlib
import json
import unittest

from tools import export_function_coverage


class FunctionCoverageExportTests(unittest.TestCase):
    def test_checked_in_export_is_reproducible_from_published_inputs(self):
        manifest, csv_bytes = export_function_coverage.build_export()
        manifest_path = export_function_coverage.ROOT / export_function_coverage.OUTPUT_JSON
        csv_path = export_function_coverage.ROOT / export_function_coverage.OUTPUT_CSV

        self.assertEqual(json.loads(manifest_path.read_text(encoding="utf-8")), manifest)
        self.assertEqual(csv_path.read_bytes(), csv_bytes)
        self.assertEqual(72437, manifest["measurements"]["denominator"])
        self.assertEqual(
            {"L0": 72383, "L1": 50, "L2": 4},
            manifest["measurements"]["portable_highest_known_level"],
        )
        self.assertEqual(["L3", "L4"], manifest["measurements"]["unpublished_levels"])
        self.assertEqual(hashlib.sha256(csv_bytes).hexdigest(), manifest["per_function_export"]["sha256"])

    def test_per_function_export_has_exact_denominator_and_scope_labels(self):
        manifest_path = export_function_coverage.ROOT / export_function_coverage.OUTPUT_JSON
        csv_path = export_function_coverage.ROOT / export_function_coverage.OUTPUT_CSV
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        with csv_path.open("r", encoding="utf-8", newline="") as stream:
            rows = list(csv.DictReader(stream))
        self.assertEqual(manifest["measurements"]["denominator"], len(rows))
        self.assertTrue(all(row["connectivity_axis"] == "not_exported" for row in rows))
        self.assertTrue(all(row["runtime_axis"] == "not_exported" for row in rows))
        self.assertEqual(4, sum(row["highest_portable_evidence_level"] == "L2" for row in rows))


if __name__ == "__main__":
    unittest.main()
