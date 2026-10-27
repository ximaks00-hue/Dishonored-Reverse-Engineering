#!/usr/bin/env python3
"""Compare UELib DXT1 mip ranges, including chunked LZO blocks, to UModel TGAs."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import struct
from pathlib import Path
from typing import Iterable

import lzokay


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest().upper()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def decode_tga_rle(path: Path) -> tuple[int, int, list[tuple[int, int, int]]]:
    data = path.read_bytes()
    if len(data) < 18 or data[2] != 10 or data[16] != 24 or data[1] != 0:
        raise ValueError(f"Expected 24-bit type-10 true-color TGA: {path}")
    width = int.from_bytes(data[12:14], "little")
    height = int.from_bytes(data[14:16], "little")
    offset = 18 + data[0]
    bgr: list[tuple[int, int, int]] = []
    while offset < len(data):
        packet = data[offset]
        offset += 1
        count = (packet & 0x7F) + 1
        if packet & 0x80:
            pixel = tuple(data[offset : offset + 3])
            if len(pixel) != 3:
                raise ValueError("Truncated TGA run packet")
            offset += 3
            bgr.extend([pixel] * count)
        else:
            packet_bytes = data[offset : offset + 3 * count]
            if len(packet_bytes) != 3 * count:
                raise ValueError("Truncated TGA raw packet")
            bgr.extend(tuple(packet_bytes[i : i + 3]) for i in range(0, len(packet_bytes), 3))
            offset += 3 * count
        if len(bgr) > width * height:
            raise ValueError("TGA RLE packet stream exceeds declared dimensions")
    if len(bgr) != width * height or offset != len(data):
        raise ValueError("TGA RLE stream does not exactly cover declared dimensions")

    # Normalize image orientation to top-left RGB row-major order.
    rows = [bgr[y * width : (y + 1) * width] for y in range(height)]
    if not (data[17] & 0x20):
        rows.reverse()
    if data[17] & 0x10:
        rows = [list(reversed(row)) for row in rows]
    rgb = [(r, g, b) for row in rows for b, g, r in row]
    return width, height, rgb


def _rgb565(value: int) -> tuple[int, int, int]:
    red = (value >> 11) & 0x1F
    green = (value >> 5) & 0x3F
    blue = value & 0x1F
    return (
        (red << 3) | (red >> 2),
        (green << 2) | (green >> 4),
        (blue << 3) | (blue >> 2),
    )


def decode_dxt1(data: bytes, width: int, height: int) -> list[tuple[int, int, int]]:
    if width % 4 or height % 4:
        raise ValueError("This verifier requires DXT1 dimensions divisible by four")
    expected = (width // 4) * (height // 4) * 8
    if len(data) != expected:
        raise ValueError(f"DXT1 size mismatch: got {len(data)}, expected {expected}")
    image = [(0, 0, 0)] * (width * height)
    offset = 0
    for block_y in range(0, height, 4):
        for block_x in range(0, width, 4):
            c0 = int.from_bytes(data[offset : offset + 2], "little")
            c1 = int.from_bytes(data[offset + 2 : offset + 4], "little")
            selectors = int.from_bytes(data[offset + 4 : offset + 8], "little")
            offset += 8
            color0, color1 = _rgb565(c0), _rgb565(c1)
            if c0 > c1:
                palette = [
                    color0,
                    color1,
                    tuple((2 * color0[c] + color1[c]) // 3 for c in range(3)),
                    tuple((color0[c] + 2 * color1[c]) // 3 for c in range(3)),
                ]
            else:
                palette = [
                    color0,
                    color1,
                    tuple((color0[c] + color1[c]) // 2 for c in range(3)),
                    (0, 0, 0),
                ]
            for pixel in range(16):
                x = block_x + pixel % 4
                y = block_y + pixel // 4
                image[y * width + x] = palette[(selectors >> (2 * pixel)) & 3]
    return image


def read_range(path: Path, offset: int, size: int) -> bytes:
    if offset < 0 or size < 0:
        raise ValueError(f"Invalid range: {path} offset={offset} size={size}")
    file_size = path.stat().st_size
    if offset + size > file_size:
        raise ValueError(f"Range exceeds file: {path} offset={offset} size={size} length={file_size}")
    with path.open("rb") as stream:
        stream.seek(offset)
        data = stream.read(size)
    if len(data) != size:
        raise ValueError("Short read for requested mip range")
    return data


def decode_lzo_bulk(stored: bytes, expected_size: int, mip_index: int) -> tuple[bytes, dict[str, object]]:
    # UE3 LZO bulk blocks can contain a chunk table after the 16-byte fixed
    # header. Validate the table by its declared aggregate sizes and exact
    # stored-range boundary; do not infer meanings for unrelated header words.
    if len(stored) >= 24 and struct.unpack_from("<I", stored, 0)[0] == 0x9E2A83C1:
        _, _, total_compressed, total_uncompressed = struct.unpack_from("<4I", stored, 0)
        if total_uncompressed == expected_size and total_compressed <= len(stored) - 16:
            cursor = 16
            compressed_sum = uncompressed_sum = 0
            chunks: list[tuple[int, int]] = []
            while compressed_sum < total_compressed or uncompressed_sum < total_uncompressed:
                if cursor + 8 > len(stored):
                    break
                compressed_size, uncompressed_size = struct.unpack_from("<2I", stored, cursor)
                if not compressed_size or not uncompressed_size:
                    break
                chunks.append((compressed_size, uncompressed_size))
                compressed_sum += compressed_size
                uncompressed_sum += uncompressed_size
                cursor += 8
                if compressed_sum > total_compressed or uncompressed_sum > total_uncompressed:
                    break
            if (
                chunks
                and compressed_sum == total_compressed
                and uncompressed_sum == total_uncompressed
                and cursor + total_compressed == len(stored)
            ):
                output: list[bytes] = []
                data_cursor = cursor
                for compressed_size, uncompressed_size in chunks:
                    chunk = stored[data_cursor : data_cursor + compressed_size]
                    decoded = lzokay.decompress(chunk, uncompressed_size)
                    if len(decoded) != uncompressed_size:
                        raise ValueError(f"LZO chunk output size mismatch for mip {mip_index}")
                    output.append(decoded)
                    data_cursor += compressed_size
                decoded_all = b"".join(output)
                if len(decoded_all) != expected_size:
                    raise ValueError(f"LZO aggregate output size mismatch for mip {mip_index}")
                return decoded_all, {
                    "lzo_container_header_bytes": cursor,
                    "lzo_chunk_count": len(chunks),
                    "lzo_chunk_compressed_sizes": [item[0] for item in chunks],
                    "lzo_chunk_uncompressed_sizes": [item[1] for item in chunks],
                    "lzo_prefix_bytes_skipped": None,
                }

    successes: list[tuple[int, bytes]] = []
    for prefix_size in range(min(65, len(stored))):
        try:
            decoded = lzokay.decompress(stored[prefix_size:], expected_size)
        except Exception:
            continue
        if len(decoded) == expected_size:
            successes.append((prefix_size, decoded))
    if not successes:
        raise ValueError(f"No supported LZO payload layout decoded to the declared element count for mip {mip_index}")
    prefix_size, decoded = min(successes, key=lambda item: item[0])
    return decoded, {
        "lzo_container_header_bytes": None,
        "lzo_chunk_count": 1,
        "lzo_chunk_compressed_sizes": [len(stored) - prefix_size],
        "lzo_chunk_uncompressed_sizes": [len(decoded)],
        "lzo_prefix_bytes_skipped": prefix_size,
    }


def decode_bulk(row: dict[str, str], package: Path, tfc: Path) -> tuple[bytes, dict[str, object]]:
    external = "StoreInSeparateFile" in row["bulk_flags"]
    source = tfc if external else package
    offset, size = int(row["storage_offset"]), int(row["storage_size"])
    stored = read_range(source, offset, size)
    if "CompressedLZO" in row["bulk_flags"]:
        decoded, lzo_info = decode_lzo_bulk(stored, int(row["element_count"]), int(row["mip_index"]))
    else:
        decoded = stored
        if len(decoded) != int(row["element_count"]):
            raise ValueError(f"Inline mip size differs from element count for mip {row['mip_index']}")
        lzo_info = {}
    return decoded, {
        "storage_file": source.name,
        "storage_offset": offset,
        "storage_size": size,
        "stored_range_sha256": sha256(stored),
        **lzo_info,
        "decoded_mip_sha256": sha256(decoded),
        "decoded_bytes": len(decoded),
    }


def compare_pixels(source: Iterable[tuple[int, int, int]], target: Iterable[tuple[int, int, int]]) -> dict[str, object]:
    source_pixels, target_pixels = list(source), list(target)
    if len(source_pixels) != len(target_pixels):
        raise ValueError("Decoded mip and TGA pixel counts differ")
    exact = 0
    absolute_error = 0
    max_error = 0
    for a, b in zip(source_pixels, target_pixels):
        for ac, bc in zip(a, b):
            error = abs(ac - bc)
            absolute_error += error
            max_error = max(max_error, error)
        exact += a == b
    channels = len(source_pixels) * 3
    return {
        "exact_rgb_pixels": exact,
        "total_pixels": len(source_pixels),
        "mean_absolute_channel_error": absolute_error / channels,
        "max_absolute_channel_error": max_error,
        "pixel_identical": exact == len(source_pixels),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mip-census-csv", type=Path, required=True)
    parser.add_argument("--package", type=Path, required=True)
    parser.add_argument("--tfc", type=Path, required=True)
    parser.add_argument("--mip0-tga", type=Path, required=True)
    parser.add_argument("--inline-fallback-tga", "--mip1-tga", dest="inline_fallback_tga", type=Path, required=True)
    parser.add_argument("--output-json", type=Path, required=True)
    args = parser.parse_args()

    with args.mip_census_csv.open(encoding="utf-8-sig", newline="") as stream:
        rows = {int(row["mip_index"]): row for row in csv.DictReader(stream)}
    first_inline_index = next(
        (index for index in sorted(rows) if "StoreInSeparateFile" not in rows[index]["bulk_flags"]),
        None,
    )
    if first_inline_index is None:
        raise ValueError("Mip census has no inline mip for fallback comparison")
    comparisons = []
    for mip_index, tga_path in ((0, args.mip0_tga), (first_inline_index, args.inline_fallback_tga)):
        row = rows[mip_index]
        mip_bytes, bulk_info = decode_bulk(row, args.package, args.tfc)
        width, height = int(row["width"]), int(row["height"])
        decoded_pixels = decode_dxt1(mip_bytes, width, height)
        tga_width, tga_height, tga_pixels = decode_tga_rle(tga_path)
        if (tga_width, tga_height) != (width, height):
            raise ValueError(f"TGA dimensions do not match mip {mip_index}")
        comparisons.append({
            "mip_index": mip_index,
            "width": width,
            "height": height,
            "bulk_flags": row["bulk_flags"],
            **bulk_info,
            "tga_file": str(tga_path),
            "tga_file_size": tga_path.stat().st_size,
            "tga_sha256": sha256(tga_path.read_bytes()),
            **compare_pixels(decoded_pixels, tga_pixels),
        })
    result = {
        "package_file": str(args.package),
        "package_sha256": sha256_file(args.package),
        "tfc_file": str(args.tfc),
        "tfc_file_size": args.tfc.stat().st_size,
        "tfc_sha256": sha256_file(args.tfc),
        "mip_comparisons": comparisons,
        "claim_limit": "Byte-to-pixel equality verifies this parser export sample; it does not prove in-game runtime rendering or general TFC format coverage.",
    }
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
