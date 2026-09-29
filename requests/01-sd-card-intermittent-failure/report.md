# Intermittent SD card failure on the dev unit: diagnosis and mitigation

Request 01, 2026-09-28. Device `p3a-fab.local` (COM5), firmware 1.2.3 at the
start, SD root `/sdcard/p3a2`, 64 GB card.

## Verdict

The microSD card is corrupting itself. It silently stores 16 KB blocks of
data at the wrong logical address, on its own 16 KB grid, unrelated to what
the firmware asked it to write. Those misplaced blocks landed on the FAT and
on well over a hundred p3a directories. The SD bus is clean: not one CRC,
timeout, or I/O error appears in any boot log. This is not a p3a bug and not a
board-level electrical problem; it is the card's internal page mapping. The
same signature was seen once before on this unit (the July incident that
motivated `sd_health`), and the card reports a generic identity
(manufacturer id 0xFE, product name "SD", serial 249, made 2024-09), which is
typical of unbranded or counterfeit cards.

What can be done besides replacing the card: the firmware now repairs both
kinds of damage on its own, so a card like this degrades into re-downloaded
caches and a warning banner instead of a latched "SD card error". The card
will keep doing this, though, and blocks that land on an artwork file or on
both FAT copies are unrecoverable. The right fix for this unit is a branded
card. The self-repair is worth shipping regardless: cheap cards and power cuts
are common in the field.

## Symptom as seen by the user

Every boot since 2026-09-28 (the device sat unplugged for three days after a
normal Friday) the runtime "SD card error" overlay appeared and the web UI
showed the SD Card Failure banner. The boot-time "No Usable SD Card" screen
was never shown. Playback continued from cache.

## Evidence

Boot log (`evidence-boot-log-2026-09-28.md`, captured reset-free on COM5):

- Card mounts; the root-directory boot probe (create, fsync, rename, read
  back, delete) passes.
- The failures are all `rename()` inside `/sdcard/p3a2/channel/` returning
  `errno=2` (ENOENT) right after the temp file in the same directory was
  created, written and fsynced without error. Three of them latch
  `sd_health` at 23 s after reset. No `sdmmc`, `diskio` or FatFS disk error
  is logged, ever.

Raw inspection (diagnostic build with `CONFIG_P3A_SD_RAW_DEBUG`, analyzed
with `fat_inspect.py`):

- `channel/` directory cluster: its first 27 sectors, plus the last 5
  sectors of the neighbouring `vault/` directory cluster, hold 16 KB of
  high-entropy foreign data (image payload). The block starts at LBA
  52536576, which is a multiple of 32 sectors on the card's absolute grid,
  while FatFS clusters on this volume start at LBA = 5 mod 32. The
  firmware writes downloads in 32 KB chunks and FAT sectors one at a time, so
  no host write has this size or this alignment.
- Behind the junk, indexes 434 to 530 of the directory are the phantom
  `.tmp` entries that each failed boot created: FatFS's `dir_find()` stops at
  the first 0x00 byte inside the junk (four such entries exist) while
  `dir_alloc()` skips past it, so every create succeeds and every lookup
  fails with ENOENT. That mechanism is confirmed in `ff.c` (`dir_find`,
  `dir_alloc`).
- FAT copy 1 versus FAT copy 2: 384 sectors differ, in 32-sector runs (16 KB)
  at 16 KB-aligned addresses. Most runs are random data in FAT1 with a sane
  FAT2. One run contains a fragment of the FAT itself (sequential cluster
  chain values belonging 3,500 sectors away): FatFS never writes 16 KB of
  FAT at once, so only the card can have produced it.
- A recursive scan found 158 damaged directories under `/p3a2` before I
  stopped it (152 with the junk signature, 6 with a zeroed region), across
  `channel`, `vault`, `giphy` and `museum`. The scan is in
  `logs/scan-p3a2-partial.txt`.
- All suspect sectors read back identically with 1-, 7- and 32-sector reads,
  so the findings are card content, not a read artifact.

## What changed in the firmware (branch `fix/sd-resilience`)

New module `components/p3a_core/sd_repair.c` (+ `sd_repair.h`):

