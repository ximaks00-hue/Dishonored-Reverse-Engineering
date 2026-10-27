"""Regression tests for documentation link integrity."""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tools.check_research_docs_links import check_links  # noqa: E402


class ResearchDocsLinksTests(unittest.TestCase):
    def test_local_path_and_anchor(self) -> None:
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            (root / "docs").mkdir()
            (root / "tools").mkdir()
            (root / "tools" / "a.py").write_text("print('ok')\n", encoding="utf-8")
            (root / "docs" / "sample.md").write_text(
                "[tool](../tools/a.py#L1) [web](https://example.org/test) "
                "[heading](#overview)\n", encoding="utf-8"
            )
            self.assertEqual(check_links(root), [])

    def test_missing_local_file(self) -> None:
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            (root / "docs").mkdir()
            (root / "docs" / "a.md").write_text("[missing](../tools/no.py)\n")
            failures = check_links(root)
            self.assertEqual(len(failures), 1)
            self.assertIn("missing local target", failures[0])

    def test_fenced_examples_are_not_paths(self) -> None:
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            (root / "docs").mkdir()
            fence = chr(96) * 3
            (root / "docs" / "example.md").write_text(
                chr(10).join([fence + "md", "[example](../../outside.txt)", fence])
            )
            self.assertEqual(check_links(root), [])

    def test_repo_escape(self) -> None:
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            (root / "docs").mkdir()
            (root / "docs" / "a.md").write_text("[escape](../../tools/a.py)\n")
            failures = check_links(root)
            self.assertEqual(len(failures), 1)
            self.assertIn("escapes repository", failures[0])


if __name__ == "__main__":
    unittest.main()
