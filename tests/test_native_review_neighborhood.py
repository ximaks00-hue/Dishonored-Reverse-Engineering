import csv
import json
import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from native_review_neighborhood import extract_neighborhood


class NativeReviewNeighborhoodTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.build = self.root / "build.md"
        self.build.write_text(
            "Build ID: `10256413`\nExecutable SHA-256: `" + "A" * 64 + "`\n",
            encoding="utf-8",
        )
        self.functions = self.root / "functions.csv"
        with self.functions.open("w", newline="", encoding="utf-8") as stream:
            writer = csv.DictWriter(stream, fieldnames=["address", "name", "size"])
            writer.writeheader()
            for address in ("00401000", "00401010", "00401020", "00401030"):
                writer.writerow({"address": address, "name": "FUN_" + address, "size": "16"})
        self.db_path = self.root / "callgraph.sqlite"
        db = sqlite3.connect(self.db_path)
        try:
            db.executescript("""
                CREATE TABLE meta (key TEXT PRIMARY KEY, value TEXT NOT NULL);
                CREATE TABLE edges (
                    id INTEGER PRIMARY KEY, kind TEXT, from_addr TEXT, to_addr TEXT,
                    from_name TEXT, to_name TEXT, site_addr TEXT
                );
            """)
            db.executemany("INSERT INTO meta VALUES (?, ?)", [
                ("build_id", "10256413"), ("exe_sha256", "A" * 64),
                ("exported_at", "2026-10-27T00:00:00Z"), ("source_csv", "edges.csv"),
            ])
            db.executemany("INSERT INTO edges VALUES (?, ?, ?, ?, ?, ?, ?)", [
                (1, "call", "00401000", "00401010", "caller", "anchor", "00401005"),
                (2, "call", "00401010", "00401020", "anchor", "callee", "00401015"),
                (3, "call", "00401020", "00401030", "callee", "far", "00401025"),
                (4, "data", "00400100", "00401010", "", "anchor", "00400100"),
            ])
            db.commit()
        finally:
            db.close()

    def tearDown(self):
        self.temp.cleanup()

    def extract(self, **kwargs):
        return extract_neighborhood(self.db_path, self.functions, self.build,
                                    ["0x00401010"], **kwargs)

    def test_includes_callers_and_callees_and_provenance(self):
        result = self.extract(max_depth=1, node_budget=10)
        self.assertEqual({node["address"] for node in result["nodes"]},
                         {"00401000", "00401010", "00401020"})
        self.assertEqual([edge["kind"] for edge in result["edges"]].count("call"), 2)
        data_edge = next(edge for edge in result["edges"] if edge["kind"] == "data")
        self.assertEqual(data_edge["interpretation"], "static_reference_only")
        self.assertEqual(data_edge["source"]["callgraph_sha256"], result["inputs"]["callgraph_sha256"])
        self.assertTrue(all(node["review_status"] == "not_changed_by_neighborhood_export"
                            for node in result["nodes"]))

    def test_depth_and_budget_are_enforced(self):
        depth_two = self.extract(max_depth=2, node_budget=10)
        self.assertIn("00401030", {node["address"] for node in depth_two["nodes"]})
        capped = self.extract(max_depth=2, node_budget=2)
        self.assertEqual(len(capped["nodes"]), 2)
        self.assertTrue(capped["truncated"])

    def test_rejects_build_mismatch(self):
        db = sqlite3.connect(self.db_path)
        try:
            db.execute("UPDATE meta SET value=? WHERE key='exe_sha256'", ("B" * 64,))
            db.commit()
        finally:
            db.close()
        with self.assertRaisesRegex(ValueError, "does not match"):
            self.extract()

    def test_rejects_unknown_anchor(self):
        with self.assertRaisesRegex(ValueError, "absent from function index"):
            extract_neighborhood(self.db_path, self.functions, self.build, ["0040FFFF"])


if __name__ == "__main__":
    unittest.main()
