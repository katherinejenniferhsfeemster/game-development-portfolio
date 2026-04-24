# Solar 2D Scene + Particle Generator

A complete, scripted Solar 2D (formerly Corona SDK) project — pure Lua plus
PNGs, no editor required. Loads a tilemap scene, spawns a sprite hero from the
shared atlas, overlays a particle burst, and can run headless behavior capture
for AI dataset collection.

## What the script produces

`scripts/python/build_solar2d_project.py` emits
`scripts/projects/solar2d/` with:

- **`main.lua`** — entry point. Seeds RNG when `CAPTURE=1`, loads the scene,
  and arms the capture module.
- **`config.lua`** — 720×1280 letterbox content, 60 fps, `@2x` asset suffix.
- **`build.settings`** — portrait-only, Android resizable off, title pinned.
- **`scene.lua`** — builds the scene: tilemap background, sprite hero from
  `graphics.newImageSheet` (24 frames × 96 px), particle overlay.
- **`particles.lua`** — deterministic CPU burst emitter (LCG-seeded) so the
  same `seed` yields the same particle trajectories. Portable to any Lua-first
  engine without the Solar 2D emitter API.
- **`capture.lua`** — headless behavior logger. Simulates N ticks of a simple
  sine-weave policy and writes `behavior.csv`, then exits.
- **`assets/`** — `creatures.png` (atlas), `tilemap.png` (24×14 grid),
  `particles.png` (preview overlay).

## Why it matters for AI research

- **Platform reach.** Solar 2D exports to iOS, Android, macOS, Windows and
  HTML5 from the same `main.lua`. For mobile-first data collection (camera
  + motion + gameplay) it beats writing platform code.
- **Offline-reproducible captures.** The LCG in `particles.lua` and the
  `math.randomseed` line in `main.lua` together make every run bit-identical.
- **Minimal project surface.** Seven Lua files + three PNGs is the whole
  project. Easy to reason about in code review.

## Run the Solar 2D project

```bash
corona-simulator --project scripts/projects/solar2d
# or headless capture:
CAPTURE=1 corona-simulator --project scripts/projects/solar2d
```

## Run the generator

```bash
python3 scripts/python/build_solar2d_project.py
```

## References

- Solar 2D docs: https://docs.coronalabs.com/
- `graphics.newImageSheet`: https://docs.coronalabs.com/api/library/graphics/newImageSheet.html
- `composer` scene manager: https://docs.coronalabs.com/api/library/composer/
