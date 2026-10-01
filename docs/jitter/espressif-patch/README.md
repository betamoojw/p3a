# Espressif patch evaluation (esp-idf #19034)

Espressif answered [esp-idf #19034](https://github.com/espressif/esp-idf/issues/19034)
with a patch for v5.5.4 and asked us to test it. This folder records the
comparison against p3a's fix 8 (`components/sd_idle_wait`, one CMD13 poll per
FreeRTOS tick) and keeps the patch so the test can be re-run.

## The patches

- **v1** (2026-09-02): exponential back-off from 100 us doubling to a 32 ms
  cap; delays shorter than one tick are `esp_rom_delay_us()` spins, longer
  ones `vTaskDelay()`. Patched all three busy loops (`sdmmc_wait_for_idle`,
  the init data-ready wait, the tuning-block read) and added
  `CONFIG_SD_READY_POLL_PERIOD_START_US`. Not kept in the tree.
- **v2** (2026-09-03, `patch/sdmmc_back_off_between_CMD13_polls_v2_v5.5.4.patch`):
  same start, but spins only while below one tick, then one `vTaskDelay(1)`
  per poll; both the delay and the configured start period are clamped to a
  tick (Kconfig range 1-10000 us). At 1000 Hz this is fix 8 plus
  100/200/400/800 us spins before the first yield. This is the version
  approved for master.

Apply to a clean v5.5.4 tree with
`git -C <idf> apply <patch>`; restore with
`git -C <idf> checkout -- components/sdmmc` and delete the new
`components/sdmmc/Kconfig`. Never run a release build while the IDF tree is
patched: the release `sdkconfig` would gain
`CONFIG_SD_READY_POLL_PERIOD_START_US` (`build.ps1` throws on any release
`sdkconfig` change).

## Arms

All **diag** flavour (release `sdkconfig` + `sdkconfig.diag.defaults`),
differing only in the busy-wait:

| Arm | Build dir | IDF tree | `CONFIG_P3A_SD_IDLE_WAIT_WRAP` | Device reports (`/api/debug/frames/stats` -> `config`) |
|-----|-----------|----------|-------------------------------|------------------------------------------------------|
| `stock` | `build-diag-nowrap/` | clean | n (`sdkconfig.nowrap.defaults`) | `sd_idle_wait_wrap=false, idf_sdmmc_backoff_patch=false` |
| `patch` | `build-diag-patch/` | patch applied | n | `sd_idle_wait_wrap=false, idf_sdmmc_backoff_patch=true` |
| `wrap` (ours, = main) | `build-diag/` | clean | y (default) | `sd_idle_wait_wrap=true, idf_sdmmc_backoff_patch=false` |

Arm identity is proven twice: `build.ps1` prints an `ARM:` line from the map
file (`__wrap_sdmmc_wait_for_idle`, `sdmmc_poll_delay_and_backoff`) and the
device reports the same two facts at runtime (`sd_idle_wait_info.c`, weak
reference to the patch's new symbol). `arm_reproducer.py --arm X` and
`zm_reproducer.py --arm X` refuse to run if the device does not match.

Build every clean-tree arm before patching the IDF, then flash with
`build.ps1 -FlashOnly`, which flashes the build dir's `flash_args` with
esptool and never re-runs ninja (a plain `-Flash` or `idf.py flash` would
rebuild against the current tree state).

Procedure per arm: `arm_reproducer.py` (bar GIF, SD write matrix; the
PSRAM-misaligned 32 KB condition is the poll-storm reproducer),
`zm_reproducer.py` (zero-margin artwork under paced writes), then a soak on
the Work mix playset (`soak.ps1`, `analyze.py`, `run_audit.py`,
`compare_runs.py`). External resets (USB-C cable, brownout) do not
invalidate a run; `run_audit.py` separates them from firmware resets.

## Results

| | stock | patch v1 | patch v2 | wrap (ours) |
|---|---|---|---|---|
| Reproducer (misaligned 32 KB bounce storm): producer anomalies / upscale max | 12 / 479 ms | 0 / 22 ms | 0 / 22 ms | 0 / 18 ms |
| Soak, Work mix: stalls >= 100 ms / hours | (not run) | 0 / 3.30 h | 0 / 1.08 h | 2 / 3.43 h (one event, see below) |
| Soak lateness p99 / max | | 39.1 / 77.2 ms | 18.5 / 74.9 ms | 42.0 / 231.9 ms, then 34.3 / 75.4 ms |
| SD write spans over the soak: p90 / p99 | | 52.5 / 57.5 ms | 36.0 / 44.5 ms | 35.6 / 44.3 ms |
| Upload stress: anomalies / stalls | | 0 / 0 | | 0 / 0 |
| Zero-margin probe: decode under every write condition | | | flat 63 ms, 0 anomalies | flat 64 ms, 0 anomalies |
| Write medians, internal 512 B / aligned 512 B / internal 32 KB / aligned 32 KB (ms) | 0.7 / 2.3 / 2.7 / 4.5 | 0.9 / 4.9 / 4.9 / 6.0 | 1.1 / 2.5 / 3.4 / 4.7 | 2.5 / 2.9 / 3.9 / 5.0 |

The wrap soak's one stall event is a producer-bound artwork meeting download
writes plus loader reads queued behind them. The zero-margin probe shows the
wrapper's one-poll-per-tick traffic does not inflate a saturated decoder, and
loader reads never enter `sdmmc_wait_for_idle()`, so the event is not a
property of either busy-wait; the patch soak simply never drew that artwork.
It stays on the books as a residual class, to be probed separately.

## Decision (2026-09-02, confirmed with v2 on 2026-09-03)

**p3a keeps fix 8 (the once-per-tick wrapper) until an ESP-IDF release
carries Espressif's fix; then the wrap comes out and the Kconfig stays.**
The follow-up checklist is in `../README.md`.

- Both approaches kill the poll storm completely on this hardware; the
  soaks are equivalent on stalls.
- v1 had a worse write-completion tail for our workload (32 KB download
  writes on a card busy 20-45 ms): p99 57 vs 44 ms. v2's one-tick cap
  closes that gap and its spins fix the wrapper's only weakness, the
  tick-size overshoot on sub-millisecond busy periods.
- The wrapper is what v1.2.1 shipped and has field time; a patched IDF tree
  is not something a public project can ask its builders to carry.
- Told Espressif: v2 is good to merge; asked for a `release/v5.5` backport.
