"""Checks the published EXP-0014 report-derived index."""
from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tools.check_exp0014_index import INDEX, SRC, canonical_source, validate  # noqa: E402


class Exp0014IndexTests(unittest.TestCase):
    def test_current_report_index_agree(self) -> None:
        self.assertTrue(validate(SRC.read_bytes(), json.loads(INDEX.read_text(encoding="utf-8"))))

    def test_source_digest_is_independent_of_checkout_line_endings(self) -> None:
        source = b"first line\nsecond line\n"
        self.assertEqual(canonical_source(source), canonical_source(source.replace(b"\n", b"\r\n")))


if __name__ == "__main__":
    unittest.main()