- **Directory self-heal.** At the write choke points (`fs_atomic` open and
  rename, `sd_path_ensure_parent_dirs`), an ENOENT triggers a probe: create a
  marker in the directory and stat it. A directory that hides its own new
  entries is moved to `{root}/lost/<path-with-underscores>-<n>` and recreated
  empty; `fs_atomic_write*` then redoes the write once, `fs_atomic_rename`
  callers (downloads) return an error and retry later on their own. Caches
  refill; user content that lived there was already unreachable and is kept
  in `lost/` for a PC to inspect. Repairs are counted per boot and persisted
  in NVS; an on-device format resets the total.
- **FAT mirror check at boot.** Right after mount, before FatFS touches the
  FAT, FAT1 and FAT2 are compared sector by sector. A sector is restored from
  the other copy when it is implausible (values outside the volume) or
  suspicious (a plausible fragment whose chain links point far from its own
  cluster range). Both-plausible mismatches are left alone. After any repair
  the card is remounted.
- Surfacing: `/status` gains `sd_repair` (counters and FAT check stats),
  `/playsets/active` gains `sd_repairs_boot` / `sd_repairs_total`, the web UI
  shows an "SD Card Corruption Repaired" banner (`WEBUI_VERSION` 2.24). Docs
  updated: `docs/HOW-TO-USE.md`, `README.md`, `AGENTS.md`,
  `docs/infrastructure/components.md`.
- Diagnostics: `GET /api/debug/sd/{info,read,ls,stat}` behind the new
  `CONFIG_P3A_SD_RAW_DEBUG` (default off, zero code in release builds), with
  `fat_inspect.py` on the host. Overlay `sdkconfig.sdraw.defaults` builds
  them into `build-sdraw/`.

## Verification on the device

First boot of the repair build: FAT check restored 134 FAT1 sectors and
139 FAT2 sectors, left 75 sectors alone (both copies junk), took 3.4 s; the
`channel/` directory was quarantined and recreated on the first write;
`sd_card_failed` went to `false` for the first time since the problem
started.

Second boot: FAT check idempotent (0 restored, 75 unrepairable, 110 benign
mismatches, 979 ms); six more directories repaired as downloads reached
them (`vault/22/55`, `vault/10/50`, `vault/55/24`, `vault/41/14`,
`museum/cma/49/37`, `museum/cma/10/1`); every failed download was redone;
no latch; the recreated `channel/` directory parses clean and FatFS sees all
16 files in it. `lost/` lists the quarantined folders. The banner markup is
served and the flags reach the UI.

Third boot (final build, path-preserving quarantine names): 40 forced
artwork swaps drove downloads into six more damaged shards
(`museum/cma/15/1`, `vault/4/11`, `giphy/35/34`, `museum/ham/9/4`,
`vault/8/41`, `vault/39/19`), each quarantined as
`lost/<path>-<n>` and recreated; 14 repairs in total, no latch, no other
error lines in the log.

Not exercised on the device: the ancestor case (a shard parent directory
damaged so that a child is invisible), the `fs_atomic_write_cb` retry path
(only the rename path fired), and the format-resets-counter path.

## Known limits and follow-ups

- 75 FAT sectors (about 600 MB of cluster space) are junk in both copies;
  files whose chains pass through them are lost, and allocation avoids them.
  Only a format reclaims that space. The same goes for directories already
  quarantined into `lost/`: their clusters stay allocated until a PC deletes
  the folder or the card is formatted.
- The FAT mirror check costs about one second per boot on a 64 GB card
  (15 MB of reads). It could be sampled or skipped when FSInfo is clean if
  boot time matters.
- A damaged directory is only repaired when something tries to write into
  it. Artwork in never-written shards stays unreachable but harmless.
- The card will keep misplacing blocks. When you are back home: swap in the
  known-good card and let the device run a day; zero repairs there and
  continued repairs on this card close the case. A PC `chkdsk /f` over USB
  export would also show the cross-linked leftovers.
- The mitigation is on a feature branch; it needs your merge decision and a
  release with the web UI bump.
