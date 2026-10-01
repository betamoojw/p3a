# Directory Structure

Top-level layout of the repository. For what each component does, see
[components.md](components.md); for the files inside a folder, list the folder.

| Path | Contents |
|------|----------|
| `main/` | Application component: boot (`p3a_main.c`), LCD/touch/USB init, display renderer and upscalers, on-screen overlays, animation player, playback controller, service wrappers (`*_service.c`), `Kconfig.projbuild` |
| `components/` | The 32 project components (state machine, scheduler, channels, content sources, decoders, networking, OTA, board HAL). One folder per component, public headers in `include/` |
| `webui/` | Web UI packed into the LittleFS image: HTML pages, `static/` (CSS, theme switcher, icons, generated `compat.js`), `museum/` (browse adapters for the playset editor), `setup/` (captive portal), `pico8/` |
| `docs/` | Documentation; the map is in `AGENTS.md` |
| `host/` | Host-side tools: `intro-anim-lab/` (build and preview boot animations on Windows), `jitter-lab/` (serial logger and port finder) |
| `scripts/` | Development helpers: asset converters, museum term/set builders, stress and memory test scripts |
| `flasher/` | Optional Windows flasher, built with `-DP3A_BUILD_FLASHER=ON` |
| `certs/` | Provisioning certificate authority material |
| `images/` | Photos, brand assets, screenshots, UI icon sources, board imagery |
| `reference/` | Third-party reference material kept for development (museum APIs) |
| `requests/` | Self-contained investigation requests with their scripts and reports |
| `release/` | Per-version release binaries (git-ignored, filled by every build) |
| `build/` | Build output (git-ignored) |
| `managed_components/` | Components downloaded by the IDF component manager (git-ignored) |

## Key files

- `CMakeLists.txt` (root): version variables (`PROJECT_VER`, `WEBUI_VERSION`,
  `P3A_API_VERSION`), LittleFS image creation, release packaging hook.
- `partitions.csv`: flash layout (NVS, dual OTA, LittleFS web UI, slave firmware).
- `sdkconfig`: release ESP-IDF configuration. `sdkconfig.*.defaults` are
  alternate configurations for diagnostic builds.
- `dependencies.lock`: pinned versions of ESP-IDF and managed components.
- `AGENTS.md` / `CLAUDE.md`: guidance for AI coding agents.
