#!/usr/bin/env python3
import re
import sys
from pathlib import Path

if len(sys.argv) != 4:
    raise SystemExit("usage: compare_modversions.py Module.symvers vendor_dir report.md")

symvers_path = Path(sys.argv[1])
vendor_dir = Path(sys.argv[2])
report_path = Path(sys.argv[3])

symvers = {}
for raw in symvers_path.read_text(errors="replace").splitlines():
    parts = raw.split()
    if len(parts) < 2:
        continue
    try:
        symvers[parts[1]] = int(parts[0], 16)
    except ValueError:
        pass

crc_re = re.compile(r"^\s*(0x[0-9a-fA-F]+)\s+(\S+)\s*$")
results = []
overall = {"parsed": 0, "match": 0, "mismatch": 0, "missing": 0}

for dump in sorted(vendor_dir.glob("*.txt")):
    entries = []
    for raw in dump.read_text(errors="replace").splitlines():
        m = crc_re.match(raw)
        if m:
            entries.append((m.group(2), int(m.group(1), 16)))

    stats = {"match": 0, "mismatch": 0, "missing": 0}
    mismatches, missing = [], []

    for symbol, vendor_crc in entries:
        candidate_crc = symvers.get(symbol)
        if candidate_crc is None:
            stats["missing"] += 1
            missing.append((symbol, vendor_crc))
        elif candidate_crc == vendor_crc:
            stats["match"] += 1
        else:
            stats["mismatch"] += 1
            mismatches.append((symbol, vendor_crc, candidate_crc))

    overall["parsed"] += len(entries)
    for key in ("match", "mismatch", "missing"):
        overall[key] += stats[key]

    results.append((dump.stem, entries, stats, mismatches, missing))

lines = [
    "# ABI / CONFIG_MODVERSIONS comparison",
    "",
    "This compares CRCs required by the original vendor modules with CRCs",
    "exported by the candidate unmodified kernel build.",
    "",
]

if overall["parsed"] == 0:
    lines += ["**Result: INCOMPLETE** — no vendor MODVERSIONS entries were parsed.", ""]
elif overall["mismatch"] == 0 and overall["missing"] == 0:
    lines += [
        "**Result: all tested vendor symbol CRCs match this candidate build.**",
        "",
        "This is strong evidence for the tested symbol set, but does not by itself",
        "prove that the entire vendor kernel ABI is identical.",
        "",
    ]
else:
    lines += [
        "**Result: candidate is NOT ABI-compatible with the tested vendor symbol set.**",
        "",
        "Do not flash a kernel from this source/ref.",
        "",
    ]

lines += [
    f"- Parsed vendor requirements: {overall['parsed']}",
    f"- CRC matches: {overall['match']}",
    f"- CRC mismatches: {overall['mismatch']}",
    f"- Missing candidate symbols: {overall['missing']}",
    "",
]

for name, entries, stats, mismatches, missing in results:
    lines += [
        f"## {name}",
        "",
        f"- Parsed: {len(entries)}",
        f"- Match: {stats['match']}",
        f"- Mismatch: {stats['mismatch']}",
        f"- Missing: {stats['missing']}",
        "",
    ]

    if mismatches:
        lines += ["### CRC mismatches", "", "| Symbol | Vendor | Candidate |", "|---|---:|---:|"]
        for symbol, vendor, candidate in mismatches[:100]:
            lines.append(f"| `{symbol}` | `0x{vendor:08x}` | `0x{candidate:08x}` |")
        lines.append("")

    if missing:
        lines += ["### Missing candidate symbols", "", "| Symbol | Vendor CRC |", "|---|---:|"]
        for symbol, vendor in missing[:100]:
            lines.append(f"| `{symbol}` | `0x{vendor:08x}` |")
        lines.append("")

report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
