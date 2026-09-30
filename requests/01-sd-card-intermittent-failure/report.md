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

## Overnight soak (2026-09-28 22:00 to 2026-09-29 06:00) and follow-up fixes

Setup: device on the diagnostic build, reset-free serial logger on COM5,
`soak_monitor.py` snapshotting `/status` and hashing both FAT copies every
30 minutes (16 snapshots, `logs/soak/`).

Three defects in the first cut surfaced within the first hour and were
fixed, rebuilt, reflashed and re-verified the same night (commit
`d2e83972`):

1. **False 404 tombstones.** `fs_atomic` reported a repaired directory as
   `ESP_ERR_NOT_FOUND`, the code `http_fetch` uses for HTTP 404, and the
   download manager wrote a `.404` marker next to the artwork whose download
   had triggered the repair. Markers only die through age-based eviction, so
   124 artworks would have stayed skipped for days. Now `ESP_ERR_NOT_FINISHED`
   (a plain transient failure); the 124 false markers were removed from the
   card with a new root-scoped `GET /api/debug/sd/unlink` (diagnostic build
   only, `clean_false_404.py`).
2. **Short probe, false negative.** The probe file name fitted a single
   directory entry and could land in a stray free slot ahead of the junk, so
   `vault/5/51` (phantom zone at index 106) kept failing every time without
   being repaired. The probe now needs six contiguous entries, like the
   artwork names p3a writes.
3. **Endless directory table, EACCES.** A directory whose cluster chain runs
   into FAT junk becomes a 36-cluster, 73,000-entry garbage table
   (`museum/ham/52/0`); FatFS refuses creates there with FR_DENIED (EACCES),
   not ENOENT, and `http_fetch` opens its temp file itself, bypassing
   `fs_atomic`. EACCES now triggers the heal, the heal falls back to a
   `readdir` scan (non-ASCII names, or a table that does not end within
   2048 entries) when the create probe cannot run, and `http_fetch` heals and
   retries its open. Path buffers in `sd_repair` moved to the heap for the
   small-stack download tasks.

Results of the 9 hours on the fixed build:

- 59 more directories repaired (203 on the card by morning; 205 after the
  release-build check): 32 Giphy, 14 Klipy, 10 vault, 3 museum shards; 57
  by the phantom probe, 2 by the enumeration scan. No heal failure, no
  write failure reached `sd_health`, latch never tripped, free space stable
  (46 GB).
- FAT drift: none. Across 16 snapshots neither FAT copy changed on one side
  only and no new junk appeared; every change was a normal FatFS allocation
  mirrored in both copies. While powered, the card misplaced nothing all
  night, which fits damage at power loss (card-internal housekeeping).
- One reboot at 04:02, unrelated: Wi-Fi dropped, the C6 stack would not
  re-initialize, and the existing `wifi_recovery` escalation rebooted the
  device after three attempts.
- Two cached artworks failed to read or decode (`giphy/32/29`,
  `vault/20/54`), most likely chains through the 75 unrepairable FAT
  sectors; the existing corrupt-file handling deleted them for re-download.
- Side observation: 46 Minneapolis (artsmia) image requests returned
  HTTP 403 overnight. Investigated 2026-09-29: not a block on p3a. Every
  such object also 403s from a PC on all three size buckets with an S3
  AccessDenied body, meaning the rendition was never generated even
  though the search index marks the image valid. This is the known Mia
  data gap (139 of 2574 public-domain Paintings today, up from 40 of
  1024 in August; upstream issue artsmia/collection-elasticsearch#10,
  still unanswered). The download tombstone handled it as designed: 55
  entries tombstoned after 5 attempts each. The logs look worse than
  the 5% rate because cached artworks are never re-requested, so the
  download loop keeps cycling through the dead tail.

Release-configuration build (`build-rel/`, tracked `sdkconfig`, no debug
overlay) flashed in the morning: `/api/debug/sd/*` returns 404, the boot FAT
check runs in 980 ms, directories repair on the fly, `/status` and
`/playsets/active` carry the counters, the web UI banner is served. Silicon
revision guards intact. The local `release/v1.2.3/` folder, overwritten by
every build (the CMake copy step is unconditional), was restored
byte-identical from the GitHub release.

Still untested: format resetting the persisted repair counter, and the A/B
with a known-good card.

## A/B test, 2026-09-29

Same device, same firmware (diagnostic build of the branch), same SD root
setting, same download traffic driven by a swap loop.

**New card** (32 GB, fresh out of the box, FAT32 as shipped, 16 KB clusters;
manufacturer id 111, name "SDABC", serial 2852129421):

