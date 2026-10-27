import pathlib
import tempfile
import unittest
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "tools"))
import validate_repo

class ValidatorTests(unittest.TestCase):
    def test_current_repository(self):
        self.assertEqual([], validate_repo.check())

    def test_missing_required_files(self):
        with tempfile.TemporaryDirectory() as d:
            self.assertTrue(any("missing required file" in s for s in validate_repo.check(pathlib.Path(d))))

    def test_broken_link(self):
        with tempfile.TemporaryDirectory() as d:
            root = pathlib.Path(d)
            for item in validate_repo.REQUIRED:
                p = root / item
                p.parent.mkdir(parents=True, exist_ok=True)
                p.write_text("# OK\n")
            (root / "README.md").write_text("[missing](nothing.md)\n")
            self.assertTrue(any("broken relative link" in s for s in validate_repo.check(root)))

    def test_documented_local_only_artifacts_are_optional(self):
        with tempfile.TemporaryDirectory() as d:
            root = pathlib.Path(d)
            for item in validate_repo.REQUIRED:
                p = root / item
                p.parent.mkdir(parents=True, exist_ok=True)
                p.write_text("# OK\n")
            exp = root / "experiments" / "EXP-0001-example.md"
            exp.parent.mkdir(parents=True, exist_ok=True)
            exp.write_text(
                "[sample](../assets/extracted/sample/result.tga) "
                "[tool](../tools/ue-package-decompressor/decompress.exe)\n"
            )
            self.assertEqual([], validate_repo.check(root))

if __name__ == "__main__":
    unittest.main()
