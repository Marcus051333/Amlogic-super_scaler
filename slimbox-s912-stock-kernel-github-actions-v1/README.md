# SlimBOX 9.2.0 / H96 Pro+ S912 — stock kernel reproduction builder

This is **phase 1 only**.

It does **not** patch `super_scaler`.
It does **not** repack `boot.img`.
It does **not** flash anything.

Goal: test whether the candidate public Amlogic Android Pie 4.9.113 source can
reproduce the stock kernel closely enough, especially its `CONFIG_MODVERSIONS`
symbol CRCs.

## Known stock target

- H96 Pro+ / Amlogic S912 (GXM)
- SlimBOX 9.2.0 X92-compatible ROM
- ARMv7 / 32-bit ARM
- Linux 4.9.113
- `CONFIG_MODVERSIONS=y`
- Linaro GCC 6.3.1-2017.02
- original build identity `daivietpda@gocmobile`
- original build timestamp `Wed Jul 8 19:59:03 +07 2020`

## Required file

Copy:

    C:\SlimboxKernel\kernel-config.gz

to:

    stock/kernel-config.gz

Do not rename or decompress it.

## Public repo and vendor modules

The workflow does not require original vendor `.ko` files to be committed publicly.

After a successful build it uploads `Module.symvers`; that can be compared separately
against your original:

    amvdec_h264.ko
    decoder_common.ko

If you explicitly want GitHub Actions to compare them automatically, you may add them
to `stock/` with `git add -f`, but `.gitignore` blocks accidental publication by default.

## Run

1. Create a new public GitHub repository.
2. Extract this ZIP into it.
3. Add `stock/kernel-config.gz`.
4. Commit and push.
5. Open Actions.
6. Select `SlimBOX S912 - stock kernel reproduction`.
7. Click `Run workflow`.

Default candidate:

    LineageOS/android_kernel_amlogic_linux-4.9-pie
    lineage-19.1

The branch is only a candidate starting point. The workflow records the exact source
commit. A clean compile alone is not proof of ABI compatibility.

## Outputs

The artifact includes, when the build reaches them:

- zImage
- vmlinux
- System.map
- Module.symvers
- stock.config
- effective.config
- config.diff
- KERNELRELEASE.txt
- SOURCE_IDENTITY.txt
- TOOLCHAIN.txt
- VPP_SUPER_SCALER_SOURCE.txt
- BUILD_PRODUCTS.txt
- build.log
- ABI_REPORT.md (if applicable)
- SHA256SUMS.txt

## First-run result to send back

If successful, send:

- `Module.symvers`
- `config.diff`
- `SOURCE_IDENTITY.txt`
- `KERNELRELEASE.txt`
- `VPP_SUPER_SCALER_SOURCE.txt`

If it fails, send the failed Actions section or `build.log`.

Do not flash `zImage` yet.
