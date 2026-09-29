# Boot log evidence, 2026-09-28 (firmware 1.2.3, reboot via /action/reboot)

Captured reset-free on COM5 with the jitter lab's serial_logger.py. Host
timestamps stripped; device millisecond ticks kept. Lines chosen: everything SD-related
from reset to the latch.

```
rst:0xc (SW_CPU_RESET),boot:0xf (SPI_FAST_FLASH_BOOT)
I (1433) channel_cache: Channel cache subsystem initialized
I (2142) sdmmc_periph: sdmmc_host_init: SDMMC host already initialized, skipping init flow
I (2194) sd_path: Using configured root: /sdcard/p3a2 (from user path: /p3a2)
I (2200) sd_path: SD directories ensured under /sdcard/p3a2
I (2294) sd_health: boot probe OK (/sdcard/p3a2/.sdh_probe)
I (2300) dl_mgr: Waiting for WiFi...
I (2407) channel_cache: No cache for 'Promoted', starting empty (server refresh will populate)
I (2424) channel_cache: No cache for 'm o n s t e r', starting empty (server refresh will populate)
I (2441) channel_cache: No cache for 'Fab', starting empty (server refresh will populate)
I (2457) channel_cache: No cache for 'Giphy: Trending', starting empty (server refresh will populate)
I (2475) channel_cache: No cache for 'Klipy: Trending', starting empty (server refresh will populate)
I (2493) channel_cache: No cache for 'HAM · Oil', starting empty (server refresh will populate)
I (2511) channel_cache: No cache for 'CMA · Painting', starting empty (server refresh will populate)
I (2529) channel_cache: No cache for 'Mia · Paintings', starting empty (server refresh will populate)
I (14769) giphy_refresh: Full refresh: evicted 0 orphaned entries, 254 kept
E (14871) fs_atomic: Rename failed: /sdcard/p3a2/channel/4aaf9a86f603b8b5.json.tmp -> /sdcard/p3a2/channel/4aaf9a86f603b8b5.json (errno=2)
W (14874) sd_health: SD write failure 1/3: /sdcard/p3a2/channel/4aaf9a86f603b8b5.json (errno=2)
W (14881) giphy_refresh: Failed to save channel metadata: ESP_FAIL
I (22503) cache_evict: Full refresh: evicted 0 orphaned entries, 304 kept (channel 'Promoted')
E (22585) fs_atomic: Rename failed: /sdcard/p3a2/channel/8b3f17902d72addd.cache.tmp -> /sdcard/p3a2/channel/8b3f17902d72addd.cache (errno=2)
W (22589) sd_health: SD write failure 2/3: /sdcard/p3a2/channel/8b3f17902d72addd.cache (errno=2)
E (22595) channel_cache: Failed to save cache '8b3f17902d72addd': ESP_FAIL
W (22602) makapix_channel_refresh: Cache flush failed for '8b3f17902d72addd', skipping metadata save
I (22937) cache_evict: Full refresh: evicted 0 orphaned entries, 223 kept (channel 'm o n s t e r')
E (23019) fs_atomic: Rename failed: /sdcard/p3a2/channel/54e1e0fc822ad732.cache.tmp -> /sdcard/p3a2/channel/54e1e0fc822ad732.cache (errno=2)
W (23023) sd_health: SD write failure 3/3: /sdcard/p3a2/channel/54e1e0fc822ad732.cache (errno=2)
E (23029) sd_health: SD CARD FAILURE latched (consecutive write failures) - writes/downloads disabled until reboot
E (23039) channel_cache: Failed to save cache '54e1e0fc822ad732': ESP_FAIL
W (23048) makapix_channel_refresh: Cache flush failed for '54e1e0fc822ad732', skipping metadata save
I (23140) giphy_dl: Aborting download: SD card exported to USB host
I (23264) dl_mgr: Waiting for SD card...
```

Observations:

- The card mounts and the root-directory boot probe (create, fsync, rename, read back, delete) passes.
- No sdmmc, diskio or FatFS disk-error line appears anywhere in the boot: no CRC, no timeout, no EIO.
- Every failure is rename() inside /sdcard/p3a2/channel/ returning errno 2 (ENOENT) right after
  the temp file in the same directory was created, written and fsynced without error.
- Three such failures latch sd_health at 23.0 s after reset; playback continues from cache.
