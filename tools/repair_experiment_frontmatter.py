#!/usr/bin/env python3
"""Rewrite experiment YAML frontmatter with separated lifecycle vs claim fields.

experiment_status: planned | in_progress | done | superseded
claim_status: confirmed | observed | inferred | unknown | superseded | mixed
  (mixed = experiment contains both confirmed facts and open claims; see body)

Does not infer status from keyword hits inside prose.
"""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXPERIMENTS = ROOT / "experiments"
FRONTMATTER_RE = re.compile(r"^---\r?\n(.*?)\r?\n---\r?\n", re.DOTALL)
QUESTION_RE = re.compile(r"^-\s*Question:\s*(.+)$", re.MULTILINE | re.IGNORECASE)
PURPOSE_RE = re.compile(r"^-\s*Purpose:\s*(.+)$", re.MULTILINE | re.IGNORECASE)
TITLE_RE = re.compile(r"^#\s+(.+)$", re.MULTILINE)

# Explicit corrections: experiment_status, claim_status, optional question override.
META: dict[str, tuple[str, str, str | None]] = {
    "EXP-0001": ("done", "confirmed", "Which executable build is in the local copy, and what files does the copy contain?"),
    "EXP-0002": ("done", "observed", "What are the opening bytes / package-tag shape of DishonoredGame.upk and Core.upk?"),
    "EXP-0003": ("done", "observed", "Does the current game configuration contain the changes described by the bundled StartInMenu installer?"),
    "EXP-0004": ("done", "observed", "What Blink-related class/object names does UModel report in DishonoredGame.upk?"),
    "EXP-0005": ("done", "observed", "Which paths differ between the previous and current local Steam inventories, and do shared paths match by hash?"),
    "EXP-0006": ("done", "confirmed", "Do UModel and package-header triage agree on Core/DishonoredGame package version and engine metadata?"),
    "EXP-0007": ("done", "observed", "Can UE Explorer MCP inspect package summary/objects on the compressed DishonoredGame.upk?"),
    "EXP-0008": ("superseded", "superseded", "Can Blink script/defaults be recovered from the compressed package without decompression?"),
    "EXP-0009": ("done", "confirmed", "After Gildor decompression, what Blink class/default values does UELib emit?"),
    "EXP-0010": ("done", "observed", "What are the co-op character preview artifacts, and what is excluded from research scope?"),
    "EXP-0011": ("done", "confirmed", "Do all CookedPCConsole .upk files appear in the package index with matching manifest hashes?"),
    "EXP-0012": ("done", "mixed", "What Blink-related native leads exist before full EXE analysis, and what are the Ghidra binding caveats?"),
    "EXP-0013": ("done", "mixed", "Does full Ghidra analysis of the workspace EXE complete, and what Blink name/native-table correlations appear?"),
    "EXP-0014": ("done", "mixed", "Which native owners can be attributed for Blink-adjacent tables, and what remains unresolved for movement?"),
    "EXP-0015": ("done", "confirmed", "How is PowerBlink wired in player-pawn defaults, and where does the native/script boundary stop?"),
    "EXP-0016": ("done", "observed", "Why did runtime/Frida MCP miss the research process, and are corrected paths sufficient without live attach?"),
    "EXP-0017": ("done", "mixed", "Which pointer-run/constructor vtable candidates match PowerWheel/Controller slots, and which are false positives?"),
    "EXP-0018": ("done", "mixed", "Does package data support NPC look-at ownership for ArkCpntType_Lookat, and is there a Blink move link?"),
    "EXP-0019": ("done", "confirmed", "How does PowerWheel Scaleform selection reach native OnSelectionChanged, and does it activate Blink?"),
    "EXP-0020": ("superseded", "superseded", "Which constructor/global initializes DisGFxMoviePlayerPowerWheel? (Superseded by EXP-0021.)"),
    "EXP-0021": ("done", "mixed", "What are the exact PowerWheel and PlayerController vtables/targets for selection callbacks?"),
    "EXP-0022": ("done", "mixed", "What do controller shortcut Use/Select handlers write, and how do they relate to power activation?"),
    "EXP-0023": ("done", "mixed", "How does native code read Blink tweak/level data through the component interface?"),
    "EXP-0024": ("done", "confirmed", "Is there a static Blink path that writes the owner pawn position?"),
    "EXP-0025": ("done", "mixed", "What package UsePower/CastBlink configuration exists, and is there a script edge to Blink move-mode?"),
    "EXP-0026": ("done", "observed", "Do consumers of the controller shortcut index reach power activation?"),
    "EXP-0027": ("done", "mixed", "Can UsePower/CastBlink configuration be joined to the Blink move-mode setter, and is nearby pointer data a live table?"),
    "EXP-0028": ("done", "mixed", "What is the UsePower inheritance/vtable shape, and is there a static path into Blink move-mode?"),
    "EXP-0029": ("done", "mixed", "Is FUN_00C0CA70 a runtime dispatcher that invokes DisItemContext_UsePower slots?"),
    "EXP-0030": ("done", "mixed", "What conditions gate the static transition into Blink move mode, and who calls that setter?"),
    "EXP-0031": ("done", "mixed", "How do UsePower context lifecycle/callback cleanup helpers behave, and do they join activation?"),
    "EXP-0032": ("done", "mixed", "What is the machine-level layout and caller context of candidate dispatcher FUN_00C0CA70?"),
    "EXP-0033": ("done", "mixed", "What package/default ownership surrounds UsePower context creation and callback registration?"),
    "EXP-0034": ("done", "mixed", "Is there a concrete context-manager slot dispatch path, and does it reach Blink?"),
    "EXP-0035": ("done", "mixed", "Which class owns the +0x59C manager used by the EXP-0034 dispatch candidate?"),
    "EXP-0036": ("done", "mixed", "What does FUN_00B36CA0 register, and does any key route join Use/Blink?"),
    "EXP-0037": ("done", "mixed", "Does the Pawn manager dispatch ABI match DisItemContext_UsePower, and who writes pawn+0x59C?"),
}


