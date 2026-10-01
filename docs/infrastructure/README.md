# p3a Infrastructure Documentation

Technical documentation for the **p3a** firmware, an ESP32-P4 Wi-Fi pixel art player.
For the map of all other documentation (user guides, work streams, open issues),
see the Documentation map in [`AGENTS.md`](../../AGENTS.md).

## Contents

- [Architecture](architecture.md): platform, system diagram, boot sequence, service layer pattern
- [Directory Structure](directory-structure.md): top-level folder layout and key files
- [Build System](build-system.md): CMake configuration, build commands, release packaging
- [Components](components.md): all 32 ESP-IDF components under `components/`
- [Hardware and Peripherals](hardware-and-peripherals.md): board specs, display, touch, USB, SD card
- [Network and API](network-and-api.md): Wi-Fi, HTTP server, REST API, WebSocket, MQTT
- [Display Pipeline](display-pipeline.md): rendering, upscaling, overlays, frame buffer management
- [Configuration and Development](configuration-and-development.md): Kconfig options, dev workflow, setup

## Quick Links

- **Repository**: https://github.com/fabkury/p3a
- **Hardware**: [Waveshare ESP32-P4-WIFI6-Touch-LCD-4B](https://www.waveshare.com/esp32-p4-wifi6-touch-lcd-4b.htm?sku=31416)
- **ESP-IDF**: https://docs.espressif.com/projects/esp-idf/
- **Makapix Club**: https://makapix.club/

---

*Last updated: October 2026*