- Mounted directly; boot FAT check 0 mismatched sectors; folders created.
- 20 minutes of downloads (288 files, 41 MB): 0 repairs, 0 anomalies in
  349 directories, no write failures. The FAT monitor saw one transient
  copy-1/copy-2 difference in the hottest FAT chunk that was gone on
  re-read (a write caught between the two copies), no drift.
- Three power cuts during active downloads (unplug, 5 s, replug; four boots
  recorded): every boot's FAT check clean (0 mismatched, 0 restored,
  0 unrepairable), 0 repairs, 310 files across 369 directories, 0 anomalies.

**Old card** (64 GB, manufacturer id 254, name "SD", serial 249): before the
swap it carried 111 mismatched FAT sectors (75 junk in both copies) and 217
quarantined directories. The move to the new Wi-Fi (one power cut) added no
FAT damage. Matched three-cut test: see below.

**Old card, matched three-cut test** (same swap loop running): every boot's
FAT check unchanged (111 mismatched, 75 unrepairable, 0 restored), no new
repairs, 217 quarantined folders before and after. Quick cuts during
downloads did not add FAT damage.

**Directory-level check.** The 217 directories the repair had recreated
overnight were known-clean at recreation. Scanned this morning after the
move and the first cut round, 11 of them carried junk again (32 KB and 48 KB
runs, at 16 KB-aligned absolute addresses, no FAT chain pointing at them, FAT
unchanged: the card's signature, not a cross-link from the FAT repair; in 8
of the 11 the junk sits past the end marker and does not affect FatFS).
The damage window covers the night on power, the laptop move (one power
cut) and the first three cuts. A second round of three cuts, bracketed by a
hash snapshot of all 216 directories, produced nothing new: 200 identical,
15 changed only by FatFS adding files, 1 already-damaged directory re-parsed
differently. So a quick unplug during downloads does not reproduce the
mechanism on demand; the card damages itself at moments this test did not
capture (candidates: its own background housekeeping while idle or
unpowered for longer, or a slower power decay than a 5-second cut).

**A/B verdict.** Identical device, firmware, traffic and abuse: the new card
finished with 0 damaged directories out of 369 and a clean FAT; the old card
carries 224 quarantined directories, 75 FAT sectors junk in both copies, and
acquired 11 new junk blocks in the 12 hours between the overnight repair and
this morning. The old card is the fault. The self-repair kept the device
working throughout: no latch, no user-visible failure, caches refilled.
Repairs since boot on the old card kept landing on shards that had never been
written since the original damage (Klipy and Giphy shards), as expected.

## On-screen notice (added 2026-09-29 before the merge)

A once-per-boot message box ("SD card repaired. The card is corrupting
data. Back it up and replace it. Details in the web UI.", 20 s TTL) is armed
by the first directory quarantine of the boot or by a boot FAT check that
rewrote sectors, and consumed by the render loop through the same pull model
as the existing SD-failure notice. It ranks above channel errors and below
the failure notice. Verified on the device by code path and by the repair
counter firing twice on the release-configuration build (12:09 and 12:36),
and the web UI banner was seen; nobody was watching the screen at those
moments, so the rendering itself is not visually verified. It reuses the
render path of the SD-failure notice, which is.

### Defect found 2026-09-30: the notice repeated on every repair

Fab saw the message box on the device, several times in one boot. The flag
was set by every directory quarantine and again by the boot FAT restore, and
nothing remembered that the notice had already been armed, so each repair
raised it anew (`/status` at 184 s uptime: two quarantines plus a FAT restore
of 37 + 28 sectors). The sibling SD-failure notice never had the problem
because its flag sits inside the write-once failure latch.

Fix: a write-once latch in `sd_repair.c` gates both arming sites. The first
repair of the boot arms the notice; later repairs only move the counters. An
on-device format clears the latch with the persisted total (both format
paths reboot today, so this has no visible effect yet). `p3a_render` logs
`SD repair notice raised` at INFO when it shows the box.

Device, release configuration, serial capture of the first 5 minutes after
flashing: quarantines at 105 s (`giphy/48/8`) and 128 s (`klipy/gif/41/33`),
one `SD repair notice raised` line at 105 s, none for the second repair,
which landed after the first notice's 20 s had run out and would have raised
a second box before the fix. The boot FAT check restored nothing on that
boot, so the path where the FAT restore arms the notice and a later
quarantine stays silent was not exercised. Not yet confirmed by eye on the
screen.

Still open: the 20 s is an upper bound. A successful artwork swap clears the
message slot, so a notice armed by the boot FAT restore may be dismissed by
the first swap. To be judged on the device before changing anything.
