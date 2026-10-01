# Set up ESP-IDF v5.5.4 on Windows

How to install the p3a toolchain on a Windows machine with Espressif's
Installation Manager (EIM) and build the firmware. All project-side settings
(`sdkconfig`, `dependencies.lock`, the `slave_ota` esptool fix) come from git;
the machine only needs the toolchain and the activation steps below.

## 1. Install ESP-IDF v5.5.4 with EIM

Download the EIM command-line installer (`eim-cli-windows-x64.exe`) from
https://github.com/espressif/idf-im-ui/releases (0.13.x is known to work) and
run it **outside the repository**, since it writes `eim_config.toml` into the
current directory:

```powershell
.\eim.exe install -i v5.5.4 -t esp32p4,esp32c6 -n true -a true --cleanup true --do-not-track true
```

This takes about 10 minutes, mostly downloads. With EIM 0.13.x defaults:

- ESP-IDF lands in `C:\esp\v5.5.4\esp-idf` (not `C:\Espressif\frameworks\...`).
- Tools and Python land in `C:\Espressif\tools`. Other IDF versions installed
  there coexist.
- The activation script is `C:\Espressif\tools\Microsoft.v5.5.4.PowerShell_profile.ps1`.

`eim_config.toml` can be deleted afterwards.

## 2. Activate the environment

Once per PowerShell session:

```powershell
$env:PYTHONUTF8 = "1"
. C:\Espressif\tools\Microsoft.v5.5.4.PowerShell_profile.ps1
$env:ESP_IDF_VERSION = "5.5"   # REQUIRED, see below
```

### Why `ESP_IDF_VERSION` must be `5.5`

EIM's profile sets `ESP_IDF_VERSION` to the full version (`5.5.4`), but
official IDF 5.5.x activation sets major.minor (`5.5`). `esp_wifi_remote`'s
Kconfig loads `Kconfig.idf_v$ESP_IDF_VERSION.in`, and only
`Kconfig.idf_v5.5.in` exists. With the wrong value the fragment silently loads
nothing, every `SLAVE_IDF_TARGET_*` symbol vanishes, `sdkconfig` regenerates
with esp_hosted on SPI and an "invalid" slave target, and the build fails with
`#error "Unknown Slave Target"` inside esp_hosted.

**Recovery:** `git checkout -- sdkconfig dependencies.lock`, delete `build/`,
set the variable, rebuild.

## 3. Build and check `sdkconfig`

From the repository root (if `build/` exists from another IDF version, delete
it first):

```powershell
idf.py build
```

After a successful build, `git diff sdkconfig` must be empty. A diff touching
`ESP32P4_REV_MIN_FULL`, `ESP_HOSTED_*`, or `SLAVE_IDF_TARGET_*` means the
environment was wrong; recover as above.

## 4. Flash and check the boot log

```powershell
idf.py -p COM<N> flash monitor
```

- `idf.py flash` works under esptool v5 because `slave_ota/CMakeLists.txt`
  adds `--force` (esptool v5 otherwise refuses the embedded ESP32-C6
  `network_adapter.bin` in a P4 image set).
- The committed `sdkconfig` targets **silicon rev < 3.0 only**
  (`ESP32P4_SELECTS_REV_LESS_V3=y`), which matches the board's rev v1.0 chip.
  A rev 3.x board refuses this image; rev < 3.0 and >= 3.0 are mutually
  exclusive targets from IDF 5.5.2 onward. Check `chip revision:` in the boot
  log.

Healthy boot milestones:

```
I boot: ESP-IDF v5.5.4 2nd stage bootloader
I boot: chip revision: v1.0
I esp_psram: SPI SRAM memory test OK
I cpu_start: cpu freq: 360000000 Hz           (correct for rev < 3 silicon)
I H_SDIO_DRV: Card init success, TRANSPORT_RX_ACTIVE
I esp_netif_handlers: sta ip: ...
```

Known-benign log lines: `E system_api: 0 mac type is incorrect` (long-standing
P4 quirk) and the `slave_ota` warning about the C6's esp_hosted 2.7.0
(esp-hosted-mcu#143).

## Pinned components

The component pins are deliberate. Do **not** run `idf.py update-dependencies`.

- `esp_hosted ~2.9.3`: 2.10 and later exceed the internal-RAM budget (see the
  comment in `main/idf_component.yml`).
- `esp_wifi_remote 1.2.2`, pinned through `dependencies.lock`: 1.4.2 and later
  require esp_hosted 2.11 or newer.
