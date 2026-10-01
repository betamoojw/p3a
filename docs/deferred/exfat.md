# exFAT support (mount-only)

**Status:** Deferred (evaluated 2026-07-27, nothing implemented).
**Scope:** Mount factory-formatted exFAT cards read/write. The on-device
formatter keeps producing FAT32; no exFAT formatting anywhere.

## Why it comes up

SDXC cards (above 32 GB) ship formatted as exFAT. p3a cannot mount them: the
user gets the "No Usable SD Card" screen, and the only on-device fix is a
destructive FAT32 format. On a computer, Windows' own Format dialog caps FAT32
at 32 GB, so users need guiformat or Rufus (see the caveat in
`docs/HOW-TO-USE.md`). Small cards are getting harder to buy, so more first-run
users will hit this over time.

## What it would take

Nothing in p3a's own code is FAT32-specific (mount via the BSP's
`esp_vfs_fat_sdmmc_mount()`, free space via `esp_vfs_fat_info()`, rename-based
`fs_atomic`, I/O-driven `sd_health`). The blocker is that ESP-IDF hardcodes
`FF_FS_EXFAT 0` in `components/fatfs/src/ffconf.h` with no Kconfig switch.
Espressif declines to enable it for patent reasons
([esp-idf#6601](https://github.com/espressif/esp-idf/issues/6601)).

1. Shadow the IDF `fatfs` component in `components/fatfs/` (same pattern as
   the `components/espressif__libpng` fork) and set `FF_FS_EXFAT 1`. LFN is
   already on; no other config changes.
2. **Pin the formatter to FAT32.** IDF's `vfs_fat_sdmmc.c` passes `FM_ANY` to
   `f_mkfs` at both format sites; with exFAT compiled in, FatFs picks exFAT for
   volumes of 32 GiB and up. Change both to `FM_FAT | FM_FAT32`, or the
   on-device formatter silently starts producing exFAT.
3. Update the FAT32 wording in `docs/HOW-TO-USE.md`, the `sd_format.h`/`.c`
   headers and the probe comment in `main/sd_format.c`. The probe logic itself
   needs no change: exFAT cards would simply take the "card OK" path.
4. Device tests: factory-exFAT card end to end (vault, downloads, eviction,
   playback), formatter still FAT32 on a >32 GB card, NTFS card still offered
   a format, power-cut soak while caching, USB-MSC round trip.

Measured cost: +7.3 KiB flash (`ff.c`), negligible RAM (a few dozen bytes per
handle plus ~608 B per mounted volume). The functional diff is about 3 lines.

## Risks and costs

- A permanent fork of a core IDF component, re-applied on every IDF bump.
  Losing the `FM_ANY` pin in a re-sync would silently change formatter output.
- A configuration Espressif does not test; any VFS-glue exFAT bug is ours.
- The fleet splits into two on-card formats, doubling the SD test surface.
- Probably less robust than FAT32 as p3a formats it: exFAT keeps one FAT plus
  a bitmap, FAT32 keeps two FATs, and `sd_repair` restores FAT1 from FAT2.
- Patent exposure if devices are ever sold (FatFs's application note says
  commercial products may need a Microsoft license).

## Why deferred

The on-device FAT32 formatter (shipped 1.1.1) already unblocks every card,
destructively. Mount-only exFAT only adds "big store-bought cards, including
ones holding data, work with no wipe". That is a nice-to-have for today's
builder-heavy audience.

## Revisit when

- Field reports show users reaching the No-Usable-SD screen with cards that
  carry data they want to keep, or
- An outreach wave is about to put units or instructions in front of
  non-tinkerers.

If triggered, implement exactly as scoped here and document the fork diff in
`components/fatfs/README.md`, following the libpng fork's README.