def yaml_value(value: str) -> str:
    value = value.replace('"', '\\"')
    if any(
        ch in value
        for ch in (
            ":",
            "#",
            "{",
            "}",
            "[",
            "]",
            ",",
            "&",
            "*",
            "?",
            "|",
            "-",
            "<",
            ">",
            "=",
            "!",
            "%",
            "@",
            "`",
        )
    ) or value != value.strip():
        return f'"{value}"'
    return value


def body_without_frontmatter(text: str) -> str:
    match = FRONTMATTER_RE.match(text)
    return text[match.end() :] if match else text


def infer_title(body: str, stem: str) -> str:
    match = TITLE_RE.search(body)
    if not match:
        parts = stem.split("-", 2)
        return parts[2].replace("-", " ") if len(parts) == 3 else stem
    return re.sub(r"^EXP-\d{4}\s*[—\-–:]\s*", "", match.group(1).strip()).strip()


def main() -> None:
    for path in sorted(EXPERIMENTS.glob("EXP-*.md")):
        parts = path.stem.split("-")
        exp_id = f"{parts[0]}-{parts[1]}"
        if exp_id not in META:
            raise SystemExit(f"Missing META entry for {exp_id}")
        experiment_status, claim_status, question = META[exp_id]
        body = body_without_frontmatter(path.read_text(encoding="utf-8"))
        title = infer_title(body, path.stem)
        if question is None:
            qmatch = QUESTION_RE.search(body) or PURPOSE_RE.search(body)
            question = re.sub(r"\s+", " ", qmatch.group(1).strip()) if qmatch else title
        lines = [
            "---",
            f"id: {exp_id}",
            f"title: {yaml_value(title)}",
            f"experiment_status: {experiment_status}",
            f"claim_status: {claim_status}",
            'build: "10256413"',
            f"question: {yaml_value(question)}",
            "---",
            "",
        ]
        path.write_text("\n".join(lines) + body.lstrip("\n"), encoding="utf-8", newline="\n")
        print(f"{exp_id}: experiment_status={experiment_status} claim_status={claim_status}")


if __name__ == "__main__":
    main()
