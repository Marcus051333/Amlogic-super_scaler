#!/usr/bin/env python3
import re
import sys
from pathlib import Path

if len(sys.argv) != 5:
    raise SystemExit(
        "usage: compare_modversions.py Module.symvers stock_modversions_dir providers.tsv report.md"
    )

symvers_path = Path(sys.argv[1])
imports_dir = Path(sys.argv[2])
providers_path = Path(sys.argv[3])
report_path = Path(sys.argv[4])

candidate = {}
for raw in symvers_path.read_text(errors="replace").splitlines():
    parts = raw.split()
    if len(parts) < 2:
        continue
    try:
        candidate[parts[1]] = int(parts[0], 16)
    except ValueError:
        pass

providers = {}
provider_name = {}
for raw in providers_path.read_text(errors="replace").splitlines():
    if not raw.strip() or raw.startswith("#"):
        continue
    parts = raw.split("\t")
    if len(parts) < 3:
        continue
    crc_s, symbol, provider = parts[:3]
    try:
        crc = int(crc_s, 16)
    except ValueError:
        continue

    # A symbol should not be exported with conflicting CRCs across the stock providers.
    if symbol in providers and providers[symbol] != crc:
        raise SystemExit(
            f"conflicting stock provider CRC for {symbol}: "
            f"0x{providers[symbol]:08x} vs 0x{crc:08x}"
        )
    providers[symbol] = crc
    provider_name.setdefault(symbol, provider)

crc_re = re.compile(r"^\s*(0x[0-9a-fA-F]+)\s+(\S+)\s*$")

totals = {
    "parsed": 0,
    "kernel_match": 0,
    "external_match": 0,
    "mismatch": 0,
    "unresolved": 0,
}
module_results = []

for dump in sorted(imports_dir.glob("*.modversions.txt")):
    entries = []
    for raw in dump.read_text(errors="replace").splitlines():
        m = crc_re.match(raw)
        if m:
            entries.append((m.group(2), int(m.group(1), 16)))

    stats = {
        "kernel_match": 0,
        "external_match": 0,
        "mismatch": 0,
        "unresolved": 0,
    }
    mismatches = []
    unresolved = []
    external = []

    for symbol, stock_crc in entries:
        if symbol in candidate:
            got = candidate[symbol]
            if got == stock_crc:
                stats["kernel_match"] += 1
            else:
                stats["mismatch"] += 1
                mismatches.append(
                    (symbol, stock_crc, got, "candidate vmlinux/Module.symvers")
                )
        elif symbol in providers:
            got = providers[symbol]
            if got == stock_crc:
                stats["external_match"] += 1
                external.append((symbol, stock_crc, provider_name[symbol]))
            else:
                stats["mismatch"] += 1
                mismatches.append(
                    (symbol, stock_crc, got, provider_name[symbol])
                )
        else:
            stats["unresolved"] += 1
            unresolved.append((symbol, stock_crc))

    totals["parsed"] += len(entries)
    for k in ("kernel_match", "external_match", "mismatch", "unresolved"):
        totals[k] += stats[k]

    module_results.append((dump.name, len(entries), stats, mismatches, unresolved, external))

passed = (
    totals["parsed"] > 0
    and totals["mismatch"] == 0
    and totals["unresolved"] == 0
    and totals["kernel_match"] + totals["external_match"] == totals["parsed"]
)
verdict = "MATCH" if passed else "NO_MATCH"

lines = [
    "# SlimBOX tested ABI / CONFIG_MODVERSIONS comparison",
    "",
    "The stock import fingerprints come from the original SlimBOX vendor modules.",
    "Symbols are checked first against the candidate kernel `Module.symvers`, then",
    "against CRC exports from the original stock external media modules.",
    "",
]

if passed:
    lines += [
        "**Result: MATCH for every tested imported symbol.**",
        "",
        "No tested CRC mismatch remains and no tested symbol is unresolved.",
        "This is strong evidence for the tested ABI surface; it is not by itself",
        "proof that every untested kernel ABI detail is identical.",
        "",
    ]
else:
    lines += [
        "**Result: NOT a complete match for the tested symbol set.**",
        "",
        "Do not flash this build.",
        "",
    ]

lines += [
    f"- Parsed stock requirements: {totals['parsed']}",
    f"- Matched directly in candidate kernel Module.symvers: {totals['kernel_match']}",
    f"- Matched in stock external media-module providers: {totals['external_match']}",
    f"- CRC mismatches: {totals['mismatch']}",
    f"- Unresolved symbols: {totals['unresolved']}",
    "",
]

for name, parsed, stats, mismatches, unresolved, external in module_results:
    lines += [
        f"## {name}",
        "",
        f"- Parsed: {parsed}",
        f"- Kernel match: {stats['kernel_match']}",
        f"- External-module match: {stats['external_match']}",
        f"- CRC mismatch: {stats['mismatch']}",
        f"- Unresolved: {stats['unresolved']}",
        "",
    ]

    if external:
        lines += [
            "### Resolved by original stock media modules",
            "",
            "| Symbol | CRC | Provider |",
            "|---|---:|---|",
        ]
        for symbol, crc, provider in external:
            lines.append(f"| `{symbol}` | `0x{crc:08x}` | `{provider}` |")
        lines.append("")

    if mismatches:
        lines += [
            "### CRC mismatches",
            "",
            "| Symbol | Stock required | Found | Source |",
            "|---|---:|---:|---|",
        ]
        for symbol, want, got, source in mismatches:
            lines.append(
                f"| `{symbol}` | `0x{want:08x}` | `0x{got:08x}` | `{source}` |"
            )
        lines.append("")

    if unresolved:
        lines += [
            "### Unresolved",
            "",
            "| Symbol | Stock CRC |",
            "|---|---:|",
        ]
        for symbol, crc in unresolved:
            lines.append(f"| `{symbol}` | `0x{crc:08x}` |")
        lines.append("")

lines += [
    "## Machine-readable summary",
    "",
    f"`VERDICT={verdict}`",
    f"`PARSED={totals['parsed']}`",
    f"`KERNEL_MATCH={totals['kernel_match']}`",
    f"`EXTERNAL_MATCH={totals['external_match']}`",
    f"`MISMATCH={totals['mismatch']}`",
    f"`UNRESOLVED={totals['unresolved']}`",
    "",
]

report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
print(
    f"VERDICT={verdict} PARSED={totals['parsed']} "
    f"KERNEL_MATCH={totals['kernel_match']} "
    f"EXTERNAL_MATCH={totals['external_match']} "
    f"MISMATCH={totals['mismatch']} UNRESOLVED={totals['unresolved']}"
)
