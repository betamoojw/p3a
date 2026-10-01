# Deferred ideas

Ideas we evaluated and intentionally did not ship, one page each. Every page
says what was considered, why now is not the right time, and what would make
us revisit it. Open bugs and unfinished mitigations live in
`docs/known-issues.md` instead.

| Page | Idea | Main reason it waits |
|------|------|----------------------|
| [aspect-ratio-filter.md](aspect-ratio-filter.md) | Filter museum artwork by aspect ratio | Design closed, not yet scheduled |
| [esp-idf-6.md](esp-idf-6.md) | Migrate from ESP-IDF 5.5 LTS to 6.0 | Maintenance-only payoff; waits on a v6.0-compatible Waveshare BSP |
| [exfat.md](exfat.md) | Mount factory-formatted exFAT cards | Permanent fork of IDF `fatfs`; the FAT32 formatter already unblocks every card |
| [gallica.md](gallica.md) | BnF Gallica as a museum channel | Needs an XML/SRU parser |
| [library-of-congress.md](library-of-congress.md) | Library of Congress as a museum channel | IIIF identifiers often overflow the 48-byte `iiif_key` slot, and listings do not reliably expose IIIF URLs |
| [wellcome-long-labels.md](wellcome-long-labels.md) | Wellcome facet terms with labels over 32 characters | Playset identifier field is 32 characters |
