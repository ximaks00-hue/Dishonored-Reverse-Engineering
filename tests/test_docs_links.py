"""Regression tests for repository-local Markdown link checks."""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tools.check_research_docs_links import check_links  # noqa: E402


class ResearchDocsLinksTests(unittest.TestCase):
    def test_existing_relative_file_with_anchor_and_external_links(self) -> None:
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            (root / "docs").mkdir()
            (root / "tools").mkdir()
            (root / "tools" / "tool.py").write_text("pass\n", encoding="utf-8")
            (root / "docs" / "guide.md").write_text(
                "[tool](../tools/tool.py#main) [web](https://example.org/x) [local](#top)\n",
                encoding="utf-8",
            )
            self.assertEqual(check_links(root), [])

    def test_missing_file_and_reference_definition(self) -> None:
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            (root / "docs").mkdir()
            (root / "docs" / "guide.md").write_text(
                "[missing](../tools/missing.py)\n[ref]: ../also-missing.md\n",
                encoding="utf-8",
            )
            failures = check_links(root)
            self.assertEqual(len(failures), 2)
            self.assertTrue(all("missing local target" in failure for failure in failures))

    def test_ignores_fenced_and_inline_code(self) -> None:
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            (root / "docs").mkdir()
            (root / "docs" / "guide.md").write_text(
                "`[inline](../../outside)`\n~~~md\n[outside](../../outside)\n~~~\n",
                encoding="utf-8",
            )
            self.assertEqual(check_links(root), [])

    def test_rejects_repository_escape(self) -> None:
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            (root / "docs").mkdir()
            (root / "docs" / "guide.md").write_text(
                "[escape](../../outside.md)\n", encoding="utf-8"
            )
            failures = check_links(root)
            self.assertEqual(len(failures), 1)
            self.assertIn("link escapes repository", failures[0])

    def test_allows_missing_documented_local_only_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            (root / "experiments").mkdir()
            (root / "experiments" / "EXP-0001.md").write_text(
                "[binary](../tools/ue-package-decompressor/decompress.exe) "
                "[output](../assets/extracted/result/data.json)\n",
                encoding="utf-8",
            )
            self.assertEqual(check_links(root), [])


if __name__ == "__main__":
    unittest.main()
