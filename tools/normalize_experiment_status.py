#!/usr/bin/env python3
"""DISABLED: keyword-based status inference corrupted experiment frontmatter.

Use tools/repair_experiment_frontmatter.py for explicit META-driven repairs, or
edit YAML frontmatter by hand (experiment_status + claim_status).
"""

from __future__ import annotations

import sys


def main() -> int:
    print(
        "normalize_experiment_status.py is disabled. "
        "It previously inferred statuses from prose keywords and produced "
        "false labels (e.g. EXP-0017=rejected, EXP-0030=unknown). "
        "Use tools/repair_experiment_frontmatter.py instead.",
        file=sys.stderr,
    )
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
