# Jitter work stream

Goal was to eliminate sporadic 100-800 ms playback stalls with zero overhead
in release builds. `REPORT.md` is the standalone summary: causes, fixes,
evidence. This file holds what is still needed to maintain the result: the
one open item, the diagnostic builds, and the lab tooling.

## Status

Done. Merged to `main` 2026-08-30 (`f65f1dd4`): fixes 1-9, the Phase 6
catch-up re-baseline in `main/display_renderer.c`, the frame trace and the
host lab. Pass bar met on the release config with only
`CONFIG_P3A_FRAME_TRACE=y` added: 3.06 h, 0 stalls >= 100 ms, p99 lateness
36.7 ms.

One item stays open: fix 8 (`components/sd_idle_wait`) works around an
ESP-IDF driver behaviour reported upstream as
[esp-idf #19034](https://github.com/espressif/esp-idf/issues/19034).
Espressif's revised patch (v2, back-off capped at one tick) tested OK on the
dev unit on 2026-09-03 and Fab approved it for master; a `release/v5.5`
backport was requested. The comparison of their patch against fix 8 is in
`espressif-patch/README.md`.

## When #19034 lands in an IDF release

The wrap is harmless on top of a fixed IDF (it shadows the fixed function),
so nothing breaks if the IDF moves first. When a release carries the fix:

1. Upgrade the workstation IDF to that release (AGENTS.md: `ESP_IDF_VERSION`
   major.minor, P4 rev-v1.0 `sdkconfig` guards must survive).
2. Confirm at runtime: a diag build's `/api/debug/frames/stats` -> `config`
   -> `idf_sdmmc_backoff_patch=true`. Detection is a weak reference to the
   patch's `sdmmc_poll_delay_and_backoff` in
   `components/sd_idle_wait/sd_idle_wait_info.c`; rename it there if
   upstream renamed the symbol.
3. Drop the wrap: flip `P3A_SD_IDLE_WAIT_WRAP` to default n and keep the
   option and the identity helpers (decided 2026-09-02: the Kconfig stays,
   so the stock-vs-wrap comparison can always be rebuilt).
4. Re-soak with the procedure in `espressif-patch/README.md` (arm
   reproducer, zero-margin probe, 3 h Work mix soak, `run_audit.py`). Pass
   bar: no in-scope presented-frame lateness >= 100 ms. Reference numbers
   for the v2 patch are in that file's Round 2 table.
5. Bump `PROJECT_VER`, add a release-notes bullet, post a closing note on
   the issue.

## Rules for this stream

- **Release builds carry no overhead.** All instrumentation is behind
  `CONFIG_P3A_FRAME_TRACE` (default n). Heavier probes live only in
  `sdkconfig.diag.defaults`. Do not fold diag or trace options into the
  release `sdkconfig`. Any regeneration must keep
  `CONFIG_ESP32P4_SELECTS_REV_LESS_V3=y` + `CONFIG_ESP32P4_REV_MIN_1=y`.
- **Automation first.** The agent builds, flashes, monitors, runs soaks, pulls
  data, and analyzes on its own. Fab is consulted only for decisions or physical
  actions. Keep Fab informed: chat summary at each phase milestone; push
  notification when a soak yields an attributed stall, a fix is ready for his
  eyes, or work is blocked. Durable findings go into `REPORT.md`.
- **Device is fair game, restore afterwards.** Any runtime setting, playset,
  upload, reboot or flash is allowed on the dev unit; snapshot settings before a
  run and restore after. Never `erase-flash`, never touch NVS contents
  (Wi-Fi, Makapix registration, API keys live there).
- **Never put API keys in docs or run archives.** `GET /config` returns Giphy,
  Klipy, HAM and SI keys in the clear; tooling redacts `*_api_key` fields.
- Out of scope: producer overrun (artworks too heavy to decode in time) and
  60 Hz quantization judder.

## Environment facts

| Item | Value |
|------|-------|
| Dev device UART | **COM5** (CH343 bridge, 115200). Opening it with .NET `SerialPort` or plain `idf.py monitor` **resets the board**; `host/jitter-lab/serial_logger.py` does not. `idf.py flash` needs COM5 free: stop the logger first |
| USB-Serial-JTAG | not wired to the laptop; no OpenOCD/SystemView. In-firmware tracing only |
| Device LAN name | `http://p3a-fab.local`. **`p3a.local` is a different device**: tooling refuses any host whose `/api/device-name` hostname is not `p3a-fab` |
| SD root | `sdcard_root = /p3a2` (not the default `/p3a`) |
| Panel | 720x720 @ 60 Hz (`VSYNC_PERIOD_US 16667` in `main/display_renderer.c`) |
| SD card / bus | slot 0, 4-bit, `SDMMC_FREQ_HIGHSPEED` (40 MHz); TOPESEL 32 GB UHS-I, busy 1-45 ms after a single-block write |

## Frame trace (`components/frame_trace`)

Zero code and data when `CONFIG_P3A_FRAME_TRACE` is off; when on, a few
dozen ns per record, no allocation and no logging in the hot path.

- **Ring.** PSRAM, `CONFIG_P3A_FRAME_TRACE_ENTRIES` x 56 B, lock-free
  multi-writer (atomic fetch-add on the sequence, entry published by storing
  its seq last). Two record kinds:
  - **FRAME**, written by the consumer at `esp_lcd_panel_draw_bitmap`:
    target and present time, duration, generation, queue depth, vsync wait,
    and the producer's decode/upscale/free-buffer-wait/produce-end times
    carried in `ready_frame_t` (`main/display_renderer_priv.h`). Derived:
    `lateness = present - target` (the jitter metric) and
    `ready_margin = target - produce_end` (negative means the producer was
    late: overrun, out of scope, flagged and excluded from the pass bar).
  - **MARK**, from any task via `frame_trace_mark(kind, phase, arg)`: SD
    read/write spans, flash ops, NVS commits, loader loads, downloads, cache
    refreshes, verify sweeps, HTTP requests, MQTT receives, swaps, resyncs,
    slow log calls, provocations, user marks (`ft_mark_kind_t` in
    `frame_trace.h`).
- **Stall detector and UART report.** The consumer only posts; a reporter
  task on core 0 at priority 2 prints one `JTR|` block per stall (rate
  limited) with the recent FRAME/MARK history and, in diag builds, the
  per-task run-time delta. Format in `host/jitter-lab/README.md`. Limitation:
  the delta compares against the reporter's last periodic snapshot, so a task
  created and deleted inside the window is invisible.
- **HTTP** (`components/http_api/http_api_rest_debug_frames.c`, 404 when the
  trace is off): `GET /api/debug/frames?since=<seq>` (CSV),
  `GET /api/debug/frames/stats`, `POST /api/debug/frames/reset`,
  `POST /api/debug/mark`, and with `CONFIG_P3A_FRAME_TRACE_DEV_ENDPOINTS`
  the provocations under `POST /api/debug/provoke`.
- **Overlay.** The FPS overlay adds the worst lateness of the last 10 s and a
  red tick for 2 s after a recorded stall.

## Diagnostic builds

Both overlays apply on top of the tracked release `sdkconfig` into a separate
build directory; the release file is never modified.

| Overlay | Contents | Use |
|---------|----------|-----|
| `sdkconfig.diag.defaults` | frame trace (32768 entries), dev provocation endpoints, FreeRTOS trace facility + run-time stats (`JTR\|T` attribution) | investigating a regression |
| `sdkconfig.trace.defaults` | frame trace only | confirming the pass bar on a build whose only delta from release is the trace |
| `sdkconfig.nowrap.defaults` | `P3A_SD_IDLE_WAIT_WRAP=n`, stacked on diag | measuring stock IDF or an IDF-side fix |

`host/jitter-lab/build.ps1 -Diag` builds into `build-diag/`
(`-DSDKCONFIG=build-diag/sdkconfig -DSDKCONFIG_DEFAULTS="sdkconfig;sdkconfig.diag.defaults"`);
`-Extra <overlay> -Suffix <name>` stacks another overlay into
`build-diag-<name>/`. It guards that the release `sdkconfig` is unchanged and
the rev-v1.0 lines are present, and prints an `ARM:` line saying which SD
busy-wait variant the binary carries. Put the dev unit back on a release
build from `main` when done (`/api/debug/*` must return 404).

## Lab tooling (`host/jitter-lab/`)

`host/jitter-lab/README.md` documents every tool, the device endpoints and
the UART report format. Short form:

```powershell
pwsh host/jitter-lab/build.ps1 -Diag -Flash            # needs COM5 free
$run = pwsh host/jitter-lab/soak.ps1 -NewRunId
pwsh host/jitter-lab/soak.ps1 -Start -Run $run -Hours 3 -Note "Work mix"
pwsh host/jitter-lab/soak.ps1 -Stop -Run $run            # final pull + analyze -> runs/$run/report.md
python host/jitter-lab/snapshot_settings.py restore $run
python host/jitter-lab/compare_runs.py <A> <B>
```

Run data and `report.md` stay local in `host/jitter-lab/runs/<RUN-ID>/`
(gitignored). Per-run notes are not committed; results that matter go into
`REPORT.md`.
