#!/usr/bin/env python3
"""Deprecated entry point.

Prefer tools/repair_experiment_frontmatter.py (explicit META) or hand-edit
experiment_status + claim_status. This script only reminds operators.
"""

from __future__ import annotations

import sys


def main() -> int:
    print(
        "add_experiment_frontmatter.py is deprecated. "
        "Use tools/repair_experiment_frontmatter.py for bulk repair, "
        "or edit YAML frontmatter manually.",
        file=sys.stderr,
    )
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
