# Brand themes: implementation notes

The web UI ships five **live, switchable themes** (`spectrum` · `gallery` · `console` · `dither` ·
`blossom`), selectable from **Settings → Display → Theme**; `spectrum` is the default. This file
documents how the system works, what each theme is, and how to extend it.

The brand brief behind all five: p3a is, before anything else, a pixel-art player, and its logo is a
pixel-art device showing a high-saturation hue wheel. Colorfulness is a value (muted tones are
off-brand), balanced with taste (color maps to a role, never decoration). The themes answer that
tension in different ways.

> **Spectrum vs Pixel Console** are deliberately pushed to opposite poles so they don't read alike:
> Spectrum = deep-violet canvas, rounded, flat, multi-colour, a rainbow (conic-gradient) wordmark,
> sans body; Pixel Console = pure cool-black CRT, sharp corners, scanlines, monochrome cyan glow,
> all-mono uppercase wordmark.

## How it works

- **Selection mechanism.** The active theme is a `data-theme` attribute on `<html>`
  (`spectrum` · `gallery` · `console` · `dither` · `blossom`). `webui/static/common.css` defines every
  colour/type/radius as a **design token** (CSS custom property); `:root` holds the default
  (Spectrum) and each `html[data-theme="…"]` block overrides the tokens.
- **Persistence.** `webui/static/theme.js` reads/writes `localStorage["p3a-theme"]`
  (default `spectrum`). It is loaded **synchronously in each page's `<head>`** so the saved
  theme is applied before first paint (no flash) and keeps `<meta name="theme-color">` in sync.
  It renders no UI — it exposes `window.p3aTheme = { THEMES, get(), set(id) }`.
  > Per-browser today. A future revision may promote this to an NVS device setting — at that
  > point `theme.js` should hydrate the initial value from `/config` and POST changes back,
  > keeping `localStorage` as the offline fallback.
- **Picker.** A `<select>` in the **Settings → Display tab** ("Theme" section, styled like the
  other Display sections). It is populated from `window.p3aTheme.THEMES`, and `onchange` calls
  `window.p3aTheme.set(id)`. (There is no global footer picker.)

## Files

| File | Role |
|------|------|
| `webui/static/common.css` | Token vocabulary, one block per theme, per-theme signature rules (canvas texture, wordmark voice, console glow), picker styling |
| `webui/static/theme.js` | Pre-paint apply, persistence, `window.p3aTheme` API (no UI) |
| `webui/settings.html` | `theme.js` in head; the **Theme** picker in the Display tab |
| `webui/index.html`, `playset-editor.html`, `ota.html`, `pico8/index.html` | Colors through tokens; `theme.js` in head |
| `webui/museum/browse.js` | Injected museum-browse modal uses the card tokens |

Any change here ships through the web UI OTA, so it needs a `WEBUI_VERSION` bump in the root
`CMakeLists.txt`. `version.txt`, `metadata.json`, and `compat.js` are generated from it; never edit
them by hand.

## Token families (see the header comment in common.css for the full list)

- `--c-bg` / `--c-on-bg*` / `--c-bg-fill*` — the page canvas and things directly on it
- `--c-card-*` / `--c-surface-sunk` / `--c-input-bg` — the raised (card/panel/input) world
- `--c-text* / --c-border` — **legacy aliases** of the card family (so old `var(--c-text)` refs
  theme for free; defined once in `:root`, they re-resolve per theme via `var(--c-card-fg)`)
- `--c-primary` / `--c-accent` (+ `--c-on-*` for text on them) — brand + action
- `--c-success/danger/warning` (+ `-dark`, `--c-on-*`, and `*-soft-bg/-fg` pairs) — state
- `--c-pill-user/pin/builtin` (+ `-fg`) — the playlist-pill families
- `--font` / `--font-display` / `--font-mono`, and `--r-sm/md/lg`

Translucent tints are derived at use-site with `color-mix(in srgb, var(--c-…) N%, transparent)`
(widely supported in current mobile browsers), so a single base token drives both the solid and
the tinted states.

