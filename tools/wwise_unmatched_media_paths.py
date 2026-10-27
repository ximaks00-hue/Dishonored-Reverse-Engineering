#!/usr/bin/env python3
"""Join unmatched Wwise Sound media IDs to parsed same-bank event paths.

The result is a static parser-output join, not proof that an event is invoked
or that its media payload is present or playable.
"""

from __future__ import annotations

import argparse
import csv
from collections import Counter, defaultdict
from pathlib import Path


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--build-dir", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()

    sound_rows = read_csv(args.build_dir / "wwise-sound-media-joins.csv")
    event_paths = read_csv(args.build_dir / "wwise-event-hirc-sound-paths.csv")
    direct_paths = read_csv(args.build_dir / "wwise-event-direct-sound-paths.csv")

    def bank_key(row: dict[str, str]) -> tuple[str, str]:
        return row["source_pck"], row["bank_id"]

    path_by_media: dict[tuple[str, str, str], list[dict[str, str]]] = defaultdict(list)
    direct_by_media: Counter[tuple[str, str, str]] = Counter()
    for row in event_paths:
        path_by_media[(*bank_key(row), row["media_source_id"])].append(row)
    for row in direct_paths:
        direct_by_media[(*bank_key(row), row["media_source_id"])] += 1

    output_rows: list[dict[str, str | int]] = []
    for sound in sound_rows:
        if not (
            sound["same_bank_media_index"] == "false"
            and sound["same_pck_wem_matches"] == "0"
            and sound["global_wem_match_count"] == "0"
            and sound["global_media_index_bank_count"] == "0"
        ):
            continue

        key = (*bank_key(sound), sound["media_source_id"])
        paths = path_by_media.get(key, [])
        if not paths:
            raise SystemExit(f"unmatched media has no same-bank event path: {key}")
        if sound["file_id"] != "0" or sound["stream_type"] != "0" or sound["external_flag"] != "0":
            raise SystemExit(f"unexpected parser fields for unmatched media: {key}")

        chains = sorted({row["object_type_chain"] for row in paths})
        events = sorted({row["event_id"] for row in paths})
        output_rows.append(
            {
                "source_pck": sound["source_pck"],
                "bank_id": sound["bank_id"],
                "sound_id": sound["sound_id"],
                "media_source_id": sound["media_source_id"],
                "file_id": sound["file_id"],
                "stream_type": sound["stream_type"],
                "external_flag": sound["external_flag"],
                "event_path_count": len(paths),
                "distinct_event_count": len(events),
                "event_ids": ";".join(events),
                "direct_sound_path_count": direct_by_media[key],
                "object_type_chains": ";".join(chains),
                "claim": "parser-derived event path; invocation and media payload/playability unproved",
            }
        )

    args.output.parent.mkdir(parents=True, exist_ok=True)
    fields = list(output_rows[0]) if output_rows else []
    with args.output.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(output_rows)

    print(
        f"unmatched_sound_rows={len(output_rows)} "
        f"unique_media_ids={len({row['media_source_id'] for row in output_rows})} "
        f"event_paths={sum(int(row['event_path_count']) for row in output_rows)} "
        f"direct_event_paths={sum(int(row['direct_sound_path_count']) for row in output_rows)} "
        f"source_pcks={len({row['source_pck'] for row in output_rows})}"
    )


if __name__ == "__main__":
    main()
