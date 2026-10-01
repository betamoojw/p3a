# ESP-IDF 6.0 migration

**Status:** Deferred. Evaluated 2026-05-16 against v6.0.1; status line
reviewed 2026-10-01. Baseline is ESP-IDF v5.5.4 (LTS); nothing migrated.

## Why deferred

v6.0 is a maintenance migration: nothing in it unblocks a p3a feature, and
v5.5 is an LTS line that keeps receiving fixes until 2027. The work is
estimated at one to two weeks, most of it outside p3a's own code.

## What p3a's own code needs

A grep of every symbol the v6.0 migration guide lists as removed found no
direct hits. The known edits are small:

- **Silicon revision.** v6.0 raises the default minimum to rev 3.0. p3a
  already sets `CONFIG_ESP32P4_SELECTS_REV_LESS_V3=y` and
  `CONFIG_ESP32P4_REV_MIN_1=y` (required since IDF 5.5.2); keep them.
- **mbedTLS 4 / PSA Crypto.** Call `psa_crypto_init()` in `app_main()` before
  any TLS. Re-test every endpoint (Makapix MQTT, Giphy, Klipy, each museum
  host, GitHub Releases): v6.0 drops deprecated CAs and non-forward-secret
  cipher suites. `esp_http_client` grows by about 37 KB of flash.
- **`esp-mqtt` moves to the registry.** Add the `espressif/mqtt` dependency;
  the API is unchanged.
- **GCC 15, warnings as errors, orphan sections as errors.** Expect a cleanup
  pass across the components. `CONFIG_COMPILER_DISABLE_DEFAULT_ERRORS=y` is
  the escape hatch for a first build.
- **Picolibc replaces Newlib by default.** stdio is global, not per task;
  `CONFIG_LIBC_NEWLIB=y` restores the old behavior if something breaks.
- **Re-evaluate workarounds:** `components/animation_decoder/idf_jpeg_release_null_fix.c`
  (patches the IDF JPEG driver's release path, may collide with v6.0
  internals), the HW JPEG dimension gate in `jpeg_animation_decoder.c`, the
  Rijks 3xx comment in `rijksmuseum.c`, and the `idf::libjpeg-turbo` alias
  workaround in the root `CMakeLists.txt`.
- **Component bumps:** `esp_wifi_remote` (1.2.2 locked; 1.5.x ships v6.0
  Kconfig fragments), `esp_tinyusb` (1.7.6 locked; v6.0 likely needs 2.0.x,
  read its release notes), `littlefs` optional.

## External blockers

- **Waveshare BSP** (`waveshare/esp32_p4_wifi6_touch_lcd_4b`, 1.0.1 locked).
  v6.0 changes the `esp_lcd` panel-config structs, which p3a reaches only
  through the BSP and the ST7703 driver. Without a v6.0-compatible BSP release
  the options are to wait or to fork the BSP.
- **`esp_hosted` stays on 2.9.x** (`~2.9.3` in `main/idf_component.yml`).
  2.9.x builds on v6.0, so this is not a migration blocker. Newer lines
  preallocate about 47.6 KB of DMA-capable internal RAM for the SDIO mempool
  ([esp-hosted-mcu#191](https://github.com/espressif/esp-hosted-mcu/issues/191)),
  which this sdkconfig cannot spare. Any bump is its own work stream, tied to
  the SDIO RX entry in `docs/known-issues.md`.

## Revisit when

- Waveshare publishes a v6.0-compatible BSP, and
- a v6.0.x bugfix release has settled, or v5.5 LTS end of life approaches, or
  a v6.0 capability (for example Picolibc's smaller binaries) is wanted.

First step when picked up: on a branch, apply the mechanical edits above and
try a build with default errors disabled, to see the real blocker list.
