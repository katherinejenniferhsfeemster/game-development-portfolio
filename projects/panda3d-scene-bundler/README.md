# Panda 3D Scene + Headless Capture

A runnable Panda 3D app generated from Python. Ships a 178-voxel `.egg` scene
graph, a classic `ShowBase` entry point, and an offscreen capture script that
renders N frames into PNGs without opening a window — ideal for computer-vision
dataset generation in CI.

## What the script produces

`scripts/python/build_panda3d_project.py` emits
`scripts/projects/panda3d/` with:

- **`main.py`** — `DatasetApp(ShowBase)`. Loads `scene.egg`, sets the camera
  to an isometric-ish pose, adds an ambient + directional light, and spins
  the scene at 10 deg/s for preview.
- **`scene.egg`** — hand-written Panda `.egg` text-format scene graph.
  `CoordinateSystem { Z-Up }`, 178 voxel cubes laid out identically to the
  Godot and Stride scenes so captures line up cross-engine.
- **`scene_graph.json`** — portable JSON mirror of the voxel positions and
  colors. Useful for tools that don't speak `.egg` but need the same scene.
- **`Config.prc`** — window size, framerate meter, multisample anti-aliasing.
- **`headless_capture.py`** — uses `loadPrcFileData("", "window-type offscreen")`
  and the Panda offscreen framebuffer to render 120 frames to PNG, rotating
  the scene 3 deg per frame. Runs without a display server.

## Why it matters for AI research

- **Offscreen rendering out of the box.** Panda's `offscreen` window type
  produces framebuffers identical to the on-screen output, so CV datasets
  captured from CI match the visual target the model will see.
- **Hand-editable scenes.** `.egg` is text. Adding a new cube is twenty lines;
  no editor round-trip.
- **Scene parity across engines.** The voxel layout in `scene.egg` matches
  `godot/scenes/main.tscn` and `stride/Assets/Scenes/MainScene.sdscene`, so
  the same camera pose yields the same frame in all three engines.

## Run Panda 3D

```bash
pip install panda3d
python scripts/projects/panda3d/main.py
```

Headless dataset capture (120 frames in `captures/`):

```bash
python scripts/projects/panda3d/headless_capture.py
```

## Run the generator

```bash
python3 scripts/python/build_panda3d_project.py
```

## References

- Panda 3D manual: https://docs.panda3d.org/1.10/python/index
- `.egg` format spec: https://docs.panda3d.org/1.10/python/pipeline/egg-files/index
- Offscreen buffers: https://docs.panda3d.org/1.10/python/programming/advanced-loading/offscreen-buffers
