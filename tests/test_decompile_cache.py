import json
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path
from unittest.mock import patch

from mcp_servers.common import decompile_cache
from mcp_servers.common.config import build_settings


class DecompileCacheTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        ghidra_root = self.root / "ghidra"
        (ghidra_root / "support").mkdir(parents=True)
        properties = ghidra_root / "Ghidra" / "application.properties"
        properties.parent.mkdir(parents=True)
        properties.write_text(
            "application.version=12.1.2\n"
            "application.revision.ghidra=revision-a\n"
            "application.revision.ghidra.bin=revision-b\n",
            encoding="utf-8",
        )
        for component in decompile_cache._decompiler_components(ghidra_root):
            component.parent.mkdir(parents=True, exist_ok=True)
            component.write_bytes(b"decompiler component")

        self.project = self.root / "project"
        rep = self.project / "Dishonored-test.rep"
        (rep / "idata").mkdir(parents=True)
        (rep / "project.prp").write_text("project metadata", encoding="utf-8")
        (rep / "idata" / "program.db").write_bytes(b"analysis-revision-a")
        self.script = self.root / decompile_cache.DECOMPILE_SCRIPT
        self.script.parent.mkdir(parents=True)
        self.script.write_text("// deterministic test script\n", encoding="utf-8")
        self.index = self.root / "functions.csv"
        self.index.write_text("address,name\n00C0CA70,Test\n", encoding="utf-8")

        base = build_settings(self.root)
        self.settings = replace(
            base,
            root=self.root,
            ghidra_headless=ghidra_root / "support" / "analyzeHeadless.bat",
            ghidra_project=self.project,
            ghidra_project_name="Dishonored-test",
            ghidra_program="Dishonored.exe",
            functions_csv=self.index,
            decompile_cache_dir=self.root / "cache",
        )

    def tearDown(self):
        self.temp.cleanup()

    def test_cache_round_trip_requires_matching_provenance(self):
        address = "00C0CA70"
        key = decompile_cache.cache_key(address, self.settings)
        self.assertIsNotNone(key)

        with patch.object(decompile_cache, "get_settings", return_value=self.settings):
            stored = decompile_cache.store(
                address,
                {"name": "Test", "pseudocode": "int test(void) { return 1; }"},
                expected_cache_key=key,
            )
            self.assertTrue(stored["cache_stored"])
            cached = decompile_cache.load(address, expected_cache_key=key)
            self.assertTrue(cached["cache_hit"])
            self.assertEqual("int test(void) { return 1; }", cached["pseudocode"])

            changed_build = replace(self.settings, build_id="other-build")
            with patch.object(decompile_cache, "get_settings", return_value=changed_build):
                self.assertIsNone(decompile_cache.load(address))

    def test_identity_changes_with_tool_options_script_project_and_index(self):
        address = "00C0CA70"
        original = decompile_cache.cache_key(address, self.settings)
        self.assertIsNotNone(original)

        with patch.object(decompile_cache, "HEADLESS_OPTIONS", ("-readOnly",)):
            self.assertNotEqual(original, decompile_cache.cache_key(address, self.settings))

        component = decompile_cache._decompiler_components(
            self.settings.ghidra_headless.parent.parent
        )[0]
        component.write_bytes(b"updated decompiler component")
        self.assertNotEqual(original, decompile_cache.cache_key(address, self.settings))
        component.write_bytes(b"decompiler component")

        self.script.write_text("// changed decompiler script\n", encoding="utf-8")
        self.assertNotEqual(original, decompile_cache.cache_key(address, self.settings))
        self.script.write_text("// deterministic test script\n", encoding="utf-8")

        project_db = self.project / "Dishonored-test.rep" / "idata" / "program.db"
        project_db.write_bytes(b"analysis-revision-with-changes")
        self.assertNotEqual(original, decompile_cache.cache_key(address, self.settings))
        project_db.write_bytes(b"analysis-revision-a")

        self.index.write_text("address,name\n00C0CA70,Renamed\n", encoding="utf-8")
        self.assertNotEqual(original, decompile_cache.cache_key(address, self.settings))

    def test_ghidra_version_change_and_unavailable_provenance_fail_closed(self):
        address = "00C0CA70"
        original = decompile_cache.cache_key(address, self.settings)
        properties = self.settings.ghidra_headless.parent.parent / "Ghidra" / "application.properties"
        properties.write_text(
            "application.version=12.1.3\n"
            "application.revision.ghidra=revision-c\n",
            encoding="utf-8",
        )
        self.assertNotEqual(original, decompile_cache.cache_key(address, self.settings))

        properties.unlink()
        self.assertIsNone(decompile_cache.cache_key(address, self.settings))
        with patch.object(decompile_cache, "get_settings", return_value=self.settings):
            stored = decompile_cache.store(
                address,
                {"pseudocode": "stale"},
                expected_cache_key=original,
            )
            self.assertFalse(stored["cache_stored"])
            self.assertIsNone(decompile_cache.load(address))

    def test_legacy_cache_entry_without_key_is_a_miss(self):
        address = "00C0CA70"
        with patch.object(decompile_cache, "get_settings", return_value=self.settings):
            path = self.settings.decompile_cache_dir / "00C0CA70.json"
            path.parent.mkdir(parents=True)
            path.write_text(json.dumps({"pseudocode": "legacy"}), encoding="utf-8")
            self.assertIsNone(decompile_cache.load(address))

    def test_cache_misses_if_identity_changes_during_read(self):
        address = "00C0CA70"
        key = decompile_cache.cache_key(address, self.settings)
        with patch.object(decompile_cache, "get_settings", return_value=self.settings):
            decompile_cache.store(
                address,
                {"pseudocode": "current"},
                expected_cache_key=key,
            )
            with patch.object(decompile_cache, "cache_key", side_effect=[key, "changed"]):
                self.assertIsNone(decompile_cache.load(address))


if __name__ == "__main__":
    unittest.main()
