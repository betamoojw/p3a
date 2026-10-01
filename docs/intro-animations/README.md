# Intro Animations

p3a ships **22 boot intro animations**, one picked at random on every boot.
Each is a different way of fading in the p3a logo: the screen starts as a flat
fill of the user-configured background color and ends with the logo statically
centered. Only what happens in between differs.

**Status:** all 22 animations ship and are device-verified. The only remaining
work is the owner's Phase 5 QA pass (checklist below).

- [architecture.md](architecture.md): shared animation interface, host harness
  design, timing model, performance budget, automated checks, NVS keys.
- [catalog.md](catalog.md): the animation roster and the candidate pool.

## Boot sequence

```
blank-delay (250 ms, hardcoded)  ->  intro-animation (NVS-configurable 1000..7500 ms, default 3000 ms)  ->  hold (1000 ms, hardcoded)
```

- **blank-delay**: flat background color, no logo. Owned by the manager.
- **intro-animation**: the randomly picked animation, rendered from normalized
  time `t` in [0,1] across this window. The only part animation modules
  implement.
- **hold**: logo at full opacity, centered. The manager renders it by calling
  the animation at `t = 1`, so the handoff is seamless.

## Key facts

- The intro manager is `components/p3a_core/p3a_boot_logo.c`, driven by
  `p3a_render_frame()` in `components/p3a_core/p3a_render.c`. It picks the
  animation with `esp_random()` and logs the choice at INFO.
- Animations live in `components/p3a_core/intro_anims/`: `intro_anim.h`
  (interface), `intro_anim_common.c` (shared helpers), `intro_anim_registry.c`
  (the registry), and one `ia_<name>.c` per animation. These files are pure C
  with no ESP-IDF includes, so the host harness compiles them unchanged.
- Default total boot is 4250 ms (250 + 3000 + 1000); frame target is 33 ms
  (30 FPS).
- Logo: 46x54 BGR888 with a gray (0x808080) chroma key, in
  `components/p3a_core/p3a_logo.c`; blitted at 3x scale (138x162 px), centered
  on 720x720, honoring rotation (0/90/180/270) and the background color from
  `config_store`.
- Settings: NVS `intro_anim_ms` (duration, 1000..7500, default 3000) and
  `intro_anim_force` (empty or `random` = random pick, otherwise an animation
  name). Exposed by `GET /api/intro-animations` and written through `PUT
  /config`; the web UI has a slider and dropdown in the Settings Display tab.
- At the end of each intro the manager logs render-time min/avg/max and the
  budget-overrun count.

## Adding an animation

Every animation must satisfy this contract:

1. **t = 0** is pixel-identical to a flat fill of the background color (what
   blank-delay shows). No logo content.
2. **t = 1** is pixel-identical to the end state: background fill plus
   `p3a_logo_blit_pixelwise_bgr888(alpha=255, scale=3, rotation)` centered.
3. **Pure function of time**: each frame is computed from `t` and the per-boot
   seed only. No state across frames, no wall clock, no global RNG.
4. Honors any RGB background color and all four rotations.
5. Fits its declared per-frame budget on the P4 (see
   [architecture.md](architecture.md), performance budget).
6. Duration-agnostic: animations only ever see `t`.

Steps:

1. Write `components/p3a_core/intro_anims/ia_<name>.c` with an
   `ia_<name>_render(buffer, ctx, t)` function, using the helpers in
   `intro_anim_common.c`.
2. Declare it and add an entry (`name`, `frame_budget_ms`, `render`) to
   `intro_anim_registry[]` in `intro_anim_registry.c`.
3. Add the source file to `components/p3a_core/CMakeLists.txt` and to the
   `$sources` list in `host/intro-anim-lab/build.ps1`.
4. On the host, build the harness, iterate in the live viewer, and run
   `intro-anim-lab.exe --check` until it exits 0 (usage in
   `host/intro-anim-lab/README.md`).
5. Verify on the device, using `intro_anim_force` to play it every boot.
6. Add it to [catalog.md](catalog.md).

## Phase 5 QA checklist (owner, on device)

- [ ] One profiling firmware pass: per-frame render time (min/avg/max) for all
      22 animations on the P4; each must fit its declared per-frame budget.
- [ ] Spot-check all 22 across rotations and a few background colors,
      including black, white, 0x808080 (the chroma-key gray), and a saturated
      color.
- [ ] Spot-check the duration setting at min (1000 ms), default (3000 ms), and
      max (7500 ms).
