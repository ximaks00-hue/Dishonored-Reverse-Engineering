import pathlib
import tempfile
import unittest
import sys
import json

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "tools"))
import validate_repo


def prepare_root(root):
    for item in validate_repo.REQUIRED:
        path = root / item
        path.parent.mkdir(parents=True, exist_ok=True)
        if path.suffix == ".json":
            path.write_text(json.dumps({"type": "object"}), encoding="utf-8")
        else:
            path.write_text("# OK\n", encoding="utf-8")

class ValidatorTests(unittest.TestCase):
    def test_current_repository(self):
        self.assertEqual([], validate_repo.check())

    def test_missing_required_files(self):
        with tempfile.TemporaryDirectory() as d:
            self.assertTrue(any("missing required file" in s for s in validate_repo.check(pathlib.Path(d))))

    def test_broken_link(self):
        with tempfile.TemporaryDirectory() as d:
            root = pathlib.Path(d)
            prepare_root(root)
            (root / "README.md").write_text("[missing](nothing.md)\n")
            self.assertTrue(any("broken relative link" in s for s in validate_repo.check(root)))

    def test_local_markdown_anchors(self):
        with tempfile.TemporaryDirectory() as d:
            root = pathlib.Path(d)
            prepare_root(root)
            (root / "README.md").write_text("[valid](docs/page.md#same-heading-1) [bad](docs/page.md#missing)\n")
            page = root / "docs/page.md"
            page.parent.mkdir(parents=True, exist_ok=True)
            page.write_text("# Same heading\n# Same heading\n\n<a id=\"explicit-anchor\"></a>\n")
            errors = validate_repo.check(root)
            self.assertTrue(any("broken local anchor 'missing'" in error for error in errors))
            self.assertFalse(any("same-heading-1" in error for error in errors))

    def test_record_id_parser_handles_slug_and_extension(self):
        self.assertEqual("FIND-0123", validate_repo.parse_record_id("FIND-0123-ai-cluster-review.md"))
        self.assertEqual("OBS-0007", validate_repo.parse_record_id("nested/OBS-0007-runtime.json"))
        self.assertIsNone(validate_repo.parse_record_id("FIND-123-ai.md"))

    def test_record_schema_enforces_kind_prefix_and_calibration(self):
        from jsonschema import Draft202012Validator

        schema = json.loads((validate_repo.ROOT / "schemas/research-record.schema.json").read_text(encoding="utf-8"))
        validator = Draft202012Validator(schema)
        record = {
            "id": "FIND-0001", "kind": "finding", "status": "inferred", "claim": "A claim",
            "scope": {"build": "test"}, "sources": [], "confidence": 0.7,
        }
        self.assertTrue(any("calibration_reference" in error.message for error in validator.iter_errors(record)))
        record["calibration_reference"] = "calibration-v1"
        self.assertEqual([], list(validator.iter_errors(record)))
        record["id"] = "OBS-0001"
        self.assertTrue(list(validator.iter_errors(record)))

    def test_documented_local_only_artifacts_are_optional(self):
        with tempfile.TemporaryDirectory() as d:
            root = pathlib.Path(d)
            prepare_root(root)
            exp = root / "experiments" / "EXP-0001-example.md"
            exp.parent.mkdir(parents=True, exist_ok=True)
            exp.write_text(
                "---\nid: EXP-0001\ntitle: Sample\nexperiment_status: planned\nclaim_status: unknown\nbuild: unknown\nquestion: Sample?\n---\n\n"
                "[sample](../assets/extracted/sample/result.tga) "
                "[tool](../tools/ue-package-decompressor/decompress.exe)\n"
            )
            self.assertEqual([], validate_repo.check(root))

if __name__ == "__main__":
    unittest.main()
