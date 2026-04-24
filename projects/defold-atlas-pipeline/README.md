# Defold Atlas + Behavior Capture Pipeline

A working Defold 1.6+ project, generated from Python. Ships a hero game object
with a shared sprite atlas, a deterministic behavior controller, and a headless
capture module that writes one CSV row per frame for AI training.

## What the script produces

`scripts/python/build_defold_project.py` emits
`scripts/projects/defold/` with:

- **`game.project`** — 1280×720 viewport, editorial clear color, main
  collection `/main/main.collectionc`, shared Lua state enabled.
- **`input/game.input_binding`** — left / right / capture actions.
- **`main/main.collection`** — Defold text-format collection with a `hero`
  entity bundling a `script` component and an embedded `sprite` component
  bound to the atlas animation `creature_00`.
- **`main/hero.script`** — Lua controller. When `sys.get_config("behavior.capture")`
  is `"1"` it opens `behavior.csv` and writes `t,x,y,vx,vy,action` every
  `update()` tick, so runs are reproducible.
- **`main/behavior_capture.lua`** — headless driver. Steps the collection N
  times and exits. Invoked from CI as `defold-build -- lua main/behavior_capture.lua`.
- **`main/creatures.png`** — shared atlas (same bytes as Godot/Solar 2D).
- **`main/creatures.atlas`** — Defold atlas manifest with 24 animations, one
  per creature, loop forward at 12 fps.
- **`manifest.csv`** — AI-pipeline view of the atlas.

## Why it matters for AI research

- **Behavior datasets from gameplay.** `hero.script` is deliberately simple
  (input-driven 2D motion) so the resulting CSV is a clean ground-truth for
  imitation-learning baselines.
- **Engine-authoritative transforms.** Defold runs the same physics and
  input dispatch in headless mode, so `behavior.csv` rows match what a player
  would see — no separate "physics sim" to maintain.
- **Text-format collections.** `.collection` and `.atlas` are both text
  protocols; the repo diffs cleanly in PR reviews.

## Run the Defold project

Open `game.project` in the Defold editor (build → run) or headless:

```bash
# from the project root:
bob --archive --platform x86_64-linux build
./build/default/x86_64-linux/dmengine
```

## Run the generator

```bash
python3 scripts/python/build_defold_project.py
```

## References

- Defold manuals: https://defold.com/manuals/introduction/
- Atlas format: https://defold.com/manuals/atlas/
- Headless builds (`bob`): https://defold.com/manuals/bob/
- Text protobuf file formats: https://defold.com/ref/stable/
