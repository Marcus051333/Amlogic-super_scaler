# SlimBOX S912 v1.2 update

This update changes the workflow from a branch-tip build into a historical ABI search.

## What changes

- keeps `LineageOS/android_kernel_amlogic_linux-4.9-pie` as the candidate source family
- fetches full history of `lineage-19.1`
- by default selects the newest commit at or before:
  `2020-07-08T12:59:03Z`
- builds the kernel unmodified with the stock config and Linaro GCC 6.3.1-2017.02
- automatically compares `Module.symvers` against CRC fingerprints extracted from:
  - stock `amvdec_h264.ko` (95 imported symbols)
  - stock `decoder_common.ko` (175 imported symbols)
- does NOT include or publish the original `.ko` binaries
- does NOT patch `super_scaler`
- does NOT create or flash a boot image

## Files to replace/add in the existing repository

Replace:

    .github/workflows/stock-kernel-reproduction.yml
    scripts/compare_modversions.py

Add:

    stock/modversions/amvdec_h264.modversions.txt
    stock/modversions/decoder_common.modversions.txt

Keep your existing:

    stock/kernel-config.gz

## First v1.2 run

Use defaults:

    source_repo  = LineageOS/android_kernel_amlogic_linux-4.9-pie
    source_ref   = lineage-19.1
    target_time  = 2020-07-08T12:59:03Z
    build_dtbs   = true

The workflow will select the newest commit in that branch history not newer than
the stock kernel build time.

After the run, inspect `ABI_REPORT.md`. A compile success is not enough; do not flash
unless the tested stock CRC set is a complete match and later boot-image checks also pass.