## The five themes

Hex values are the shipped tokens in `common.css` (canvas `--c-bg`, card `--c-card-bg`,
`--c-primary`, `--c-accent`).

### Spectrum (default)

The logo's hue wheel made systematic: one spectral ring of equal saturation and lightness, so the
brand colors are siblings and cannot clash. Discipline rule: one accent per context, neutral
everything else; the riot of color lives inside the artwork. Dark "display-off" canvas so accents
glow like pixels on the panel.

- Canvas `#0E0A1A` (deep violet), card `#171229`, primary `#8B5CFF` violet, accent `#FF4D97` pink.
- Rounded (`--r-md` 12px), flat, sans body. Signature: soft violet/pink radial aura on the canvas
  and a conic-gradient rainbow wordmark.

### Gallery

A tiny museum on the wall: warm passe-partout neutrals, editorial type, and color held in reserve
for the art. The calm pole, aimed at the museum/IIIF content.

- Canvas `#F4F1EA` (mat cream), card `#FBFAF7`, primary `#244E66` deep blue, accent `#B08A3E`
  brass.
- Serif display face, small radii (6px). Signature: small-caps serif wordmark.

### Pixel Console

The web UI as the instrument panel of a display device: cool-black chassis, monospace readouts,
sparse emissive accents that glow like lit LEDs. Deliberately the opposite pole from Spectrum.

- Canvas `#07080A`, card `#0E1014`, primary `#3DF0E0` cyan, accent `#FF5CD2` magenta.
- Sharp corners (2px), mono display face. Signature: CRT scanlines over a fine grid, cyan glow on
  the uppercase wordmark, buttons, and active pills.

### Dither Pop

A risograph print poster: a few bold inks on warm paper, flat color blocks, and a dot-screen
texture that nods to dithering, pixel art's ancestor. Restraint by constraint.

- Canvas `#F3EEE3` (newsprint), card `#FAF6EC`, primary `#2541B2` riso blue, accent `#FF48A0`
  fluoro pink.
- Sharp corners (2px), heavy sans display face. Signature: dot-screen canvas, heavy poster
  wordmark.

### Blossom

A soft boutique palette: blush canvas, plum ink, a rose primary with a lilac accent. Colorful in
feeling without being bright; restraint through softness.

- Canvas `#FBF1F3` (blush), card `#FFFBFC`, primary `#D14E8C` rose, accent `#8E5BA6` lilac-plum.
- Generously rounded (14px), Didot-style serif display face. Signature: soft rose/lilac wash and an
  italic serif wordmark.

## Conventions that keep colour disciplined

- **On-canvas vs in-card.** Anything on the body background uses the `--c-on-bg*` / `--c-bg-fill*`
  family; anything inside a card/modal uses `--c-card-*`. This is what lets light themes (Gallery, Blossom,
  Dither) and dark themes (Spectrum, Console) both stay legible from the same markup.
- **Text-on-fill tokens.** Buttons/badges read their text colour from `--c-on-primary`,
  `--c-on-success`, etc. — never a hardcoded `white`, because on Console's cyan or Gallery's brass
  the correct text is dark.
- **Theme-safe literals left alone:** black-alpha drop shadows / scrims, modal backdrops, the
  categorical `channelColors` chart palette in playset-editor, and the live RGB preview swatch.

## Adding another theme

1. Add an `html[data-theme="<id>"] { … }` block in common.css with the full token set.
2. (Optional) add a signature rule block at the bottom for texture/wordmark.
3. Add `{ id, name }` to `THEMES` and an entry to `THEME_COLOR` in `theme.js`.
4. Add a section for it under "The five themes" above, and bump `WEBUI_VERSION`.

## Out of scope (intentionally not themed)

The Wi-Fi **setup / captive-portal** pages (`webui/setup/*`) are standalone, served pre-network in
AP mode, and do not load `common.css`/`theme.js`. They keep their own minimal styling.
