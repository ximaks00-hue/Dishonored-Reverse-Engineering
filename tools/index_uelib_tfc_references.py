#!/usr/bin/env python3
"""Index UELib Texture2D TextureFileCacheName fields against installed TFC files."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import defaultdict
from pathlib import Path, PurePosixPath


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--properties", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--game-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    manifest: dict[str, dict[str, str]] = {}
    with args.manifest.open(encoding="utf-8-sig", newline="") as stream:
        for row in csv.DictReader(stream):
            path = row["relative_path"].replace("\\", "/")
            if PurePosixPath(path).suffix.casefold() == ".tfc":
                manifest[PurePosixPath(path).stem.casefold()] = row

    game_root = args.game_root.resolve(strict=True)
    cache_checks: dict[str, tuple[bool, bool]] = {}
    for row in manifest.values():
        relative = row["relative_path"].replace("\\", "/")
        path = game_root.joinpath(*PurePosixPath(relative).parts)
        exists = path.is_file()
        size_match = exists and path.stat().st_size == int(row["bytes"])
        digest = hashlib.sha256()
        if exists:
            with path.open("rb") as cache_stream:
                for chunk in iter(lambda: cache_stream.read(8 * 1024 * 1024), b""):
                    digest.update(chunk)
        hash_match = exists and digest.hexdigest().upper() == row["sha256"].upper()
        cache_checks[PurePosixPath(relative).stem.casefold()] = (size_match, hash_match)

    refs: dict[tuple[str, str, str], set[int]] = defaultdict(set)
    source_hashes: dict[str, set[str]] = defaultdict(set)
    with args.properties.open("r", encoding="utf-8") as stream:
        for line in stream:
            if '"propertyName":"TextureFileCacheName"' not in line:
                continue
            row = json.loads(line)
            if row.get("propertyType") != "NameProperty":
                continue
            value = str(row.get("value") or "").strip().strip('"')
            if not value:
                continue
            package = row["package"].replace("\\", "/")
            object_path = str(row.get("ownerObjectPath") or "")
            owner_class = object_path.split("'", 1)[0] if "'" in object_path else "<untyped>"
            refs[(package, owner_class, value)].add(int(row["ownerPackageIndex"]))
            source_hashes[package].add(row.get("sourceSha256", ""))

    args.output.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "source_package", "source_sha256_values", "owner_class", "cache_name", "object_count",
        "installed_tfc_match", "tfc_path", "tfc_bytes", "tfc_sha256",
        "current_tfc_size_match", "current_tfc_sha256_match",
    ]
    with args.output.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        for (package, owner_class, cache_name), owners in sorted(refs.items()):
            cache = manifest.get(cache_name.casefold())
            writer.writerow({
                "source_package": package,
                "source_sha256_values": ";".join(sorted(filter(None, source_hashes[package]))),
                "owner_class": owner_class,
                "cache_name": cache_name,
                "object_count": len(owners),
                "installed_tfc_match": bool(cache),
                "tfc_path": cache["relative_path"].replace("\\", "/") if cache else "",
                "tfc_bytes": cache["bytes"] if cache else "",
                "tfc_sha256": cache["sha256"].upper() if cache else "",
                "current_tfc_size_match": cache_checks[cache_name.casefold()][0] if cache else False,
                "current_tfc_sha256_match": cache_checks[cache_name.casefold()][1] if cache else False,
            })
    summary = {
        "texture_cache_objects_with_cache_name": sum(map(len, refs.values())),
        "source_package_class_cache_pairs": len(refs),
        "distinct_source_package_cache_pairs": len({(package, name.casefold()) for package, _, name in refs}),
        "distinct_source_packages": len({package for package, _, _ in refs}),
        "distinct_owner_classes": len({owner_class for _, owner_class, _ in refs}),
        "distinct_cache_names": len({name.casefold() for _, _, name in refs}),
        "distinct_installed_tfc_names": len(manifest),
        "matched_source_package_class_cache_pairs": sum(name.casefold() in manifest for _, _, name in refs),
        "unmatched_source_package_class_cache_pairs": sum(name.casefold() not in manifest for _, _, name in refs),
        "current_tfc_files_size_matched": sum(size for size, _ in cache_checks.values()),
        "current_tfc_files_sha256_matched": sum(digest for _, digest in cache_checks.values()),
    }
    summary_path = args.output.with_name("tfc-reference-summary.json")
    summary_path.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
