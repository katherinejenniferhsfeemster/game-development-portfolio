# Godot 4 Procedural Asset Pipeline

A valid Godot 4.2 project, generated from Python. Builds a 12×12 voxel world
at runtime via GDScript, ships a shared sprite atlas, and includes an
`AssetExporter` autoload that writes glTF for downstream AI training.

## What the script produces

`scripts/python/build_godot_project.py` emits
`scripts/projects/godot/` with:

- **`project.godot`** — pinned to Godot 4.2 Forward Plus, viewport 1920×1080,
  clear color set to the editorial ink, `AssetExporter` registered as an
  autoload.
- **`scenes/main.tscn`** — `Node3D` with a `Camera3D` at `(12, 14, 12)`
  looking at the voxel origin and a `DirectionalLight3D` with shadows.
- **`scripts/VoxelScene.gd`** — 12×12 seeded voxel builder using
  `MeshInstance3D` + `BoxMesh` + `StandardMaterial3D`. Height comes from
  `hash(Vector2i(i, j)) % 3`, so CI runs are byte-identical.
- **`scripts/AssetExporter.gd`** — autoload singleton that detects headless
  mode (`OS.has_feature("headless")`) and writes `res://build/world.gltf`
  via `GLTFDocument`.
- **`assets/creatures.png`** — shared 24-sprite atlas (96×96 frames,
  6 columns × 4 rows).
- **`assets/creatures.atlas.tres`** — `SpriteFrames` resource referencing the
  atlas PNG.
- **`manifest.csv`** — one row per sprite with atlas rect coordinates. Used by
  the AI pipeline to slice the sheet without opening Godot.

## Why it matters for AI research

- **Reproducible dataset captures**. Run the project with
  `godot --headless scenes/main.tscn`; `AssetExporter` writes `world.gltf`
  which downstream CV pipelines consume directly.
- **Diffable cuts**. The voxel world is described by ~60 lines of GDScript
  and a `.tscn` with ten fields — PRs reviewing "did we change the scene?"
  take five seconds.
- **No editor round-trip**. The project is generated from source, so the CI
  doesn't need a GUI session to regenerate it.

## Run the Godot project

```bash
godot --path scripts/projects/godot scenes/main.tscn
```

Headless glTF export:

```bash
godot --headless --path scripts/projects/godot scenes/main.tscn
# writes scripts/projects/godot/build/world.gltf
```

## Run the generator

```bash
python3 scripts/python/build_godot_project.py
```

## References

- Godot 4 docs: https://docs.godotengine.org/en/stable/
- `.tscn`/`.tres` format: https://docs.godotengine.org/en/stable/contributing/development/file_formats/tscn.html
- `GLTFDocument`: https://docs.godotengine.org/en/stable/classes/class_gltfdocument.html
